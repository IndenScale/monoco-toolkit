"""
Scheduler Service - Event-driven agent orchestration (FEAT-0155, FEAT-0160).

Replaces polling-based trigger logic with event-driven architecture.
Uses AgentScheduler abstraction for provider-agnostic task scheduling.
"""

import asyncio
import logging
import os
from typing import Dict, Optional, List, Any, Tuple
from pathlib import Path

from monoco.daemon.services import ProjectManager, SemaphoreManager
from monoco.core.scheduler import AgentEventType, event_bus, AgentScheduler, LocalProcessScheduler
from monoco.daemon.handlers import EventHandlerRegistry
from monoco.features.agent.manager import SessionManager
from monoco.features.agent.session import RuntimeSession
from monoco.features.agent.apoptosis import ApoptosisManager
from monoco.features.memo.core import load_memos
from monoco.features.issue.core import list_issues
from monoco.core.config import get_config

logger = logging.getLogger("monoco.daemon.scheduler")


class SchedulerService:
    """
    Event-driven scheduler service for agent orchestration.
    
    Responsibilities:
    - Initialize and manage event handlers
    - Monitor sessions and emit lifecycle events
    - Watch for memo/issue changes and emit trigger events
    - Coordinate with AgentScheduler for task execution
    
    Note: FEAT-0160 refactored to use AgentScheduler abstraction.
    """
    
    MEMO_CHECK_INTERVAL = 5  # seconds
    ISSUE_CHECK_INTERVAL = 5  # seconds
    SESSION_CHECK_INTERVAL = 2  # seconds
    
    def __init__(self, project_manager: ProjectManager):
        self.project_manager = project_manager
        self.session_managers: Dict[str, SessionManager] = {}
        self.apoptosis_managers: Dict[str, ApoptosisManager] = {}
        self.handler_registry = EventHandlerRegistry()
        
        # Initialize AgentScheduler (FEAT-0160)
        scheduler_config = self._load_scheduler_config()
        self.agent_scheduler: AgentScheduler = LocalProcessScheduler(
            max_concurrent=scheduler_config.get("max_concurrent", 5),
            project_root=Path.cwd(),
        )
        
        # Initialize SemaphoreManager with config
        config = self._load_concurrency_config()
        self.semaphore_manager = SemaphoreManager(config)
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._running = False
        
        # State tracking for event emission
        self._memo_counts: Dict[str, int] = {}
        self._issue_states: Dict[str, Dict[str, Any]] = {}
    
    def _load_scheduler_config(self) -> Dict[str, Any]:
        """Load scheduler configuration from config files and env vars."""
        config = {"max_concurrent": 5}
        
        try:
            settings = get_config()
            
            # Check for concurrency config
            if hasattr(settings, "agent") and hasattr(settings.agent, "concurrency"):
                concurrency_config = settings.agent.concurrency
                if hasattr(concurrency_config, "global_max"):
                    config["max_concurrent"] = concurrency_config.global_max
            
            # Check for environment variable override
            env_max_agents = os.environ.get("MONOCO_MAX_AGENTS")
            if env_max_agents:
                try:
                    config["max_concurrent"] = int(env_max_agents)
                    logger.info(f"Overriding max_concurrent from environment: {env_max_agents}")
                except ValueError:
                    logger.warning(f"Invalid MONOCO_MAX_AGENTS value: {env_max_agents}")
            
            return config
        except Exception as e:
            logger.warning(f"Failed to load scheduler config: {e}. Using defaults.")
            return config
    
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
        """Get or create session and apoptosis managers for a project."""
        key = str(project_path)
        if key not in self.session_managers:
            sm = SessionManager(project_root=project_path)
            self.session_managers[key] = sm
            self.apoptosis_managers[key] = ApoptosisManager(sm)
            
            # Register event handlers for this project
            self._register_handlers(sm, self.apoptosis_managers[key])
        
        return self.session_managers[key], self.apoptosis_managers[key]
    
    def _register_handlers(
        self,
        session_manager: SessionManager,
        apoptosis_manager: ApoptosisManager,
    ):
        """Register event handlers for a project."""
        self.handler_registry.register_architect(
            session_manager, self.semaphore_manager
        )
        self.handler_registry.register_engineer(
            session_manager, self.semaphore_manager
        )
        self.handler_registry.register_coroner(
            session_manager, self.semaphore_manager, apoptosis_manager
        )
        # Reviewer is registered but only responds to PR_CREATED events
        self.handler_registry.register_reviewer(
            session_manager, self.semaphore_manager
        )
    
    async def start(self):
        """Start the scheduler service."""
        logger.info("Starting Scheduler Service (event-driven)...")
        self._running = True
        
        # Start event bus
        await event_bus.start()
        
        # Start agent scheduler (FEAT-0160)
        await self.agent_scheduler.start()
        
        # Initialize managers for all projects
        for project_ctx in self.project_manager.projects.values():
            self.get_managers(project_ctx.path)
        
        # Start background monitoring tasks (for event emission)
        self._tasks = [
            asyncio.create_task(self._memo_watcher_loop()),
            asyncio.create_task(self._issue_watcher_loop()),
            asyncio.create_task(self._session_monitor_loop()),
        ]
        
        logger.info("Scheduler Service started with event-driven architecture")
    
    def stop(self):
        """Stop the scheduler service."""
        logger.info("Stopping Scheduler Service...")
        self._running = False
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Stop agent scheduler (FEAT-0160)
        asyncio.create_task(self.agent_scheduler.stop())
        
        # Stop event bus
        asyncio.create_task(event_bus.stop())
        
        # Unregister handlers
        self.handler_registry.unregister_all()
        
        # Terminate all sessions
        for sm in self.session_managers.values():
            for session in sm.list_sessions():
                session.terminate()
        
        logger.info("Scheduler Service stopped")
    
    async def _memo_watcher_loop(self):
        """Watch for memo changes and emit MEMO_THRESHOLD events."""
        logger.info("Starting memo watcher loop")
        
        while self._running:
            try:
                await self._check_memo_thresholds()
                await asyncio.sleep(self.MEMO_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in memo watcher: {e}")
                await asyncio.sleep(self.MEMO_CHECK_INTERVAL)
    
    async def _check_memo_thresholds(self):
        """Check memo counts and emit threshold events."""
        for project_ctx in self.project_manager.projects.values():
            project_id = project_ctx.id
            issues_root = project_ctx.issues_root
            
            try:
                memos = load_memos(issues_root)
                pending_count = len([m for m in memos if m.status == "pending"])
                
                prev_count = self._memo_counts.get(project_id, 0)
                self._memo_counts[project_id] = pending_count
                
                # Emit threshold event when crossing the threshold
                threshold = 5  # Configurable
                if prev_count < threshold <= pending_count:
                    logger.info(f"Memo threshold reached for {project_id}: {pending_count}")
                    await event_bus.publish(
                        AgentEventType.MEMO_THRESHOLD,
                        {
                            "project_id": project_id,
                            "issues_root": str(issues_root),
                            "memo_count": pending_count,
                            "threshold": threshold,
                        },
                        source="scheduler.memo_watcher"
                    )
            except Exception as e:
                logger.error(f"Error checking memos for {project_id}: {e}")
    
    async def _issue_watcher_loop(self):
        """Watch for issue state changes and emit events."""
        logger.info("Starting issue watcher loop")
        
        while self._running:
            try:
                await self._check_issue_changes()
                await asyncio.sleep(self.ISSUE_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in issue watcher: {e}")
                await asyncio.sleep(self.ISSUE_CHECK_INTERVAL)
    
    async def _check_issue_changes(self):
        """Check issue states and emit change events."""
        for project_ctx in self.project_manager.projects.values():
            project_id = project_ctx.id
            issues_root = project_ctx.issues_root
            
            try:
                issues = list_issues(issues_root)
                
                for issue in issues:
                    issue_key = f"{project_id}:{issue.id}"
                    prev_state = self._issue_states.get(issue_key, {})
                    
                    current_state = {
                        "status": issue.status,
                        "stage": issue.stage,
                    }
                    
                    # Check for stage changes
                    if prev_state.get("stage") != issue.stage:
                        logger.debug(f"Issue {issue.id} stage changed: {prev_state.get('stage')} -> {issue.stage}")
                        await event_bus.publish(
                            AgentEventType.ISSUE_STAGE_CHANGED,
                            {
                                "project_id": project_id,
                                "issue_id": issue.id,
                                "issue_title": issue.title,
                                "old_stage": prev_state.get("stage"),
                                "new_stage": issue.stage,
                                "issue_status": issue.status,
                            },
                            source="scheduler.issue_watcher"
                        )
                    
                    # Check for status changes
                    if prev_state.get("status") != issue.status:
                        logger.debug(f"Issue {issue.id} status changed: {prev_state.get('status')} -> {issue.status}")
                        await event_bus.publish(
                            AgentEventType.ISSUE_STATUS_CHANGED,
                            {
                                "project_id": project_id,
                                "issue_id": issue.id,
                                "old_status": prev_state.get("status"),
                                "new_status": issue.status,
                            },
                            source="scheduler.issue_watcher"
                        )
                    
                    self._issue_states[issue_key] = current_state
                    
            except Exception as e:
                logger.error(f"Error checking issues for {project_id}: {e}")
    
    async def _session_monitor_loop(self):
        """Monitor active sessions and emit lifecycle events."""
        logger.info("Starting session monitor loop")
        
        while self._running:
            try:
                await self._monitor_sessions()
                await asyncio.sleep(self.SESSION_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session monitor: {e}")
                await asyncio.sleep(self.SESSION_CHECK_INTERVAL)
    
    async def _monitor_sessions(self):
        """Check session statuses and emit lifecycle events."""
        for sm in self.session_managers.values():
            for session in sm.list_sessions():
                if session.model.status in ["running", "pending"]:
                    prev_status = session.model.status
                    status = session.refresh_status()
                    
                    # Emit events based on status changes
                    if prev_status != status:
                        if status == "completed":
                            await event_bus.publish(
                                AgentEventType.SESSION_COMPLETED,
                                {
                                    "session_id": session.model.id,
                                    "issue_id": session.model.issue_id,
                                    "role_name": session.model.role_name,
                                },
                                source="scheduler.session_monitor"
                            )
                            # Clear failure record on success
                            self.semaphore_manager.clear_failure(session.model.issue_id)
                            
                        elif status == "failed":
                            await event_bus.publish(
                                AgentEventType.SESSION_FAILED,
                                {
                                    "session_id": session.model.id,
                                    "issue_id": session.model.issue_id,
                                    "role_name": session.model.role_name,
                                    "reason": "Session failed",
                                },
                                source="scheduler.session_monitor"
                            )
                            # Record failure for cooldown
                            self.semaphore_manager.record_failure(
                                session.model.issue_id, session.model.id
                            )
                            
                        elif status == "crashed":
                            await event_bus.publish(
                                AgentEventType.SESSION_CRASHED,
                                {
                                    "session_id": session.model.id,
                                    "issue_id": session.model.issue_id,
                                    "role_name": session.model.role_name,
                                    "reason": "Session crashed",
                                },
                                source="scheduler.session_monitor"
                            )
                            # Record failure for cooldown
                            self.semaphore_manager.record_failure(
                                session.model.issue_id, session.model.id
                            )
                    else:
                        # Track active session in semaphore
                        self.semaphore_manager.acquire(session.model.id, session.model.role_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler service statistics."""
        return {
            "running": self._running,
            "event_bus": event_bus.get_stats(),
            "agent_scheduler": self.agent_scheduler.get_stats(),
            "semaphore": self.semaphore_manager.get_status(),
            "projects": len(self.session_managers),
            "memo_counts": self._memo_counts.copy(),
        }
