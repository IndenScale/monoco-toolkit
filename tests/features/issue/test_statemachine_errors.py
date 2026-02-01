"""Tests for StateMachine error messages."""

import pytest
from monoco.features.issue.engine import get_engine
from monoco.features.issue.models import (
    IssueStatus,
    IssueStage,
    IssueMetadata,
    IssueSolution,
)


class TestTransitionNotFoundErrors:
    """Tests for error messages when transition is not found."""

    def test_error_includes_current_and_target_state(self):
        """Error message should clearly state current and target states."""
        engine = get_engine()

        with pytest.raises(ValueError) as exc_info:
            engine.validate_transition(
                from_status=IssueStatus.BACKLOG,
                from_stage=IssueStage.FREEZED,
                to_status=IssueStatus.OPEN,
                to_stage=IssueStage.REVIEW,
            )

        error_msg = str(exc_info.value)
        assert "backlog(freezed)" in error_msg
        assert "open(review)" in error_msg
        assert "is not defined" in error_msg

    def test_error_includes_available_transitions(self):
        """Error message should list available transitions from current state."""
        engine = get_engine()

        with pytest.raises(ValueError) as exc_info:
            engine.validate_transition(
                from_status=IssueStatus.BACKLOG,
                from_stage=IssueStage.FREEZED,
                to_status=IssueStatus.OPEN,
                to_stage=IssueStage.REVIEW,
            )

        error_msg = str(exc_info.value)
        assert "Available transitions from this state:" in error_msg
        # Should include pull and cancel_backlog transitions
        assert "pull:" in error_msg
        assert "cancel_backlog:" in error_msg

    def test_error_shows_transitions_with_required_solutions(self):
        """Error message should show which transitions require solutions."""
        engine = get_engine()

        # Try an invalid transition from DOING to a non-existent state
        with pytest.raises(ValueError) as exc_info:
            engine.validate_transition(
                from_status=IssueStatus.OPEN,
                from_stage=IssueStage.DOING,
                to_status=IssueStatus.CLOSED,
                to_stage=IssueStage.REVIEW,  # Invalid: can't go to closed(review)
            )

        error_msg = str(exc_info.value)
        # Should show available transitions
        assert "Available transitions from this state:" in error_msg
        # cancel and wontfix require solutions
        assert "(requires --solution cancelled)" in error_msg

    def test_error_when_no_transitions_available(self):
        """Error message should indicate when no transitions are available."""
        engine = get_engine()

        # Try an invalid state combination that has no outgoing transitions
        # Using a fake status that doesn't exist
        with pytest.raises(ValueError) as exc_info:
            engine.validate_transition(
                from_status="nonexistent",
                from_stage="nonexistent",
                to_status=IssueStatus.BACKLOG,
                to_stage=IssueStage.FREEZED,
            )

        error_msg = str(exc_info.value)
        assert "No transitions are available from this state" in error_msg


class TestInvalidSolutionErrors:
    """Tests for error messages when solution is invalid or missing."""

    def test_error_when_solution_required_but_missing(self):
        """Error message should indicate when solution is required but not provided."""
        engine = get_engine()

        # Try to close from review without a solution
        with pytest.raises(ValueError) as exc_info:
            engine.validate_transition(
                from_status=IssueStatus.OPEN,
                from_stage=IssueStage.REVIEW,
                to_status=IssueStatus.CLOSED,
                to_stage=IssueStage.DONE,
                solution=None,
            )

        error_msg = str(exc_info.value)
        assert "requires a solution" in error_msg
        assert "Valid solutions are:" in error_msg

    def test_error_includes_valid_solutions(self):
        """Error message should list all valid solutions for the transition."""
        engine = get_engine()

        with pytest.raises(ValueError) as exc_info:
            engine.validate_transition(
                from_status=IssueStatus.OPEN,
                from_stage=IssueStage.REVIEW,
                to_status=IssueStatus.CLOSED,
                to_stage=IssueStage.DONE,
                solution=None,  # Missing solution
            )

        error_msg = str(exc_info.value)
        # Should list valid solutions from review state
        assert "implemented" in error_msg
        assert "cancelled" in error_msg
        assert "wontfix" in error_msg

    def test_valid_solution_works(self):
        """Valid solution should allow transition without error."""
        engine = get_engine()

        # This should not raise
        transition = engine.validate_transition(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.REVIEW,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            solution=IssueSolution.IMPLEMENTED,
        )

        assert transition is not None
        assert transition.name == "accept"

    def test_cancel_solution_finds_cancel_transition(self):
        """Cancelled solution should find the cancel transition."""
        engine = get_engine()

        transition = engine.validate_transition(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.REVIEW,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            solution=IssueSolution.CANCELLED,
        )

        assert transition is not None
        assert transition.name == "cancel"


class TestErrorMessageFormat:
    """Tests for error message format consistency."""

    def test_all_errors_start_with_lifecycle_policy(self):
        """All error messages should start with 'Lifecycle Policy:'."""
        engine = get_engine()

        # Test transition not found
        with pytest.raises(ValueError) as exc_info:
            engine.validate_transition(
                from_status=IssueStatus.BACKLOG,
                from_stage=IssueStage.FREEZED,
                to_status=IssueStatus.OPEN,
                to_stage=IssueStage.REVIEW,
            )
        assert str(exc_info.value).startswith("Lifecycle Policy:")

        # Test missing solution
        with pytest.raises(ValueError) as exc_info:
            engine.validate_transition(
                from_status=IssueStatus.OPEN,
                from_stage=IssueStage.REVIEW,
                to_status=IssueStatus.CLOSED,
                to_stage=IssueStage.DONE,
                solution=None,
            )
        assert str(exc_info.value).startswith("Lifecycle Policy:")

    def test_error_includes_state_context(self):
        """Error messages should include context about current state."""
        engine = get_engine()

        with pytest.raises(ValueError) as exc_info:
            engine.validate_transition(
                from_status=IssueStatus.OPEN,
                from_stage=IssueStage.DRAFT,
                to_status=IssueStatus.CLOSED,
                to_stage=IssueStage.DONE,
                solution=None,  # Missing solution to trigger error
            )

        error_msg = str(exc_info.value)
        # Should mention the current state
        assert "open(draft)" in error_msg.lower() or "draft" in error_msg.lower()


class TestHelperMethods:
    """Tests for helper methods used in error generation."""

    def test_get_available_solutions(self):
        """Test getting valid solutions for a state."""
        engine = get_engine()

        # From review state, we can use implemented, cancelled, or wontfix
        solutions = engine.get_available_solutions(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.REVIEW,
        )

        assert "implemented" in solutions
        assert "cancelled" in solutions
        assert "wontfix" in solutions

    def test_get_valid_transitions_from_state(self):
        """Test getting valid transitions from a state."""
        engine = get_engine()

        transitions = engine.get_valid_transitions_from_state(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DRAFT,
        )

        transition_names = [t.name for t in transitions]
        assert "start" in transition_names
        assert "push" in transition_names
        assert "cancel" in transition_names

    def test_format_state_with_stage(self):
        """Test formatting state with both status and stage."""
        engine = get_engine()

        formatted = engine._format_state("open", "draft")
        assert formatted == "open(draft)"

    def test_format_state_without_stage(self):
        """Test formatting state with only status."""
        engine = get_engine()

        formatted = engine._format_state("closed", None)
        assert formatted == "closed"


class TestEdgeCases:
    """Tests for edge cases in error handling."""

    def test_no_change_is_allowed(self):
        """Transition to same state should return None (no error)."""
        engine = get_engine()

        result = engine.validate_transition(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DRAFT,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.DRAFT,
        )

        assert result is None

    def test_cancel_from_any_open_stage(self):
        """Cancel should work from any open stage."""
        engine = get_engine()

        # From draft
        transition = engine.validate_transition(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DRAFT,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            solution=IssueSolution.CANCELLED,
        )
        assert transition is not None
        assert transition.name == "cancel"

        # From doing
        transition = engine.validate_transition(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DOING,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            solution=IssueSolution.CANCELLED,
        )
        assert transition is not None
        assert transition.name == "cancel"

    def test_backlog_to_draft_pull(self):
        """Pull transition should work from backlog to draft."""
        engine = get_engine()

        transition = engine.validate_transition(
            from_status=IssueStatus.BACKLOG,
            from_stage=IssueStage.FREEZED,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.DRAFT,
        )

        assert transition is not None
        assert transition.name == "pull"

    def test_wontfix_from_any_open_stage(self):
        """Wontfix should work from any open stage."""
        engine = get_engine()

        # From draft
        transition = engine.validate_transition(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DRAFT,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            solution=IssueSolution.WONTFIX,
        )
        assert transition is not None
        assert transition.name == "wontfix"

        # From doing
        transition = engine.validate_transition(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DOING,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            solution=IssueSolution.WONTFIX,
        )
        assert transition is not None
        assert transition.name == "wontfix"
