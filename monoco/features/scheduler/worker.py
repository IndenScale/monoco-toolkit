from typing import Optional
from .models import RoleTemplate


class Worker:
    """
    Represents an active or pending agent session assigned to a specific role and issue.
    """

    def __init__(self, role: RoleTemplate, issue_id: str):
        self.role = role
        self.issue_id = issue_id
        self.status = "pending"  # pending, running, suspended, terminated
        self.process_id: Optional[int] = None

    def start(self, context: Optional[dict] = None):
        """
        Start the worker session.
        """
        if self.status != "pending":
            return

        print(f"Starting worker {self.role.name} for issue {self.issue_id}")
        self.status = "running"

        try:
            self._execute_work(context)
            self.status = "completed"
        except Exception as e:
            print(f"Worker failed: {e}")
            self.status = "failed"
            raise

    def _execute_work(self, context: Optional[dict] = None):
        import subprocess
        import sys

        # Prepare the prompt
        if self.role.name == "drafter" and context:
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
            # Execute CLI agent with YOLO mode
            engine_args = (
                [engine, "-y", prompt] if engine == "gemini" else [engine, prompt]
            )

            process = subprocess.Popen(
                engine_args, stdout=sys.stdout, stderr=sys.stderr, text=True
            )
            self.process_id = process.pid

            # Wait for completion
            process.wait()

            if process.returncode != 0:
                raise RuntimeError(
                    f"Agent engine {engine} failed (exit code {process.returncode})"
                )

        except FileNotFoundError:
            raise RuntimeError(
                f"Agent engine '{engine}' not found. Please ensure it is installed and in PATH."
            )
        except Exception as e:
            print(f"[{self.role.name}] Process Error: {e}")
            raise

    def stop(self):
        """
        Stop the worker session.
        """
        if self.status == "terminated":
            return

        print(f"Stopping worker {self.role.name} for issue {self.issue_id}")
        self.status = "terminated"
        self.process_id = None

    def __repr__(self):
        return (
            f"<Worker role={self.role.name} issue={self.issue_id} status={self.status}>"
        )
