import asyncio
import logging
from typing import Dict, Optional, List, Any, Tuple
from pathlib import Path

from monoco.daemon.services import ProjectManager
from monoco.daemon.triggers import MemoAccumulationPolicy
from monoco.features.agent.manager import SessionManager
from monoco.features.agent.models import RoleTemplate
from monoco.features.agent.session import RuntimeSession
from monoco.features.agent.apoptosis import ApoptosisManager
from monoco.features.issue.core import list_issues

logger = logging.getLogger("monoco.daemon.scheduler")

class SchedulerService:
    def __init__(self, project_manager: ProjectManager):
        self.project_manager = project_manager
        self.session_managers: Dict[str, SessionManager] = {} 
        self._monitoring_task: Optional[asyncio.Task] = None
        self.apoptosis_managers: Dict[str, ApoptosisManager] = {}

    def get_managers(self, project_path: Path) -> Tuple[SessionManager, ApoptosisManager]:
        key = str(project_path)
        if key not in self.session_managers:
            sm = SessionManager(project_root=project_path)
            self.session_managers[key] = sm
            self.apoptosis_managers[key] = ApoptosisManager(sm)
        return self.session_managers[key], self.apoptosis_managers[key]

    async def start(self):
        logger.info("Starting Scheduler Service...")
        self._monitoring_task = asyncio.create_task(self.monitor_loop())

    def stop(self):
        logger.info("Stopping Scheduler Service...")
        if self._monitoring_task:
            self._monitoring_task.cancel()
        
        # Terminate all sessions
        for sm in self.session_managers.values():
            filtered_sessions = sm.list_sessions() 
            for session in filtered_sessions:
                session.terminate()

    async def monitor_loop(self):
        try:
            while True:
                await self.tick()
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Scheduler loop crashed: {e}", exc_info=True)

    async def tick(self):
        # We iterate over keys to avoid modification during iteration issues if new projects added
        projects = list(self.project_manager.projects.values())
        for project_ctx in projects:
            await self.process_project(project_ctx)

    async def process_project(self, project_context):
        sm, am = self.get_managers(project_context.path)
        
        # 1. Trigger Check: Architect
        # Checking existing Architect sessions
        existing_architects = [s for s in sm.list_sessions() if s.model.role_name == "Architect" and s.model.status == "running"]
        
        if not existing_architects:
            trigger_policy = MemoAccumulationPolicy(count_threshold=5)
            if trigger_policy.evaluate({"issues_root": project_context.issues_root}):
                logger.info(f"Triggering Architect for project {project_context.id}")
                self.spawn_architect(sm, project_context)

        # 1.5 Handover Trigger: Architect -> Engineer
        # Scan for OPEN + DOING issues with no active worker
        try:
            all_issues = list_issues(project_context.issues_root)
            for issue in all_issues:
                # Check status/stage. Note: status is Enum(str) so string comparison works usually, but safer to use value
                status_val = issue.status if isinstance(issue.status, str) else issue.status.value
                stage_val = issue.stage if isinstance(issue.stage, str) else issue.stage.value
                
                if status_val == "open" and stage_val == "doing":
                    # Check if session exists
                    active = [s for s in sm.list_sessions(issue_id=issue.id) if s.model.status in ["running", "pending"]]
                    if not active:
                        logger.info(f"Handover trigger: Spawning Engineer for {issue.id}")
                        self.spawn_engineer(sm, issue)
        except Exception as e:
            logger.error(f"Error in Handover trigger: {e}")

        # 2. Monitor Active Sessions (Supervisor)
        active_sessions = sm.list_sessions()
        for session in active_sessions:
            if session.model.status in ["running", "pending"]:
                status = session.refresh_status() # Updates model.status
                
                # Check for timeout/failure
                if status == "timeout" or status == "failed":
                     if session.model.status != "crashed": 
                         logger.warning(f"Session {session.model.id} led to {status}. Triggering Autopsy.")
                         am.trigger_apoptosis(session.model.id)
                
                # Daemon Logic for Chained Execution
                if status == "completed":
                    self.handle_completion(session, sm)

    def spawn_engineer(self, sm: SessionManager, issue):
        role = RoleTemplate(
            name="Engineer",
            description="Software Engineer",
            trigger="handover",
            goal=f"Implement feature: {issue.title}",
            system_prompt="You are a Software Engineer. Read the issue and implement requirements.",
            engine="gemini"
        )
        session = sm.create_session(issue_id=issue.id, role=role)
        session.start()

    def spawn_architect(self, sm: SessionManager, project_context):
        # Create Architect Session
        role = RoleTemplate(
            name="Architect",
            description="System Architect",
            trigger="memo.accumulation",
            goal="Process memo inbox and create issues.",
            system_prompt="You are the Architect. Process the Memo inbox.",
            engine="gemini" # Default or from config?
        )
        session = sm.create_session(issue_id="architecture-review", role=role)
        session.start()

    def handle_completion(self, session: RuntimeSession, sm: SessionManager):
        # Chained Execution: Engineer -> Reviewer
        if session.model.role_name == "Engineer":
             logger.info(f"Engineer finished for {session.model.issue_id}. Spawning Reviewer.")
             reviewer_role = RoleTemplate(
                name="Reviewer",
                description="Code Reviewer",
                trigger="engineer.completion",
                goal=f"Review work on {session.model.issue_id}",
                system_prompt="You are a Code Reviewer. Review the code changes.",
                engine="gemini"
             )
             rs = sm.create_session(issue_id=session.model.issue_id, role=reviewer_role)
             rs.start()
