import logging
from typing import List, Optional, Dict, Any
from asyncio import Queue
from pathlib import Path
from datetime import datetime, timedelta
from threading import Lock

import json

logger = logging.getLogger("monoco.daemon.services")


class Broadcaster:
    """
    Manages SSE subscriptions and broadcasts events to all connected clients.
    """

    def __init__(self):
        self.subscribers: List[Queue] = []

    async def subscribe(self) -> Queue:
        queue = Queue()
        self.subscribers.append(queue)
        logger.info(f"New client subscribed. Total clients: {len(self.subscribers)}")
        return queue

    async def unsubscribe(self, queue: Queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            logger.info(f"Client unsubscribed. Total clients: {len(self.subscribers)}")

    async def broadcast(self, event_type: str, payload: dict):
        if not self.subscribers:
            return

        message = {"event": event_type, "data": json.dumps(payload)}

        # Dispatch to all queues
        for queue in self.subscribers:
            await queue.put(message)

        logger.debug(f"Broadcasted {event_type} to {len(self.subscribers)} clients.")


# Monitors moved to monoco.core.git and monoco.features.issue.monitor


from monoco.core.workspace import MonocoProject, Workspace


class ProjectContext:
    """
    Holds the runtime state for a single project.
    Now wraps the core MonocoProject primitive.
    """

    def __init__(self, project: MonocoProject, broadcaster: Broadcaster):
        self.project = project
        self.id = project.id
        self.name = project.name
        self.path = project.path
        self.issues_root = project.issues_root
        self.monitor = IssueMonitor(self.issues_root, broadcaster, project_id=self.id)

    async def start(self):
        await self.monitor.start()

    def stop(self):
        self.monitor.stop()


class SemaphoreManager:
    """
    Manages concurrency limits for agent sessions using role-based semaphores.
    Prevents fork bomb by limiting concurrent agents per role and globally.
    """

    def __init__(self, config: Optional[Any] = None):
        """
        Initialize the SemaphoreManager.
        
        Args:
            config: AgentConcurrencyConfig or dict with concurrency settings
        """
        self._lock = Lock()
        self._active_sessions: Dict[str, str] = {}  # session_id -> role_name
        self._role_counts: Dict[str, int] = {}  # role_name -> count
        self._failure_registry: Dict[str, datetime] = {}  # issue_id -> last_failure_time
        
        # Default conservative limits
        self._global_max = 3
        self._role_limits: Dict[str, int] = {
            "Engineer": 1,
            "Architect": 1,
            "Reviewer": 1,
            "Planner": 1,
        }
        self._failure_cooldown_seconds = 60
        
        # Apply config if provided
        if config:
            self._apply_config(config)
    
    def _apply_config(self, config: Any) -> None:
        """Apply configuration settings."""
        # Handle both dict and Pydantic model
        if hasattr(config, 'global_max'):
            self._global_max = config.global_max
        if hasattr(config, 'failure_cooldown_seconds'):
            self._failure_cooldown_seconds = config.failure_cooldown_seconds
        
        # Role-specific limits
        for role in ["Engineer", "Architect", "Reviewer", "Planner"]:
            if hasattr(config, role.lower()):
                self._role_limits[role] = getattr(config, role.lower())
    
    def can_acquire(self, role_name: str, issue_id: Optional[str] = None) -> bool:
        """
        Check if a new session can be acquired for the given role.
        
        Args:
            role_name: The role to check (e.g., "Engineer", "Architect")
            issue_id: Optional issue ID to check for failure cooldown
            
        Returns:
            True if the session can be started, False otherwise
        """
        with self._lock:
            # Check global limit
            total_active = len(self._active_sessions)
            if total_active >= self._global_max:
                logger.warning(
                    f"Global concurrency limit reached ({self._global_max}). "
                    f"Cannot spawn {role_name}."
                )
                return False
            
            # Check role-specific limit
            role_count = self._role_counts.get(role_name, 0)
            role_limit = self._role_limits.get(role_name, 1)
            if role_count >= role_limit:
                logger.warning(
                    f"Role concurrency limit reached for {role_name} "
                    f"({role_count}/{role_limit})."
                )
                return False
            
            # Check failure cooldown for this issue
            if issue_id and issue_id in self._failure_registry:
                last_failure = self._failure_registry[issue_id]
                cooldown = timedelta(seconds=self._failure_cooldown_seconds)
                if datetime.now() - last_failure < cooldown:
                    remaining = cooldown - (datetime.now() - last_failure)
                    logger.warning(
                        f"Issue {issue_id} is in cooldown period. "
                        f"Remaining: {remaining.seconds}s. Skipping spawn."
                    )
                    return False
            
            return True
    
    def acquire(self, session_id: str, role_name: str) -> bool:
        """
        Acquire a slot for a new session.
        
        Args:
            session_id: Unique identifier for the session
            role_name: The role of the session
            
        Returns:
            True if acquired successfully, False otherwise
        """
        with self._lock:
            if session_id in self._active_sessions:
                logger.warning(f"Session {session_id} already tracked")
                return True
            
            self._active_sessions[session_id] = role_name
            self._role_counts[role_name] = self._role_counts.get(role_name, 0) + 1
            logger.info(
                f"Acquired slot for {role_name} session {session_id}. "
                f"Global: {len(self._active_sessions)}/{self._global_max}, "
                f"Role: {self._role_counts[role_name]}/{self._role_limits.get(role_name, 1)}"
            )
            return True
    
    def release(self, session_id: str) -> None:
        """
        Release a slot when a session ends.
        
        Args:
            session_id: The session ID to release
        """
        with self._lock:
            if session_id not in self._active_sessions:
                return
            
            role_name = self._active_sessions.pop(session_id)
            self._role_counts[role_name] = max(0, self._role_counts.get(role_name, 0) - 1)
            logger.info(
                f"Released slot for {role_name} session {session_id}. "
                f"Global: {len(self._active_sessions)}/{self._global_max}"
            )
    
    def record_failure(self, issue_id: str, session_id: Optional[str] = None) -> None:
        """
        Record a failure for cooldown purposes.
        
        Args:
            issue_id: The issue that failed
            session_id: Optional session ID to release
        """
        with self._lock:
            self._failure_registry[issue_id] = datetime.now()
            logger.warning(
                f"Recorded failure for issue {issue_id}. "
                f"Cooldown: {self._failure_cooldown_seconds}s"
            )
        
        # Release the slot if session_id provided
        if session_id:
            self.release(session_id)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current semaphore status for monitoring.
        
        Returns:
            Dict with current counts and limits
        """
        with self._lock:
            return {
                "global": {
                    "active": len(self._active_sessions),
                    "limit": self._global_max,
                },
                "roles": {
                    role: {
                        "active": self._role_counts.get(role, 0),
                        "limit": limit,
                    }
                    for role, limit in self._role_limits.items()
                },
                "cooldown_issues": len(self._failure_registry),
            }
    
    def clear_failure(self, issue_id: str) -> None:
        """Clear failure record for an issue (e.g., after successful completion)."""
        with self._lock:
            if issue_id in self._failure_registry:
                del self._failure_registry[issue_id]
                logger.info(f"Cleared failure record for issue {issue_id}")


class ProjectManager:
    """
    Discovers and manages multiple Monoco projects within a workspace.
    Uses core Workspace primitive for discovery.
    """

    def __init__(self, workspace_root: Path, broadcaster: Broadcaster):
        self.workspace_root = workspace_root
        self.broadcaster = broadcaster
        self.projects: Dict[str, ProjectContext] = {}

    def scan(self):
        """
        Scans workspace for Monoco projects using core logic.
        """
        logger.info(f"Scanning workspace: {self.workspace_root}")
        workspace = Workspace.discover(self.workspace_root)

        for project in workspace.projects:
            if project.id not in self.projects:
                ctx = ProjectContext(project, self.broadcaster)
                self.projects[ctx.id] = ctx
                logger.info(f"Registered project: {ctx.id} ({ctx.path})")

    async def start_all(self):
        self.scan()
        for project in self.projects.values():
            await project.start()

    def stop_all(self):
        for project in self.projects.values():
            project.stop()

    def get_project(self, project_id: str) -> Optional[ProjectContext]:
        return self.projects.get(project_id)

    def list_projects(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": p.id,
                "name": p.name,
                "path": str(p.path),
                "issues_path": str(p.issues_root),
            }
            for p in self.projects.values()
        ]


from monoco.features.issue.monitor import IssueMonitor


class ProjectContext:
    """
    Holds the runtime state for a single project.
    Now wraps the core MonocoProject primitive.
    """

    def __init__(self, project: MonocoProject, broadcaster: Broadcaster):
        self.project = project
        self.id = project.id
        self.name = project.name
        self.path = project.path
        self.issues_root = project.issues_root

        async def on_upsert(issue_data: dict):
            await broadcaster.broadcast(
                "issue_upserted", {"issue": issue_data, "project_id": self.id}
            )

        async def on_delete(issue_data: dict):
            # We skip broadcast here if it's part of a move?
            # Actually, standard upsert/delete is fine, but we need a specialized event for MOVE
            # to help VS Code redirect without closing/reopening.
            await broadcaster.broadcast(
                "issue_deleted", {"id": issue_data["id"], "project_id": self.id}
            )

        self.monitor = IssueMonitor(self.issues_root, on_upsert, on_delete)

    async def notify_move(self, old_path: str, new_path: str, issue_data: dict):
        """Explicitly notify frontend about a logical move (Physical path changed)."""
        await self.broadcaster.broadcast(
            "issue_moved",
            {
                "old_path": old_path,
                "new_path": new_path,
                "issue": issue_data,
                "project_id": self.id,
            },
        )

    async def start(self):
        await self.monitor.start()

    def stop(self):
        self.monitor.stop()
