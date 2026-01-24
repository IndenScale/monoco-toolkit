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

    def start(self):
        """
        Start the worker session.
        This is a placeholder for the actual process spawning logic.
        """
        if self.status != "pending":
            return

        print(f"Starting worker {self.role.name} for issue {self.issue_id}")
        self.status = "running"
        # In a real implementation, this would spawn a subprocess or thread

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
