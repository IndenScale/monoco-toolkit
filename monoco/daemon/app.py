from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import logging
import os
from typing import Optional, List, Dict
from monoco.daemon.services import Broadcaster, GitMonitor, ProjectManager
from fastapi import FastAPI, Request, HTTPException, Query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("monoco.daemon")
from pathlib import Path
from monoco.core.config import get_config
from monoco.features.issue.core import list_issues

description = """
Monoco Daemon Process
- Repository Awareness
- State Management
- SSE Broadcast
"""

# Service Instances
broadcaster = Broadcaster()
git_monitor = GitMonitor(broadcaster)
project_manager: ProjectManager | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Monoco Daemon services...")
    
    global project_manager
    # Use MONOCO_SERVER_ROOT if set, otherwise CWD
    env_root = os.getenv("MONOCO_SERVER_ROOT")
    workspace_root = Path(env_root) if env_root else Path.cwd()
    logger.info(f"Workspace Root: {workspace_root}")
    project_manager = ProjectManager(workspace_root, broadcaster)
    
    await project_manager.start_all()
    monitor_task = asyncio.create_task(git_monitor.start())
    
    yield
    # Shutdown
    logger.info("Shutting down Monoco Daemon services...")
    git_monitor.stop()
    if project_manager:
        project_manager.stop_all()
    await monitor_task
    
app = FastAPI(
    title="Monoco Daemon",
    description=description,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

def get_project_or_404(project_id: Optional[str] = None):
    if not project_manager:
        raise HTTPException(status_code=503, detail="Daemon not fully initialized")
    
    # If project_id is not provided, try to use the first available project (default behavior)
    if not project_id:
        projects = list(project_manager.projects.values())
        if not projects:
             # Fallback to legacy single-project mode if no sub-projects found? 
             # Or maybe ProjectManager scan logic already covers CWD as a project.
             raise HTTPException(status_code=404, detail="No projects found")
        return projects[0]

    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project

# CORS Configuration
# Kanban may run on different ports (e.g. localhost:3000, tauri://localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """
    Instant health check for process monitors.
    """
    return {"status": "ok", "component": "monoco-daemon"}

@app.get("/api/v1/projects")
async def list_projects():
    """
    List all discovered projects.
    """
    if not project_manager:
        return []
    return project_manager.list_projects()

@app.get("/api/v1/info")
async def get_project_info(project_id: Optional[str] = None):
    """
    Metadata about the current Monoco project.
    """
    project = get_project_or_404(project_id)
    current_hash = await git_monitor.get_head_hash()
    return {
        "name": project.name,
        "id": project.id,
        "version": "0.1.0",
        "mode": "daemon",
        "head": current_hash
    }

@app.get("/api/v1/config/dictionary")
async def get_ui_dictionary(project_id: Optional[str] = None) -> Dict[str, str]:
    """
    Get UI Terminology Dictionary.
    """
    project = get_project_or_404(project_id)
    # Reload config to get latest
    config = get_config(str(project.path))
    return config.ui.dictionary

@app.get("/api/v1/events")
async def sse_endpoint(request: Request):
    """
    Server-Sent Events endpoint for real-time updates.
    """
    queue = await broadcaster.subscribe()
    
    async def event_generator():
        try:
            # Quick ping to confirm connection
            yield {
                "event": "connect",
                "data": "connected"
            }
            
            while True:
                if await request.is_disconnected():
                    break
                    
                # Wait for new messages
                message = await queue.get()
                yield message
                
        except asyncio.CancelledError:
            logger.debug("SSE connection cancelled")
        finally:
            await broadcaster.unsubscribe(queue)

    return EventSourceResponse(event_generator())

@app.get("/api/v1/issues")
async def get_issues(project_id: Optional[str] = None):
    """
    List all issues in the project.
    """
    project = get_project_or_404(project_id)
    issues = list_issues(project.issues_root)
    return issues

from monoco.features.issue.core import list_issues, create_issue_file, update_issue, delete_issue_file, find_issue_path, parse_issue, get_board_data, parse_issue_detail, update_issue_content
from monoco.features.issue.models import IssueType, IssueStatus, IssueSolution, IssueStage, IssueMetadata, IssueDetail
from monoco.daemon.models import CreateIssueRequest, UpdateIssueRequest, UpdateIssueContentRequest
from monoco.daemon.stats import calculate_dashboard_stats, DashboardStats
from fastapi import FastAPI, Request, HTTPException
from typing import Optional, List, Dict

# ... existing code ...

@app.get("/api/v1/board")
async def get_board_endpoint(project_id: Optional[str] = None):
    """
    Get open issues grouped by stage for Kanban visualization.
    """
    project = get_project_or_404(project_id)
    board = get_board_data(project.issues_root)
    return board

@app.get("/api/v1/stats/dashboard", response_model=DashboardStats)
async def get_dashboard_stats_endpoint(project_id: Optional[str] = None):
    """
    Get aggregated dashboard statistics.
    """
    project = get_project_or_404(project_id)
    return calculate_dashboard_stats(project.issues_root)


@app.post("/api/v1/issues", response_model=IssueMetadata)
async def create_issue_endpoint(payload: CreateIssueRequest):
    """
    Create a new issue.
    """
    project = get_project_or_404(payload.project_id)
    
    try:
        issue, _ = create_issue_file(
            project.issues_root, 
            payload.type, 
            payload.title, 
            parent=payload.parent, 
            status=payload.status, 
            stage=payload.stage,
            dependencies=payload.dependencies, 
            related=payload.related, 
            subdir=payload.subdir
        )
        return issue
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/issues/{issue_id}", response_model=IssueDetail)
async def get_issue_endpoint(issue_id: str, project_id: Optional[str] = None):
    """
    Get issue details by ID.
    """
    project = get_project_or_404(project_id)
    
    path = find_issue_path(project.issues_root, issue_id)
    if not path:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
        
    issue = parse_issue_detail(path)
    if not issue:
        raise HTTPException(status_code=500, detail=f"Failed to parse issue {issue_id}")
        
    return issue

@app.patch("/api/v1/issues/{issue_id}", response_model=IssueMetadata)
async def update_issue_endpoint(issue_id: str, payload: UpdateIssueRequest):
    """
    Update an issue logic state (Status, Stage, Solution).
    """
    project = get_project_or_404(payload.project_id)
    
    try:
        issue = update_issue(
            project.issues_root, 
            issue_id, 
            status=payload.status, 
            stage=payload.stage, 
            solution=payload.solution
        )
        return issue
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/issues/{issue_id}/content", response_model=IssueMetadata)
async def update_issue_content_endpoint(issue_id: str, payload: UpdateIssueContentRequest):
    """
    Update raw content of an issue. Validates integrity before saving.
    """
    project = get_project_or_404(payload.project_id)
    
    try:
        # Note: We use PUT because we are replacing the content representation
        issue = update_issue_content(
            project.issues_root,
            issue_id,
            payload.content
        )
        return issue
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/issues/{issue_id}")
async def delete_issue_endpoint(issue_id: str, project_id: Optional[str] = None):
    """
    Delete an issue (physical removal).
    """
    project = get_project_or_404(project_id)
    
    try:
        delete_issue_file(project.issues_root, issue_id)
        return {"status": "deleted", "id": issue_id}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/monitor/refresh")
async def refresh_monitor():
    """
    Manually trigger a Git HEAD check.
    Useful for 'monoco issue commit' to instantly notify Kanbans.
    """
    # In a real impl, we might force the monitor to wake up.
    # For now, just getting the hash is a good sanity check.
    current_hash = await git_monitor.get_head_hash()
    
    # If we wanted to FORCE broadcast, we could do it here,
    # but the monitor loop will pick it up in <2s anyway.
    # To be "instant", we can manually broadcast if we know it changed?
    # Or just returning the hash confirms the daemon sees it.
    return {"status": "refreshed", "head": current_hash}

# --- Workspace State Management ---
import json
from pydantic import BaseModel

class WorkspaceState(BaseModel):
    last_active_project_id: Optional[str] = None

@app.get("/api/v1/workspace/state", response_model=WorkspaceState)
async def get_workspace_state():
    """
    Get the persisted workspace state (e.g. last active project).
    """
    if not project_manager:
         raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    state_file = project_manager.workspace_root / ".monoco" / "state.json"
    if not state_file.exists():
        # Default empty state
        return WorkspaceState()
        
    try:
        content = state_file.read_text(encoding='utf-8')
        if not content.strip():
            return WorkspaceState()
        data = json.loads(content)
        return WorkspaceState(**data)
    except Exception as e:
        logger.error(f"Failed to read state file: {e}")
        # Return empty state instead of crashing, so frontend can fallback
        return WorkspaceState()

@app.post("/api/v1/workspace/state", response_model=WorkspaceState)
async def update_workspace_state(state: WorkspaceState):
    """
    Update the workspace state.
    """
    if not project_manager:
         raise HTTPException(status_code=503, detail="Daemon not initialized")

    state_file = project_manager.workspace_root / ".monoco" / "state.json"
    
    # Ensure directory exists
    if not state_file.parent.exists():
        state_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # We merge with existing state to avoid data loss if we extend model later
        current_data = {}
        if state_file.exists():
            try:
                content = state_file.read_text(encoding='utf-8')
                if content.strip():
                    current_data = json.loads(content)
            except:
                pass # ignore read errors on write
        
        # Update with new values
        new_data = state.model_dump(exclude_unset=True)
        current_data.update(new_data)
        
        state_file.write_text(json.dumps(current_data, indent=2), encoding='utf-8')
        return WorkspaceState(**current_data)
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to persist state: {str(e)}")
