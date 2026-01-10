from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import logging
from monoco.daemon.services import Broadcaster, GitMonitor, IssueMonitor

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
# IssueMonitor needs config, will be initialized in lifespan or lazily?
# Better to initialize lazily or inside lifespan to access config.
issue_monitor: IssueMonitor | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Monoco Daemon services...")
    
    # Init Issue Monitor
    settings = get_config()
    root_path = Path(settings.paths.root).resolve()
    issues_root = root_path / settings.paths.issues
    
    global issue_monitor
    issue_monitor = IssueMonitor(issues_root, broadcaster)
    
    monitor_task = asyncio.create_task(git_monitor.start())
    issue_monitor_task = asyncio.create_task(issue_monitor.start())
    
    yield
    # Shutdown
    logger.info("Shutting down Monoco Daemon services...")
    git_monitor.stop()
    if issue_monitor:
        issue_monitor.stop()
    await monitor_task
    await issue_monitor_task
    
app = FastAPI(
    title="Monoco Daemon",
    description=description,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

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

@app.get("/api/v1/info")
async def get_project_info():
    """
    Metadata about the current Monoco project.
    """
    # TODO: Connect to actual Monoco Config
    current_hash = await git_monitor.get_head_hash()
    return {
        "name": "Monoco",
        "version": "0.1.0",
        "mode": "daemon",
        "head": current_hash
    }

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
async def get_issues():
    """
    List all issues in the project.
    """
    settings = get_config()
    # Resolve absolute path for robustness, defaulting to CWD if root is "."
    root_path = Path(settings.paths.root).resolve()
    issues_root = root_path / settings.paths.issues
    
    issues = list_issues(issues_root)
    return issues

from monoco.features.issue.core import list_issues, create_issue_file, update_issue, delete_issue_file, find_issue_path, parse_issue
from monoco.features.issue.models import IssueType, IssueStatus, IssueSolution, IssueStage, IssueMetadata
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List

# ... existing code ...

class CreateIssueRequest(BaseModel):
    type: IssueType
    title: str
    parent: Optional[str] = None
    status: IssueStatus = IssueStatus.OPEN
    dependencies: List[str] = []
    related: List[str] = []
    subdir: Optional[str] = None
    
class UpdateIssueRequest(BaseModel):
    status: Optional[IssueStatus] = None
    stage: Optional[IssueStage] = None
    solution: Optional[IssueSolution] = None

# ... existing code ...

@app.post("/api/v1/issues", response_model=IssueMetadata)
async def create_issue_endpoint(payload: CreateIssueRequest):
    """
    Create a new issue.
    """
    settings = get_config()
    root_path = Path(settings.paths.root).resolve()
    issues_root = root_path / settings.paths.issues
    
    try:
        issue = create_issue_file(
            issues_root, 
            payload.type, 
            payload.title, 
            parent=payload.parent, 
            status=payload.status, 
            dependencies=payload.dependencies, 
            related=payload.related, 
            subdir=payload.subdir
        )
        return issue
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/issues/{issue_id}", response_model=IssueMetadata)
async def get_issue_endpoint(issue_id: str):
    """
    Get issue details by ID.
    """
    settings = get_config()
    root_path = Path(settings.paths.root).resolve()
    issues_root = root_path / settings.paths.issues
    
    path = find_issue_path(issues_root, issue_id)
    if not path:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
        
    issue = parse_issue(path)
    if not issue:
        raise HTTPException(status_code=500, detail=f"Failed to parse issue {issue_id}")
        
    return issue

@app.patch("/api/v1/issues/{issue_id}", response_model=IssueMetadata)
async def update_issue_endpoint(issue_id: str, payload: UpdateIssueRequest):
    """
    Update an issue logic state (Status, Stage, Solution).
    """
    settings = get_config()
    root_path = Path(settings.paths.root).resolve()
    issues_root = root_path / settings.paths.issues
    
    try:
        issue = update_issue(
            issues_root, 
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

@app.delete("/api/v1/issues/{issue_id}")
async def delete_issue_endpoint(issue_id: str):
    """
    Delete an issue (physical removal).
    """
    settings = get_config()
    root_path = Path(settings.paths.root).resolve()
    issues_root = root_path / settings.paths.issues
    
    try:
        delete_issue_file(issues_root, issue_id)
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
