from typing import List, Optional, Dict
from monoco.core.config import IssueSchemaConfig, TransitionConfig
from ..models import IssueMetadata


class StateMachine:
    def __init__(self, config: IssueSchemaConfig):
        self.issue_config = config
        self.transitions = config.workflows or []

    def get_type_config(self, type_name: str):
        if not self.issue_config.types:
            return None
        for t in self.issue_config.types:
            if t.name == type_name:
                return t
        return None

    def get_prefix_map(self) -> Dict[str, str]:
        if not self.issue_config.types:
            return {}
        return {t.name: t.prefix for t in self.issue_config.types}

    def get_folder_map(self) -> Dict[str, str]:
        if not self.issue_config.types:
            return {}
        return {t.name: t.folder for t in self.issue_config.types}

    def get_all_types(self) -> List[str]:
        if not self.issue_config.types:
            return []
        return [t.name for t in self.issue_config.types]

    def can_transition(
        self,
        current_status: str,
        current_stage: Optional[str],
        target_status: str,
        target_stage: Optional[str],
    ) -> bool:
        """Check if a transition path exists."""
        for t in self.transitions:
            if t.from_status and t.from_status != current_status:
                continue
            if t.from_stage and t.from_stage != current_stage:
                continue

            if t.to_status == target_status:
                if target_stage is None or t.to_stage == target_stage:
                    return True
        return False

    def get_available_transitions(self, meta: IssueMetadata) -> List[TransitionConfig]:
        """Get all transitions allowed from the current state of the issue."""
        allowed = []
        for t in self.transitions:
            # Universal actions (no from_status/stage) are always allowed
            if t.from_status is None and t.from_stage is None:
                allowed.append(t)
                continue

            # Match status
            if t.from_status and t.from_status != meta.status:
                continue

            # Match stage
            if t.from_stage and t.from_stage != meta.stage:
                continue

            # Special case for 'Cancel': don't show if already DONE or CLOSED
            if t.name == "cancel" and meta.stage == "done":
                continue

            allowed.append(t)
        return allowed

    def find_transition(
        self,
        from_status: str,
        from_stage: Optional[str],
        to_status: str,
        to_stage: Optional[str],
        solution: Optional[str] = None,
    ) -> Optional[TransitionConfig]:
        """Find a specific transition rule."""
        candidates = []
        for t in self.transitions:
            # Skip non-transitions (agent actions with same status/stage)
            if t.from_status is None and t.from_stage is None:
                continue

            if t.from_status and t.from_status != from_status:
                continue
            if t.from_stage and t.from_stage != from_stage:
                continue

            # Check if this transition matches the target
            if t.to_status == to_status:
                if to_stage is None or t.to_stage == to_stage:
                    candidates.append(t)

        if not candidates:
            return None

        # If we have a solution, find the transition that requires it
        if solution:
            for t in candidates:
                if t.required_solution == solution:
                    return t
            # If solution provided but none of the transitions match it,
            # we should return None (unless there is a transition with NO required_solution)
            for t in candidates:
                if t.required_solution is None:
                    return t
            return None

        # Otherwise return the first one that has NO required_solution
        for t in candidates:
            if t.required_solution is None:
                return t

        return candidates[0]

    def validate_transition(
        self,
        from_status: str,
        from_stage: Optional[str],
        to_status: str,
        to_stage: Optional[str],
        solution: Optional[str] = None,
    ) -> None:
        """
        Validate if a transition is allowed. Raises ValueError if not.
        """
        if from_status == to_status and from_stage == to_stage:
            return  # No change is always allowed (unless we want to enforce specific updates)

        transition = self.find_transition(
            from_status, from_stage, to_status, to_stage, solution
        )

        if not transition:
            raise ValueError(
                f"Lifecycle Policy: Transition from {from_status}({from_stage if from_stage else 'None'}) "
                f"to {to_status}({to_stage if to_stage else 'None'}) is not defined."
            )

        if transition.required_solution and solution != transition.required_solution:
            raise ValueError(
                f"Lifecycle Policy: Transition '{transition.label}' requires solution '{transition.required_solution}'."
            )

    def enforce_policy(self, meta: IssueMetadata) -> None:
        """
        Apply consistency rules to IssueMetadata.
        """
        from ..models import current_time

        if meta.status == "backlog":
            meta.stage = "freezed"

        elif meta.status == "closed":
            if meta.stage != "done":
                meta.stage = "done"
            if not meta.closed_at:
                meta.closed_at = current_time()

        elif meta.status == "open":
            if meta.stage is None:
                meta.stage = "draft"

    def enforce_policy(self, meta: IssueMetadata) -> None:
        """
        Apply consistency rules to IssueMetadata.
        """
        from ..models import current_time

        if meta.status == "backlog":
            meta.stage = "freezed"

        elif meta.status == "closed":
            if meta.stage != "done":
                meta.stage = "done"
            if not meta.closed_at:
                meta.closed_at = current_time()

        elif meta.status == "open":
            if meta.stage is None:
                meta.stage = "draft"
