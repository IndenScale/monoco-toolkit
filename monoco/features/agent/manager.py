from typing import Dict, List, Optional
import uuid
from pathlib import Path

from .models import RoleTemplate
from .worker import Worker
from .session import Session, RuntimeSession
from monoco.core.hooks import HookRegistry, get_registry
from monoco.core.config import find_monoco_root, MonocoConfig


class SessionManager:
    """
    Manages the lifecycle of sessions.
    Responsible for creating, tracking, and retrieving sessions.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        hook_registry: Optional[HookRegistry] = None,
        config: Optional[MonocoConfig] = None,
    ):
        # In-memory storage for now. In prod, this might be a DB or file-backed.
        self._sessions: Dict[str, RuntimeSession] = {}
        self.project_root = project_root or find_monoco_root()
        self.config = config
        
        # Initialize hook registry
        self.hook_registry = hook_registry or get_registry()
        
        # Load hooks from config if available
        self._load_hooks_from_config()

    def _load_hooks_from_config(self) -> None:
        """Load and register hooks from configuration."""
        if self.config is None:
            try:
                from monoco.core.config import get_config
                self.config = get_config(str(self.project_root))
            except Exception:
                return
        
        # Load hooks from config
        if self.config and hasattr(self.config, "session_hooks"):
            hooks_config = self.config.session_hooks
            if hooks_config:
                self.hook_registry.load_from_config(hooks_config, self.project_root)

    def create_session(self, issue_id: str, role: RoleTemplate) -> RuntimeSession:
        session_id = str(uuid.uuid4())
        branch_name = (
            f"agent/{issue_id}/{session_id[:8]}"  # Simple branch naming strategy
        )

        session_model = Session(
            id=session_id,
            issue_id=issue_id,
            role_name=role.name,
            branch_name=branch_name,
        )

        # Get timeout from config
        timeout = 900
        if self.config and hasattr(self.config, "agent"):
            timeout = self.config.agent.timeout_seconds

        worker = Worker(role, issue_id, timeout=timeout)
        runtime = RuntimeSession(
            session_model, 
            worker,
            hook_registry=self.hook_registry,
            project_root=self.project_root,
        )
        self._sessions[session_id] = runtime
        return runtime

    def get_session(self, session_id: str) -> Optional[RuntimeSession]:
        return self._sessions.get(session_id)

    def list_sessions(self, issue_id: Optional[str] = None) -> List[RuntimeSession]:
        if issue_id:
            return [s for s in self._sessions.values() if s.model.issue_id == issue_id]
        return list(self._sessions.values())

    def terminate_session(self, session_id: str):
        session = self.get_session(session_id)
        if session:
            session.terminate()
            # We might want to keep the record for a while, so don't delete immediately
            # del self._sessions[session_id]
