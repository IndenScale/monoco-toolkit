from typing import List, Optional
from pydantic import BaseModel
from ..models import IssueStatus, IssueStage, IssueSolution, current_time
from .models import Issue


class Transition(BaseModel):
    name: str
    from_status: Optional[IssueStatus] = None  # None means any
    from_stage: Optional[IssueStage] = None  # None means any
    to_status: IssueStatus
    to_stage: Optional[IssueStage] = None
    required_solution: Optional[IssueSolution] = None
    description: str = ""

    def is_allowed(self, issue: Issue) -> bool:
        if self.from_status and issue.status != self.from_status:
            return False
        if self.from_stage and issue.frontmatter.stage != self.from_stage:
            return False
        return True


class TransitionService:
    def __init__(self):
        self.transitions: List[Transition] = [
            # Open -> Backlog
            Transition(
                name="freeze",
                from_status=IssueStatus.OPEN,
                to_status=IssueStatus.BACKLOG,
                to_stage=IssueStage.FREEZED,
                description="Move open issue to backlog",
            ),
            # Backlog -> Open
            Transition(
                name="activate",
                from_status=IssueStatus.BACKLOG,
                to_status=IssueStatus.OPEN,
                to_stage=IssueStage.DRAFT,  # Reset to draft?
                description="Restore issue from backlog",
            ),
            # Open (Draft) -> Open (Doing)
            Transition(
                name="start",
                from_status=IssueStatus.OPEN,
                from_stage=IssueStage.DRAFT,
                to_status=IssueStatus.OPEN,
                to_stage=IssueStage.DOING,
                description="Start working on the issue",
            ),
            # Open (Doing) -> Open (Review)
            Transition(
                name="submit",
                from_status=IssueStatus.OPEN,
                from_stage=IssueStage.DOING,
                to_status=IssueStatus.OPEN,
                to_stage=IssueStage.REVIEW,
                description="Submit for review",
            ),
            # Open (Review) -> Open (Doing) - reject
            Transition(
                name="reject",
                from_status=IssueStatus.OPEN,
                from_stage=IssueStage.REVIEW,
                to_status=IssueStatus.OPEN,
                to_stage=IssueStage.DOING,
                description="Reject review and return to doing",
            ),
            # Open (Review) -> Closed (Implemented)
            Transition(
                name="accept",
                from_status=IssueStatus.OPEN,
                from_stage=IssueStage.REVIEW,
                to_status=IssueStatus.CLOSED,
                to_stage=IssueStage.DONE,
                required_solution=IssueSolution.IMPLEMENTED,
                description="Accept and close issue",
            ),
            # Direct Close (Cancel, Wontfix, Duplicate)
            Transition(
                name="cancel",
                to_status=IssueStatus.CLOSED,
                to_stage=IssueStage.DONE,
                required_solution=IssueSolution.CANCELLED,
                description="Cancel the issue",
            ),
            Transition(
                name="wontfix",
                to_status=IssueStatus.CLOSED,
                to_stage=IssueStage.DONE,
                required_solution=IssueSolution.WONTFIX,
                description="Mark as wontfix",
            ),
        ]

    def get_available_transitions(self, issue: Issue) -> List[Transition]:
        return [t for t in self.transitions if t.is_allowed(issue)]

    def apply_transition(self, issue: Issue, transition_name: str) -> Issue:
        # Find transition
        candidates = [t for t in self.transitions if t.name == transition_name]
        valid_transition = None
        for t in candidates:
            if t.is_allowed(issue):
                valid_transition = t
                break

        if not valid_transition:
            raise ValueError(
                f"Transition '{transition_name}' is not allowed for current state."
            )

        # Apply changes
        issue.frontmatter.status = valid_transition.to_status
        if valid_transition.to_stage:
            issue.frontmatter.stage = valid_transition.to_stage
        if valid_transition.required_solution:
            issue.frontmatter.solution = valid_transition.required_solution

        issue.frontmatter.updated_at = current_time()

        # Logic for closed_at, opened_at etc.
        if (
            valid_transition.to_status == IssueStatus.CLOSED
            and issue.frontmatter.closed_at is None
        ):
            issue.frontmatter.closed_at = current_time()

        if (
            valid_transition.to_status == IssueStatus.OPEN
            and issue.frontmatter.opened_at is None
        ):
            issue.frontmatter.opened_at = current_time()

        return issue
