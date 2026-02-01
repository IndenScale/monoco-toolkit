from datetime import datetime
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict

from .worker import Worker
from monoco.core.hooks import HookContext, HookRegistry, get_registry
from monoco.core.config import find_monoco_root


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
    pid: Optional[int] = Field(default=None, description="Process ID of the worker")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    # History could be a list of logs or pointers to git commits
    # For now, let's keep it simple. The git log IS the history.


class RuntimeSession:
    """
    The in-memory wrapper around the Session model and the active Worker.
    """

    def __init__(
        self,
        session_model: Session,
        worker: Optional[Worker],
        hook_registry: Optional[HookRegistry] = None,
        project_root: Optional[Path] = None,
        save_callback: Optional[callable] = None,
    ):
        self.model = session_model
        self.worker = worker
        self.hook_registry = hook_registry or get_registry()
        self.project_root = project_root or find_monoco_root()
        self.save_callback = save_callback

    def _save(self):
        if self.save_callback:
            self.save_callback(self.model)

    def _create_hook_context(self) -> HookContext:
        """Create a HookContext from the current session state."""
        return HookContext.from_runtime_session(self, self.project_root)

    def start(self, context: Optional[dict] = None):
        if not self.worker:
            raise RuntimeError(
                "Cannot start session in observer mode (no worker attached)"
            )

        print(
            f"Session {self.model.id}: Starting worker on branch {self.model.branch_name}"
        )
        # In real impl, checking out branch happening here
        self.model.status = "running"
        self.model.updated_at = datetime.now()

        try:
            # Execute on_session_start hooks
            hook_context = self._create_hook_context()
            self.hook_registry.execute_on_session_start(hook_context)

            self.worker.start(context)
            # Async mode: we assume it started running.
            # Use poll or refresh_status to check later.
            self.model.status = "running"
            self.model.pid = self.worker.process_id
        except Exception:
            self.model.status = "failed"
            raise
        finally:
            self.model.updated_at = datetime.now()
            self._save()

    def refresh_status(self) -> str:
        """
        Polls the worker and updates the session model status.
        """
        if self.worker:
            worker_status = self.worker.poll()
            self.model.status = worker_status
        else:
            # Observer mode
            if self.model.pid:
                try:
                    import os

                    # Check if process exists.
                    # kill(pid, 0) does not send a signal but raises OSError if pid missing
                    os.kill(self.model.pid, 0)
                    # If we are here, process exists. We assume running if it was running.
                    # We can't detect "suspended" easily without psutil.
                    if self.model.status == "terminated":
                        # If we thought it was terminated but it's alive, maybe update?
                        # Or keep as terminated? Let's assume running if found.
                        pass
                except OSError:
                    self.model.status = "terminated"
            else:
                self.model.status = "terminated"

        self.model.updated_at = datetime.now()
        self._save()
        return self.model.status

    def suspend(self):
        if not self.worker:
            raise RuntimeError("Cannot suspend session in observer mode")

        print(f"Session {self.model.id}: Suspending worker")
        self.worker.stop()
        self.model.status = "suspended"
        self.model.updated_at = datetime.now()
        self._save()
        # In real impl, ensure git commit of current state?

    def resume(self):
        if not self.worker:
            raise RuntimeError("Cannot resume session in observer mode")

        print(f"Session {self.model.id}: Resuming worker")
        self.worker.start()  # In real impl, might need to re-init process

        # Async mode: assume running
        self.model.status = "running"
        self.model.pid = self.worker.process_id
        self.model.updated_at = datetime.now()
        self._save()

    def terminate(self):
        print(f"Session {self.model.id}: Terminating")

        # Execute on_session_end hooks before stopping worker
        # This allows hooks to perform cleanup while session context is still valid
        try:
            hook_context = self._create_hook_context()
            results = self.hook_registry.execute_on_session_end(hook_context)

            # Log hook results
            for result in results:
                if result.status == "failure":
                    print(f"  Hook warning: {result.message}")
        except Exception as e:
            # Don't let hook errors prevent session termination
            print(f"  Hook execution error: {e}")

        if self.worker:
            self.worker.stop()

        self.model.status = "terminated"
        self.model.updated_at = datetime.now()
        self._save()
