from ..models import IssueStatus, IssueStage, IssueSolution
from .models import Transition, StateMachineConfig

DEFAULT_CONFIG = StateMachineConfig(
    transitions=[
        # --- UNIVERSAL AGENT ACTIONS ---
        Transition(
            name="investigate",
            label="Investigate",
            icon="$(telescope)",
            to_status=IssueStatus.OPEN,  # Dummy, doesn't change status
            command_template="monoco agent run investigate",
            description="Run agent investigation"
        ),

        # --- OPEN -> OPEN Transitions (Stage changes) ---
        Transition(
            name="start",
            label="Start",
            icon="$(play)",
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DRAFT,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.DOING,
            command_template="monoco issue start {id}",
            description="Start working on the issue"
        ),
        
        Transition(
            name="develop",
            label="Develop",
            icon="$(tools)",
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DOING,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.DOING,
            command_template="monoco agent run develop",
            description="Run agent development"
        ),

        Transition(
            name="stop",
            label="Stop",
            icon="$(stop)",
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DOING,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.DRAFT,
            command_template="monoco issue open {id}",
            description="Stop working and return to draft"
        ),
        Transition(
            name="submit",
            label="Submit",
            icon="$(check)",
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DOING,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.REVIEW,
            command_template="monoco issue submit {id}",
            description="Submit for review"
        ),
        Transition(
            name="reject",
            label="Reject",
            icon="$(error)",
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.REVIEW,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.DOING,
            command_template="monoco issue update {id} --stage doing",
            description="Reject review and return to doing"
        ),

        # --- OPEN -> CLOSED Transitions ---
        Transition(
            name="accept",
            label="Accept",
            icon="$(pass-filled)",
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.REVIEW,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            required_solution=IssueSolution.IMPLEMENTED,
            command_template="monoco issue close {id} --solution implemented",
            description="Accept and close issue"
        ),
        Transition(
            name="close_done",
            label="Close",
            icon="$(close)",
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DONE,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            required_solution=IssueSolution.IMPLEMENTED,
            command_template="monoco issue close {id} --solution implemented",
            description="Close completed issue"
        ),
        Transition(
            name="cancel",
            label="Cancel",
            icon="$(trash)",
            from_status=IssueStatus.OPEN,
            # Allowed from any stage except DONE (though core.py had a check for it)
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            required_solution=IssueSolution.CANCELLED,
            command_template="monoco issue cancel {id}",
            description="Cancel the issue"
        ),
        Transition(
            name="wontfix",
            label="Won't Fix",
            icon="$(circle-slash)",
            from_status=IssueStatus.OPEN,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            required_solution=IssueSolution.WONTFIX,
            command_template="monoco issue close {id} --solution wontfix",
            description="Mark as won't fix"
        ),

        # --- BACKLOG Transitions ---
        Transition(
            name="pull",
            label="Pull",
            icon="$(arrow-up)",
            from_status=IssueStatus.BACKLOG,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.DRAFT,
            command_template="monoco issue backlog pull {id}",
            description="Restore issue from backlog"
        ),
        Transition(
            name="cancel_backlog",
            label="Cancel",
            icon="$(trash)",
            from_status=IssueStatus.BACKLOG,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            required_solution=IssueSolution.CANCELLED,
            command_template="monoco issue cancel {id}",
            description="Cancel backlog issue"
        ),

        # --- CLOSED Transitions ---
        Transition(
            name="reopen",
            label="Reopen",
            icon="$(refresh)",
            from_status=IssueStatus.CLOSED,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.DRAFT,
            command_template="monoco issue open {id}",
            description="Reopen a closed issue"
        ),
        Transition(
            name="reopen_from_done",
            label="Reopen",
            icon="$(refresh)",
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DONE,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.DRAFT,
            command_template="monoco issue open {id}",
            description="Reopen a done issue"
        ),
    ]
)
