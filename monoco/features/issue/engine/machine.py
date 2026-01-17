from typing import List, Optional
from .models import StateMachineConfig, Transition
from ..models import IssueStatus, IssueStage, IssueMetadata, IssueSolution

class StateMachine:
    def __init__(self, config: StateMachineConfig):
        self.config = config

    def can_transition(self, current_status: IssueStatus, current_stage: Optional[IssueStage], 
                       target_status: IssueStatus, target_stage: Optional[IssueStage]) -> bool:
        """Check if a transition path exists."""
        for t in self.config.transitions:
            if t.from_status and t.from_status != current_status:
                continue
            if t.from_stage and t.from_stage != current_stage:
                continue
            
            if t.to_status == target_status:
                if target_stage is None or t.to_stage == target_stage:
                    return True
        return False

    def get_available_transitions(self, meta: IssueMetadata) -> List[Transition]:
        """Get all transitions allowed from the current state of the issue."""
        allowed = []
        for t in self.config.transitions:
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
            if t.name == "cancel" and meta.stage == IssueStage.DONE:
                continue

            allowed.append(t)
        return allowed

    def find_transition(self, from_status: IssueStatus, from_stage: Optional[IssueStage],
                        to_status: IssueStatus, to_stage: Optional[IssueStage],
                        solution: Optional[IssueSolution] = None) -> Optional[Transition]:
        """Find a specific transition rule."""
        candidates = []
        for t in self.config.transitions:
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

    def validate_transition(self, from_status: IssueStatus, from_stage: Optional[IssueStage],
                            to_status: IssueStatus, to_stage: Optional[IssueStage],
                            solution: Optional[IssueSolution] = None) -> None:
        """
        Validate if a transition is allowed. Raises ValueError if not.
        """
        if from_status == to_status and from_stage == to_stage:
            return # No change is always allowed (unless we want to enforce specific updates)

        transition = self.find_transition(from_status, from_stage, to_status, to_stage, solution)
        
        if not transition:
            raise ValueError(f"Lifecycle Policy: Transition from {from_status.value}({from_stage.value if from_stage else 'None'}) "
                             f"to {to_status.value}({to_stage.value if to_stage else 'None'}) is not defined.")

        if transition.required_solution and solution != transition.required_solution:
             raise ValueError(f"Lifecycle Policy: Transition '{transition.label}' requires solution '{transition.required_solution.value}'.")

    def enforce_policy(self, meta: IssueMetadata) -> None:
        """
        Apply consistency rules to IssueMetadata.
        """
        from ..models import current_time
        
        if meta.status == IssueStatus.BACKLOG:
            meta.stage = IssueStage.FREEZED
        
        elif meta.status == IssueStatus.CLOSED:
            if meta.stage != IssueStage.DONE:
                meta.stage = IssueStage.DONE
            if not meta.closed_at:
                meta.closed_at = current_time()
        
        elif meta.status == IssueStatus.OPEN:
            if meta.stage is None:
                meta.stage = IssueStage.DRAFT