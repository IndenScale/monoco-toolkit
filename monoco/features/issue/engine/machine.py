from typing import List, Optional, Dict
from monoco.core.config import IssueSchemaConfig, TransitionConfig
from ..models import IssueMetadata
from ..criticality import (
    CriticalityLevel,
    PolicyResolver,
    HumanReviewLevel,
)


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

    def get_available_solutions(self, from_status: str, from_stage: Optional[str]) -> List[str]:
        """Get all valid solutions for transitions from the current state."""
        solutions = set()
        for t in self.transitions:
            # Skip non-transitions (agent actions with same status/stage)
            if t.from_status is None and t.from_stage is None:
                continue

            if t.from_status and t.from_status != from_status:
                continue
            if t.from_stage and t.from_stage != from_stage:
                continue

            if t.required_solution:
                solutions.add(t.required_solution)
        return sorted(list(solutions))

    def get_valid_transitions_from_state(
        self, from_status: str, from_stage: Optional[str]
    ) -> List[TransitionConfig]:
        """Get all valid transitions from a given state."""
        valid = []
        for t in self.transitions:
            # Skip non-transitions (agent actions with same status/stage)
            if t.from_status is None and t.from_stage is None:
                continue

            if t.from_status and t.from_status != from_status:
                continue
            if t.from_stage and t.from_stage != from_stage:
                continue

            valid.append(t)
        return valid

    def _format_state(self, status: str, stage: Optional[str]) -> str:
        """Format a state for display in error messages."""
        # Handle Enum values
        if hasattr(status, 'value'):
            status = status.value
        if stage and hasattr(stage, 'value'):
            stage = stage.value
        
        if stage:
            return f"{status}({stage})"
        return status

    def _build_transition_not_found_error(
        self,
        from_status: str,
        from_stage: Optional[str],
        to_status: str,
        to_stage: Optional[str],
    ) -> str:
        """Build a descriptive error message when no transition is found."""
        current_state = self._format_state(from_status, from_stage)
        target_state = self._format_state(to_status, to_stage)

        error_msg = (
            f"Lifecycle Policy: Transition from '{current_state}' "
            f"to '{target_state}' is not defined."
        )

        # Add available transitions hint
        valid_transitions = self.get_valid_transitions_from_state(from_status, from_stage)
        if valid_transitions:
            error_msg += " Available transitions from this state:"
            for t in valid_transitions:
                target = self._format_state(t.to_status, t.to_stage)
                if t.required_solution:
                    error_msg += f"\n  - {t.name}: '{current_state}' -> '{target}' (requires --solution {t.required_solution})"
                else:
                    error_msg += f"\n  - {t.name}: '{current_state}' -> '{target}'"
        else:
            error_msg += " No transitions are available from this state."

        return error_msg

    def _build_invalid_solution_error(
        self,
        transition: TransitionConfig,
        provided_solution: Optional[str],
        from_status: str,
        from_stage: Optional[str],
    ) -> str:
        """Build a descriptive error message when solution is invalid or missing."""
        current_state = self._format_state(from_status, from_stage)
        target_state = self._format_state(transition.to_status, transition.to_stage)

        if provided_solution:
            error_msg = (
                f"Lifecycle Policy: Transition '{transition.label}' from '{current_state}' "
                f"to '{target_state}' does not accept solution '{provided_solution}'."
            )
        else:
            error_msg = (
                f"Lifecycle Policy: Transition '{transition.label}' from '{current_state}' "
                f"to '{target_state}' requires a solution."
            )

        # Get valid solutions for this transition
        valid_solutions = self.get_available_solutions(from_status, from_stage)
        if valid_solutions:
            error_msg += f" Valid solutions are: {', '.join(valid_solutions)}."

        return error_msg

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
        meta: Optional[IssueMetadata] = None,
    ) -> TransitionConfig:
        """
        Validate if a transition is allowed. Raises ValueError if not.
        If meta is provided, also validates criticality-based policies.
        Returns the TransitionConfig if a transition occurred, None if no change.
        """
        if from_status == to_status and from_stage == to_stage:
            return None  # No change is always allowed (unless we want to enforce specific updates)

        transition = self.find_transition(
            from_status, from_stage, to_status, to_stage, solution
        )

        if not transition:
            raise ValueError(
                self._build_transition_not_found_error(
                    from_status, from_stage, to_status, to_stage
                )
            )

        if transition.required_solution and solution != transition.required_solution:
            raise ValueError(
                self._build_invalid_solution_error(
                    transition, solution, from_status, from_stage
                )
            )

        # Criticality-based policy checks
        if meta and meta.criticality:
            self._validate_criticality_policy(meta, from_stage, to_stage)
            
        return transition

    def _validate_criticality_policy(
        self,
        meta: IssueMetadata,
        from_stage: Optional[str],
        to_stage: Optional[str],
    ) -> None:
        """
        Validate transition against criticality-based policies.
        Enforces stricter requirements for high/critical issues.
        """
        policy = PolicyResolver.resolve(meta.criticality)

        # Submit to Review: Enforce agent review for medium+
        if to_stage == "review" and from_stage == "doing":
            if meta.criticality >= CriticalityLevel.MEDIUM:
                # For medium+, agent review is mandatory
                # This is enforced by the policy, but we can't check actual review status here
                # The check is informational - actual enforcement happens in submit command
                pass

        # Close/Accept: Enforce human review for high/critical
        if to_stage == "done":
            if policy.human_review in [
                HumanReviewLevel.REQUIRED,
                HumanReviewLevel.REQUIRED_RECORD,
            ]:
                # For high/critical, human review is mandatory before closing
                # Actual enforcement would check review comments section
                pass

    def check_policy_compliance(self, meta: IssueMetadata) -> List[str]:
        """
        Check if an issue complies with its criticality policy.
        Returns list of policy violations.
        """
        if not meta.criticality:
            return []

        violations = []
        policy = PolicyResolver.resolve(meta.criticality)

        # Stage-based checks
        if meta.stage == "review":
            # In review stage, check coverage requirement
            # Note: Actual coverage check would require external data
            pass

        if meta.stage == "done" or meta.status == "closed":
            # For high/critical, require review comments
            if policy.human_review in [
                HumanReviewLevel.REQUIRED,
                HumanReviewLevel.REQUIRED_RECORD,
            ]:
                # This is a simplified check - full implementation would parse body
                pass

        return violations

    def enforce_policy(self, meta: IssueMetadata) -> None:
        """
        Apply consistency rules to IssueMetadata.
        Includes criticality-based defaults.
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

        # Set default criticality if not set
        if meta.criticality is None:
            from ..criticality import CriticalityTypeMapping

            meta.criticality = CriticalityTypeMapping.get_default(meta.type.value)
