import pytest
from monoco.features.issue.engine import get_engine
from monoco.features.issue.models import (
    IssueStatus,
    IssueStage,
    IssueMetadata,
    IssueSolution,
)


def test_engine_available_transitions():
    engine = get_engine()

    # Test DRAFT issue
    draft_meta = IssueMetadata(
        id="FEAT-0001",
        uid="123",
        type="feature",
        title="Test",
        status=IssueStatus.OPEN,
        stage=IssueStage.DRAFT,
        parent="EPIC-0000",
    )
    transitions = engine.get_available_transitions(draft_meta)
    transition_names = [t.name for t in transitions]

    assert "start" in transition_names

    assert "cancel" in transition_names
    assert "submit" not in transition_names

    # Test DOING issue
    doing_meta = IssueMetadata(
        id="FEAT-0001",
        uid="123",
        type="feature",
        title="Test",
        status=IssueStatus.OPEN,
        stage=IssueStage.DOING,
        parent="EPIC-0000",
    )
    transitions = engine.get_available_transitions(doing_meta)
    transition_names = [t.name for t in transitions]

    assert "submit" in transition_names

    assert "start" not in transition_names

    # Test BACKLOG issue
    backlog_meta = IssueMetadata(
        id="FEAT-0001",
        uid="123",
        type="feature",
        title="Test",
        status=IssueStatus.BACKLOG,
        stage=IssueStage.FREEZED,
        parent="EPIC-0000",
    )
    transitions = engine.get_available_transitions(backlog_meta)
    transition_names = [t.name for t in transitions]

    assert "pull" in transition_names
    assert "cancel_backlog" in transition_names
    assert "start" not in transition_names


def test_engine_validation():
    engine = get_engine()

    # Valid transition: DRAFT -> DOING
    engine.validate_transition(
        from_status=IssueStatus.OPEN,
        from_stage=IssueStage.DRAFT,
        to_status=IssueStatus.OPEN,
        to_stage=IssueStage.DOING,
    )

    # Invalid transition: BACKLOG -> REVIEW
    with pytest.raises(
        ValueError, match="Lifecycle Policy: Transition .* is not defined"
    ):
        engine.validate_transition(
            from_status=IssueStatus.BACKLOG,
            from_stage=IssueStage.FREEZED,
            to_status=IssueStatus.OPEN,
            to_stage=IssueStage.REVIEW,
        )

    # Solution check: DUPLICATE matches nothing in config
    with pytest.raises(ValueError, match="is not defined"):
        engine.validate_transition(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.REVIEW,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            solution=IssueSolution.DUPLICATE,
        )

    # Solution mismatch: 'accept' transition requires IMPLEMENTED
    # If we pass WONTFIX from REVIEW, it should find 'wontfix' transition and be valid.
    # So we need to test a case where we explicitly want a specific transition but pass wrong solution.
    # Actually, validate_transition finds the BEST transition.
    # If we pass IMPLEMENTED but we are in DOING, it should fail.
    with pytest.raises(ValueError, match="is not defined"):
        engine.validate_transition(
            from_status=IssueStatus.OPEN,
            from_stage=IssueStage.DOING,
            to_status=IssueStatus.CLOSED,
            to_stage=IssueStage.DONE,
            solution=IssueSolution.IMPLEMENTED,
        )


def test_engine_enforce_policy():
    engine = get_engine()

    # Test Closed without Done
    meta = IssueMetadata(
        id="FEAT-0001",
        uid="123",
        type="feature",
        title="Test",
        status=IssueStatus.CLOSED,
        stage=IssueStage.DOING,
        parent="EPIC-0000",
        solution=IssueSolution.IMPLEMENTED,
    )
    engine.enforce_policy(meta)
    assert meta.stage == IssueStage.DONE
    assert meta.closed_at is not None

    # Test Backlog without Freezed
    meta = IssueMetadata(
        id="FEAT-0001",
        uid="123",
        type="feature",
        title="Test",
        status=IssueStatus.BACKLOG,
        stage=IssueStage.DRAFT,
        parent="EPIC-0000",
    )
    engine.enforce_policy(meta)
    assert meta.stage == IssueStage.FREEZED
