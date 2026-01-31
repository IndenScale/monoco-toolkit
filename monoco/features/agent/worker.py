from typing import Optional
from .models import RoleTemplate
from .engines import EngineFactory


class Worker:
    """
    Represents an active or pending agent session assigned to a specific role and issue.
    """

    def __init__(self, role: RoleTemplate, issue_id: str, timeout: Optional[int] = None):
        self.role = role
        self.issue_id = issue_id
        self.timeout = timeout
        self.status = "pending"  # pending, running, suspended, terminated
        self.process_id: Optional[int] = None
        self._process = None
        self.start_at: Optional[float] = None

    def start(self, context: Optional[dict] = None):
        """
        Start the worker session asynchronously.
        """
        # Allow restart if not currently running
        if self.status == "running":
            return

        print(f"Starting worker {self.role.name} for issue {self.issue_id}")

        try:
            import time
            self.start_at = time.time()
            self._execute_work(context)
            self.status = "running"
        except Exception as e:
            print(f"Worker failed to start: {e}")
            self.status = "failed"
            raise

    def _execute_work(self, context: Optional[dict] = None):
        import subprocess
        import sys

        # Prepare the prompt
        # We treat 'Planner' as a drafter when context is provided (Draft Mode)
        if (self.role.name == "drafter" or self.role.name == "Planner") and context:
            issue_type = context.get("type", "feature")
            description = context.get("description", "No description")
            prompt = (
                f"You are a Drafter in the Monoco project.\n\n"
                f"Task: Create a new {issue_type} issue based on this request: {description}\n\n"
                "Constraints:\n"
                "1. Use 'monoco issue create' to generate the file.\n"
                "2. Use 'monoco issue update' or direct file editing to enrich Objective and Tasks.\n"
                "3. IMPORTANT: Once the issue file is created and filled with high-quality content, EXIT search or interactive mode immediately.\n"
                "4. Do not perform any other development tasks."
            )
        else:
            prompt = (
                f"{self.role.system_prompt}\n\n"
                f"Issue context: {self.issue_id}\n"
                f"Goal: {self.role.goal}\n"
            )
            if context and "description" in context:
                prompt += f"Specific Task: {context['description']}"

        engine = self.role.engine

        print(f"[{self.role.name}] Engine: {engine}")
        print(f"[{self.role.name}] Goal: {self.role.goal}")

        try:
            # Use factory to get the appropriate engine adapter
            adapter = EngineFactory.create(engine)
            engine_args = adapter.build_command(prompt)

            self._process = subprocess.Popen(
                engine_args, stdout=sys.stdout, stderr=sys.stderr, text=True
            )
            self.process_id = self._process.pid

            # DO NOT WAIT HERE.
            # The scheduler/monitoring loop is responsible for checking status.

        except ValueError as e:
            # Engine not supported by factory
            raise RuntimeError(f"Unsupported engine '{engine}'. {str(e)}")
        except FileNotFoundError:
            raise RuntimeError(
                f"Agent engine '{engine}' not found. Please ensure it is installed and in PATH."
            )
        except Exception as e:
            print(f"[{self.role.name}] Process Error: {e}")
            raise

    def poll(self) -> str:
        """
        Check process status. Returns current worker status.
        Updates self.status if process has finished.
        """
        if not self._process:
            return self.status

        # Check timeout
        if (
            self.status == "running"
            and self.timeout
            and self.start_at
        ):
            import time

            elapsed = time.time() - self.start_at
            if elapsed > self.timeout:
                print(
                    f"\n[{self.role.name}] [bold red]Timeout exceeded[/bold red] ({self.timeout}s). Terminating process..."
                )
                self.stop()
                self.status = "timeout"
                return self.status

        returncode = self._process.poll()
        if returncode is None:
            return "running"

        if returncode == 0:
            self.status = "completed"
        else:
            self.status = "failed"

        return self.status

    def wait(self):
        """
        Block until process finishes.
        """
        if self._process:
            self._process.wait()
            self.poll()  # Update status

    def stop(self):
        """
        Stop the worker session and kill the process if running.
        """
        if self.status == "terminated":
            return

        print(f"Stopping worker {self.role.name} for issue {self.issue_id}")

        if self._process:
            try:
                # Try graceful termination
                self._process.terminate()
                # Wait a bit
                try:
                    self._process.wait(timeout=2)
                except Exception:
                    # Force kill if still running
                    self._process.kill()
            except Exception as e:
                print(f"Error stopping process: {e}")

        self.status = "terminated"
        self.process_id = None
        self._process = None

    def __repr__(self):
        return (
            f"<Worker role={self.role.name} issue={self.issue_id} status={self.status}>"
        )
