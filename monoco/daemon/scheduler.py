import asyncio
import logging
import os
from typing import Dict, Optional, List, Any, Tuple
from pathlib import Path

from monoco.daemon.services import ProjectManager, SemaphoreManager
from monoco.daemon.triggers import MemoAccumulationPolicy, HandoverPolicy
from monoco.features.agent.manager import SessionManager
from monoco.features.agent.models import RoleTemplate
from monoco.features.agent.session import RuntimeSession
from monoco.features.agent.apoptosis import ApoptosisManager
from monoco.features.issue.core import list_issues
from monoco.core.config import get_config

logger = logging.getLogger("monoco.daemon.scheduler")

class SchedulerService:
    def __init__(self, project_manager: ProjectManager):
        self.project_manager = project_manager
        self.session_managers: Dict[str, SessionManager] = {} 
        self._monitoring_task: Optional[asyncio.Task] = None
        self.apoptosis_managers: Dict[str, ApoptosisManager] = {}
        
        # Initialize SemaphoreManager with config
        config = self._load_concurrency_config()
        self.semaphore_manager = SemaphoreManager(config)

    def _load_concurrency_config(self) -> Optional[Any]:
        """Load concurrency configuration from config files and env vars."""
        try:
            settings = get_config()
            concurrency_config = settings.agent.concurrency
            
            # Check for environment variable override
            env_max_agents = os.environ.get("MONOCO_MAX_AGENTS")
            if env_max_agents:
                try:
                    concurrency_config.global_max = int(env_max_agents)
                    logger.info(f"Overriding global_max from environment: {env_max_agents}")
                except ValueError:
                    logger.warning(f"Invalid MONOCO_MAX_AGENTS value: {env_max_agents}")
            
            return concurrency_config
        except Exception as e:
            logger.warning(f"Failed to load concurrency config: {e}. Using defaults.")
            return None

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
        await self.check_inbox_trigger(sm, project_context)

        # 1.5 Handover Trigger: Architect -> Engineer
        await self.check_handover_trigger(sm, project_context)

        # 2. Monitor Active Sessions (Supervisor)
        active_sessions = sm.list_sessions()
        for session in active_sessions:
            if session.model.status in ["running", "pending"]:
                status = session.refresh_status() # Updates model.status
                
                # Check for timeout/failure
                if status == "timeout" or status == "failed":
                     if session.model.status != "crashed": 
                         logger.warning(f"Session {session.model.id} led to {status}. Triggering Autopsy.")
                         # Record failure for cooldown
                         self.semaphore_manager.record_failure(
                             issue_id=session.model.issue_id,
                             session_id=session.model.id
                         )
                         am.trigger_apoptosis(session.model.id, failure_reason=f"Session status became {status}")
                else:
                    # Track active session in semaphore manager
                    self.semaphore_manager.acquire(session.model.id, session.model.role_name)
                
                # Daemon Logic for Chained Execution
                if status == "completed":
                    # Clear failure record on success
                    self.semaphore_manager.clear_failure(session.model.issue_id)
                    self.handle_completion(session, sm)

    async def check_inbox_trigger(self, sm: SessionManager, project_context):
        # Checking existing Architect sessions
        existing_architects = [s for s in sm.list_sessions() if s.model.role_name == "Architect" and s.model.status == "running"]
        
        if not existing_architects:
            # Check semaphore before spawning
            if not self.semaphore_manager.can_acquire("Architect"):
                logger.warning("Cannot spawn Architect: concurrency limit reached")
                return
                
            trigger_policy = MemoAccumulationPolicy(count_threshold=5)
            if trigger_policy.evaluate({"issues_root": project_context.issues_root}):
                logger.info(f"Triggering Architect for project {project_context.id}")
                self.spawn_architect(sm, project_context)

    async def check_handover_trigger(self, sm: SessionManager, project_context):
        # Scan for OPEN + DOING issues with no active worker
        try:
            all_issues = list_issues(project_context.issues_root)
            handover_policy = HandoverPolicy(target_status="open", target_stage="doing")
            
            for issue in all_issues:
                if handover_policy.evaluate({"issue": issue}):
                    # Check if session exists
                    active = [s for s in sm.list_sessions(issue_id=issue.id) if s.model.status in ["running", "pending"]]
                    if not active:
                        # Check semaphore before spawning (including cooldown check)
                        if not self.semaphore_manager.can_acquire("Engineer", issue_id=issue.id):
                            logger.warning(f"Cannot spawn Engineer for {issue.id}: concurrency limit or cooldown active")
                            continue
                            
                        logger.info(f"Handover trigger: Spawning Engineer for {issue.id}")
                        self.spawn_engineer(sm, issue)
        except Exception as e:
            logger.error(f"Error in Handover trigger: {e}")

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
        
        # Acquire semaphore slot
        self.semaphore_manager.acquire(session.model.id, "Engineer")
        
        try:
            session.start()
        except Exception as e:
            # Release slot on spawn failure
            self.semaphore_manager.release(session.model.id)
            self.semaphore_manager.record_failure(issue.id, session.model.id)
            logger.error(f"Failed to start Engineer session for {issue.id}: {e}")
            raise

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
        
        # Acquire semaphore slot
        self.semaphore_manager.acquire(session.model.id, "Architect")
        
        try:
            session.start()
        except Exception as e:
            # Release slot on spawn failure
            self.semaphore_manager.release(session.model.id)
            logger.error(f"Failed to start Architect session: {e}")
            raise

    def handle_completion(self, session: RuntimeSession, sm: SessionManager):
        """Handle session completion - no chained execution (FEAT-0155).
        
        Note: Reviewer is no longer auto-triggered by Engineer completion.
        Reviewer should be triggered by PR creation or manual command.
        """
        logger.info(f"Session {session.model.id} ({session.model.role_name}) completed. "
                   f"No chained execution - Reviewer must be triggered manually or via PR.")
