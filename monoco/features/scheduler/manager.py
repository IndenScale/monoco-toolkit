from typing import Dict, List, Optional
import uuid
from .models import RoleTemplate
from .worker import Worker
from .session import Session, RuntimeSession


class SessionManager:
    """
    Manages the lifecycle of sessions.
    Responsible for creating, tracking, and retrieving sessions.
    """

    def __init__(self):
        # In-memory storage for now. In prod, this might be a DB or file-backed.
        self._sessions: Dict[str, RuntimeSession] = {}

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

        worker = Worker(role, issue_id)
        runtime = RuntimeSession(session_model, worker)
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
