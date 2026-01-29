from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from .worker import Worker


class Session(BaseModel):
    """
    Represents a runtime session of a worker.
    Persisted state of the session.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(..., description="Unique session ID (likely UUID)")
    issue_id: str = Field(..., description="The Issue ID this session is working on")
    role_name: str = Field(..., description="Name of the role employed")
    status: str = Field(
        default="pending", description="pending, running, suspended, terminated"
    )
    branch_name: str = Field(
        ..., description="Git branch name associated with this session"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    # History could be a list of logs or pointers to git commits
    # For now, let's keep it simple. The git log IS the history.


class RuntimeSession:
    """
    The in-memory wrapper around the Session model and the active Worker.
    """

    def __init__(self, session_model: Session, worker: Worker):
        self.model = session_model
        self.worker = worker

    def start(self, context: Optional[dict] = None):
        print(
            f"Session {self.model.id}: Starting worker on branch {self.model.branch_name}"
        )
        # In real impl, checking out branch happening here
        self.model.status = "running"
        self.model.updated_at = datetime.now()

        try:
            self.worker.start(context)
            # Async mode: we assume it started running.
            # Use poll or refresh_status to check later.
            self.model.status = "running"
        except Exception:
            self.model.status = "failed"
            raise
        finally:
            self.model.updated_at = datetime.now()

    def refresh_status(self) -> str:
        """
        Polls the worker and updates the session model status.
        """
        worker_status = self.worker.poll()
        self.model.status = worker_status
        self.model.updated_at = datetime.now()
        return worker_status

    def suspend(self):
        print(f"Session {self.model.id}: Suspending worker")
        self.worker.stop()
        self.model.status = "suspended"
        self.model.updated_at = datetime.now()
        # In real impl, ensure git commit of current state?

    def resume(self):
        print(f"Session {self.model.id}: Resuming worker")
        self.worker.start()  # In real impl, might need to re-init process

        # Async mode: assume running
        self.model.status = "running"
        self.model.updated_at = datetime.now()

    def terminate(self):
        print(f"Session {self.model.id}: Terminating")
        self.worker.stop()
        self.model.status = "terminated"
        self.model.updated_at = datetime.now()
