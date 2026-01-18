from monoco.core.config import IssueSchemaConfig, IssueTypeConfig, TransitionConfig, StateMachineConfig

DEFAULT_ISSUE_CONFIG = IssueSchemaConfig(
    types=[
        IssueTypeConfig(name="epic", label="Epic", prefix="EPIC", folder="Epics"),
        IssueTypeConfig(name="feature", label="Feature", prefix="FEAT", folder="Features"),
        IssueTypeConfig(name="chore", label="Chore", prefix="CHORE", folder="Chores"),
        IssueTypeConfig(name="fix", label="Fix", prefix="FIX", folder="Fixes"),
    ],
    statuses=["open", "closed", "backlog"],
    stages=["draft", "doing", "review", "done", "freezed"],
    solutions=["implemented", "cancelled", "wontfix", "duplicate"],
    workflows=[
        # --- UNIVERSAL AGENT ACTIONS ---


        # --- OPEN -> OPEN Transitions (Stage changes) ---
        TransitionConfig(
            name="start",
            label="Start",
            icon="$(play)",
            from_status="open",
            from_stage="draft",
            to_status="open",
            to_stage="doing",
            command_template="monoco issue start {id}",
            description="Start working on the issue"
        ),
        


        TransitionConfig(
            name="stop",
            label="Stop",
            icon="$(stop)",
            from_status="open",
            from_stage="doing",
            to_status="open",
            to_stage="draft",
            command_template="monoco issue stop {id}",
            description="Stop working and return to draft"
        ),
        TransitionConfig(
            name="submit",
            label="Submit",
            icon="$(check)",
            from_status="open",
            from_stage="doing",
            to_status="open",
            to_stage="review",
            command_template="monoco issue submit {id}",
            description="Submit for review"
        ),
        TransitionConfig(
            name="reject",
            label="Reject",
            icon="$(error)",
            from_status="open",
            from_stage="review",
            to_status="open",
            to_stage="doing",
            command_template="monoco issue update {id} --stage doing",
            description="Reject review and return to doing"
        ),

        # --- OPEN -> CLOSED Transitions ---
        TransitionConfig(
            name="accept",
            label="Accept",
            icon="$(pass-filled)",
            from_status="open",
            from_stage="review",
            to_status="closed",
            to_stage="done",
            required_solution="implemented",
            command_template="monoco issue close {id} --solution implemented",
            description="Accept and close issue"
        ),
        TransitionConfig(
            name="close_done",
            label="Close",
            icon="$(close)",
            from_status="open",
            from_stage="done",
            to_status="closed",
            to_stage="done",
            required_solution="implemented",
            command_template="monoco issue close {id} --solution implemented",
            description="Close completed issue"
        ),
        TransitionConfig(
            name="cancel",
            label="Cancel",
            icon="$(trash)",
            from_status="open",
            # Allowed from any stage except DONE (though core.py had a check for it)
            to_status="closed",
            to_stage="done",
            required_solution="cancelled",
            command_template="monoco issue cancel {id}",
            description="Cancel the issue"
        ),
        TransitionConfig(
            name="wontfix",
            label="Won't Fix",
            icon="$(circle-slash)",
            from_status="open",
            to_status="closed",
            to_stage="done",
            required_solution="wontfix",
            command_template="monoco issue close {id} --solution wontfix",
            description="Mark as won't fix"
        ),

        # --- BACKLOG Transitions ---
        TransitionConfig(
            name="push",
            label="Push to Backlog",
            icon="$(archive)",
            from_status="open",
            to_status="backlog",
            to_stage="freezed",
            command_template="monoco issue backlog push {id}",
            description="Move issue to backlog"
        ),

        TransitionConfig(
            name="pull",
            label="Pull",
            icon="$(arrow-up)",
            from_status="backlog",
            to_status="open",
            to_stage="draft",
            command_template="monoco issue backlog pull {id}",
            description="Restore issue from backlog"
        ),
        TransitionConfig(
            name="cancel_backlog",
            label="Cancel",
            icon="$(trash)",
            from_status="backlog",
            to_status="closed",
            to_stage="done",
            required_solution="cancelled",
            command_template="monoco issue cancel {id}",
            description="Cancel backlog issue"
        ),

        # --- CLOSED Transitions ---
        TransitionConfig(
            name="reopen",
            label="Reopen",
            icon="$(refresh)",
            from_status="closed",
            to_status="open",
            to_stage="draft",
            command_template="monoco issue open {id}",
            description="Reopen a closed issue"
        ),
        TransitionConfig(
            name="reopen_from_done",
            label="Reopen",
            icon="$(refresh)",
            from_status="open",
            from_stage="done",
            to_status="open",
            to_stage="draft",
            command_template="monoco issue open {id}",
            description="Reopen a done issue"
        ),
    ]
)
