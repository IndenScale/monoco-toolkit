"""
Unit tests for Issue Criticality System (FEAT-0114).

Tests cover:
- CriticalityLevel enum and comparisons
- Policy resolution from criticality levels
- Criticality inheritance rules
- Auto-escalation detection
- Escalation approval workflow
- Policy validation and compliance
"""

import pytest

from monoco.features.issue.criticality import (
    CriticalityLevel,
    AgentReviewLevel,
    HumanReviewLevel,
    RollbackAction,
    Policy,
    PolicyResolver,
    CriticalityInheritanceService,
    AutoEscalationDetector,
    AutoEscalationRule,
    EscalationApprovalWorkflow,
    EscalationRequest,
    EscalationStatus,
    CriticalityTypeMapping,
    CriticalityValidator,
)


class TestCriticalityLevel:
    """Tests for CriticalityLevel enum."""

    def test_from_string_valid(self):
        """Test parsing valid criticality strings."""
        assert CriticalityLevel.from_string("low") == CriticalityLevel.LOW
        assert CriticalityLevel.from_string("MEDIUM") == CriticalityLevel.MEDIUM
        assert CriticalityLevel.from_string("High") == CriticalityLevel.HIGH
        assert CriticalityLevel.from_string("CRITICAL") == CriticalityLevel.CRITICAL

    def test_from_string_invalid_defaults_to_medium(self):
        """Test that invalid strings default to MEDIUM."""
        assert CriticalityLevel.from_string("invalid") == CriticalityLevel.MEDIUM
        assert CriticalityLevel.from_string("") == CriticalityLevel.MEDIUM

    def test_numeric_values(self):
        """Test numeric ordering of criticality levels."""
        assert CriticalityLevel.LOW.numeric_value == 1
        assert CriticalityLevel.MEDIUM.numeric_value == 2
        assert CriticalityLevel.HIGH.numeric_value == 3
        assert CriticalityLevel.CRITICAL.numeric_value == 4

    def test_comparison_operators(self):
        """Test comparison operators between levels."""
        assert CriticalityLevel.LOW < CriticalityLevel.MEDIUM
        assert CriticalityLevel.MEDIUM < CriticalityLevel.HIGH
        assert CriticalityLevel.HIGH < CriticalityLevel.CRITICAL

        assert CriticalityLevel.CRITICAL > CriticalityLevel.HIGH
        assert CriticalityLevel.HIGH >= CriticalityLevel.HIGH
        assert CriticalityLevel.LOW <= CriticalityLevel.MEDIUM


class TestPolicy:
    """Tests for Policy model."""

    def test_policy_defaults(self):
        """Test default policy values."""
        policy = Policy()
        assert policy.agent_review == AgentReviewLevel.STANDARD
        assert policy.human_review == HumanReviewLevel.RECOMMENDED
        assert policy.min_coverage == 70
        assert policy.rollback_on_failure == RollbackAction.ROLLBACK
        assert policy.require_security_scan is False
        assert policy.require_performance_check is False
        assert policy.max_reviewers == 1

    def test_policy_immutability(self):
        """Test that policies are frozen/immutable."""
        policy = Policy()
        with pytest.raises(Exception):  # pydantic frozen error
            policy.min_coverage = 80


class TestPolicyResolver:
    """Tests for PolicyResolver."""

    def test_resolve_low(self):
        """Test policy resolution for LOW criticality."""
        policy = PolicyResolver.resolve(CriticalityLevel.LOW)
        assert policy.agent_review == AgentReviewLevel.LIGHTWEIGHT
        assert policy.human_review == HumanReviewLevel.OPTIONAL
        assert policy.min_coverage == 0
        assert policy.rollback_on_failure == RollbackAction.WARN
        assert policy.require_security_scan is False

    def test_resolve_medium(self):
        """Test policy resolution for MEDIUM criticality."""
        policy = PolicyResolver.resolve(CriticalityLevel.MEDIUM)
        assert policy.agent_review == AgentReviewLevel.STANDARD
        assert policy.human_review == HumanReviewLevel.RECOMMENDED
        assert policy.min_coverage == 70
        assert policy.rollback_on_failure == RollbackAction.ROLLBACK

    def test_resolve_high(self):
        """Test policy resolution for HIGH criticality."""
        policy = PolicyResolver.resolve(CriticalityLevel.HIGH)
        assert policy.agent_review == AgentReviewLevel.STRICT
        assert policy.human_review == HumanReviewLevel.REQUIRED
        assert policy.min_coverage == 85
        assert policy.rollback_on_failure == RollbackAction.BLOCK
        assert policy.require_security_scan is True

    def test_resolve_critical(self):
        """Test policy resolution for CRITICAL criticality."""
        policy = PolicyResolver.resolve(CriticalityLevel.CRITICAL)
        assert policy.agent_review == AgentReviewLevel.STRICT_AUDIT
        assert policy.human_review == HumanReviewLevel.REQUIRED_RECORD
        assert policy.min_coverage == 90
        assert policy.rollback_on_failure == RollbackAction.BLOCK_NOTIFY
        assert policy.require_security_scan is True
        assert policy.require_performance_check is True
        assert policy.max_reviewers == 3

    def test_get_all_policies(self):
        """Test getting all defined policies."""
        policies = PolicyResolver.get_all_policies()
        assert len(policies) == 4
        assert CriticalityLevel.LOW in policies
        assert CriticalityLevel.CRITICAL in policies


class TestCriticalityInheritanceService:
    """Tests for CriticalityInheritanceService."""

    def test_resolve_child_no_parent(self):
        """Test child resolution when no parent exists."""
        result = CriticalityInheritanceService.resolve_child_criticality(
            None, CriticalityLevel.MEDIUM
        )
        assert result == CriticalityLevel.MEDIUM

    def test_resolve_child_inherits_parent_minimum(self):
        """Test that child inherits at least parent's criticality."""
        # Parent is HIGH, child proposed LOW -> should be HIGH
        result = CriticalityInheritanceService.resolve_child_criticality(
            CriticalityLevel.HIGH, CriticalityLevel.LOW
        )
        assert result == CriticalityLevel.HIGH

    def test_resolve_child_can_be_higher(self):
        """Test that child can have higher criticality than parent."""
        # Parent is MEDIUM, child proposed CRITICAL -> should be CRITICAL
        result = CriticalityInheritanceService.resolve_child_criticality(
            CriticalityLevel.MEDIUM, CriticalityLevel.CRITICAL
        )
        assert result == CriticalityLevel.CRITICAL

    def test_resolve_child_same_as_parent(self):
        """Test when child proposed level equals parent."""
        result = CriticalityInheritanceService.resolve_child_criticality(
            CriticalityLevel.HIGH, CriticalityLevel.HIGH
        )
        assert result == CriticalityLevel.HIGH

    def test_can_lower_child_criticality(self):
        """Test checking if child criticality can be lowered."""
        # Child HIGH, Parent MEDIUM -> can lower (still >= parent)
        assert (
            CriticalityInheritanceService.can_lower_child_criticality(
                CriticalityLevel.HIGH, CriticalityLevel.MEDIUM
            )
            is True
        )

        # Child MEDIUM, Parent MEDIUM -> cannot lower
        assert (
            CriticalityInheritanceService.can_lower_child_criticality(
                CriticalityLevel.MEDIUM, CriticalityLevel.MEDIUM
            )
            is False
        )


class TestAutoEscalationDetector:
    """Tests for AutoEscalationDetector."""

    def test_no_escalation_needed(self):
        """Test when no escalation rules match."""
        detector = AutoEscalationDetector()
        result = detector.detect_escalation(
            current_level=CriticalityLevel.LOW,
            file_paths=["src/utils.py"],
            tags=["refactor"],
        )
        assert result is None

    def test_escalation_by_path_pattern(self):
        """Test escalation triggered by file path pattern."""
        detector = AutoEscalationDetector()
        result = detector.detect_escalation(
            current_level=CriticalityLevel.LOW,
            file_paths=["src/payment/gateway.py"],
            tags=[],
        )
        assert result == CriticalityLevel.CRITICAL

    def test_escalation_by_tag(self):
        """Test escalation triggered by tag."""
        detector = AutoEscalationDetector()
        result = detector.detect_escalation(
            current_level=CriticalityLevel.LOW,
            file_paths=[],
            tags=["security", "authentication"],
        )
        assert result == CriticalityLevel.HIGH

    def test_escalation_to_highest_match(self):
        """Test that highest matching level is returned."""
        detector = AutoEscalationDetector()
        # Both payment (CRITICAL) and security (HIGH) match
        result = detector.detect_escalation(
            current_level=CriticalityLevel.LOW,
            file_paths=["src/payment/auth.py"],
            tags=["security"],
        )
        assert result == CriticalityLevel.CRITICAL

    def test_no_escalation_when_already_high(self):
        """Test no escalation when current level is already higher."""
        detector = AutoEscalationDetector()
        result = detector.detect_escalation(
            current_level=CriticalityLevel.CRITICAL,
            file_paths=["src/payment/gateway.py"],
            tags=[],
        )
        assert result is None

    def test_custom_rules(self):
        """Test using custom escalation rules."""
        custom_rules = [
            AutoEscalationRule(
                name="custom_rule",
                description="Test rule",
                path_patterns=["**/custom/**"],
                tag_patterns=["custom-tag"],
                target_level=CriticalityLevel.HIGH,
            )
        ]
        detector = AutoEscalationDetector(custom_rules)
        result = detector.detect_escalation(
            current_level=CriticalityLevel.LOW,
            file_paths=["src/custom/module.py"],
            tags=[],
        )
        assert result == CriticalityLevel.HIGH


class TestEscalationRequest:
    """Tests for EscalationRequest model."""

    def test_valid_escalation_request(self):
        """Test creating a valid escalation request."""
        request = EscalationRequest(
            id="ESC-1234",
            issue_id="FEAT-0001",
            from_level=CriticalityLevel.MEDIUM,
            to_level=CriticalityLevel.HIGH,
            reason="Security impact identified",
            requested_by="user@example.com",
        )
        assert request.status == EscalationStatus.PENDING
        assert request.approved_by is None

    def test_invalid_escalation_direction(self):
        """Test that downward escalation is rejected."""
        with pytest.raises(ValueError) as exc_info:
            EscalationRequest(
                id="ESC-1234",
                issue_id="FEAT-0001",
                from_level=CriticalityLevel.HIGH,
                to_level=CriticalityLevel.LOW,
                reason="Trying to lower",
                requested_by="user@example.com",
            )
        assert "higher level" in str(exc_info.value)

    def test_same_level_escalation_rejected(self):
        """Test that same-level escalation is rejected."""
        with pytest.raises(ValueError):
            EscalationRequest(
                id="ESC-1234",
                issue_id="FEAT-0001",
                from_level=CriticalityLevel.MEDIUM,
                to_level=CriticalityLevel.MEDIUM,
                reason="No change",
                requested_by="user@example.com",
            )


class TestEscalationApprovalWorkflow:
    """Tests for EscalationApprovalWorkflow."""

    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create a temporary storage file."""
        return tmp_path / "escalations.yaml"

    def test_create_request(self, temp_storage):
        """Test creating an escalation request."""
        workflow = EscalationApprovalWorkflow(temp_storage)
        request = workflow.create_request(
            issue_id="FEAT-0001",
            from_level=CriticalityLevel.MEDIUM,
            to_level=CriticalityLevel.HIGH,
            reason="Security impact",
            requested_by="user1",
        )

        assert request.issue_id == "FEAT-0001"
        assert request.from_level == CriticalityLevel.MEDIUM
        assert request.to_level == CriticalityLevel.HIGH
        assert request.status == EscalationStatus.PENDING
        assert request.id.startswith("ESC-")

    def test_approve_request(self, temp_storage):
        """Test approving an escalation request."""
        workflow = EscalationApprovalWorkflow(temp_storage)
        request = workflow.create_request(
            issue_id="FEAT-0001",
            from_level=CriticalityLevel.LOW,
            to_level=CriticalityLevel.HIGH,
            reason="Important",
            requested_by="user1",
        )

        approved = workflow.approve(request.id, "approver1")
        assert approved.status == EscalationStatus.APPROVED
        assert approved.approved_by == "approver1"
        assert approved.approved_at is not None

    def test_reject_request(self, temp_storage):
        """Test rejecting an escalation request."""
        workflow = EscalationApprovalWorkflow(temp_storage)
        request = workflow.create_request(
            issue_id="FEAT-0001",
            from_level=CriticalityLevel.LOW,
            to_level=CriticalityLevel.CRITICAL,
            reason="Overestimated",
            requested_by="user1",
        )

        rejected = workflow.reject(request.id, "approver1", "Not justified")
        assert rejected.status == EscalationStatus.REJECTED
        assert rejected.rejection_reason == "Not justified"

    def test_approve_nonexistent_request(self, temp_storage):
        """Test approving a non-existent request raises error."""
        workflow = EscalationApprovalWorkflow(temp_storage)
        with pytest.raises(ValueError) as exc_info:
            workflow.approve("ESC-NONEXISTENT", "approver1")
        assert "not found" in str(exc_info.value)

    def test_double_approval_rejected(self, temp_storage):
        """Test that double approval is rejected."""
        workflow = EscalationApprovalWorkflow(temp_storage)
        request = workflow.create_request(
            issue_id="FEAT-0001",
            from_level=CriticalityLevel.LOW,
            to_level=CriticalityLevel.MEDIUM,
            reason="Test",
            requested_by="user1",
        )

        workflow.approve(request.id, "approver1")

        with pytest.raises(ValueError) as exc_info:
            workflow.approve(request.id, "approver2")
        assert "already" in str(exc_info.value)

    def test_get_pending_for_issue(self, temp_storage):
        """Test retrieving pending requests for an issue."""
        workflow = EscalationApprovalWorkflow(temp_storage)

        # Create requests for different issues
        workflow.create_request(
            issue_id="FEAT-0001",
            from_level=CriticalityLevel.LOW,
            to_level=CriticalityLevel.MEDIUM,
            reason="Test1",
            requested_by="user1",
        )
        workflow.create_request(
            issue_id="FEAT-0001",
            from_level=CriticalityLevel.MEDIUM,
            to_level=CriticalityLevel.HIGH,
            reason="Test2",
            requested_by="user1",
        )
        workflow.create_request(
            issue_id="FEAT-0002",
            from_level=CriticalityLevel.LOW,
            to_level=CriticalityLevel.HIGH,
            reason="Other issue",
            requested_by="user1",
        )

        pending = workflow.get_pending_for_issue("FEAT-0001")
        assert len(pending) == 2

    def test_persistence(self, temp_storage):
        """Test that requests are persisted and can be reloaded."""
        # Create workflow and add request
        workflow1 = EscalationApprovalWorkflow(temp_storage)
        request = workflow1.create_request(
            issue_id="FEAT-0001",
            from_level=CriticalityLevel.LOW,
            to_level=CriticalityLevel.HIGH,
            reason="Persistence test",
            requested_by="user1",
        )

        # Create new workflow instance with same storage
        workflow2 = EscalationApprovalWorkflow(temp_storage)
        loaded = workflow2.get_request(request.id)

        assert loaded is not None
        assert loaded.issue_id == "FEAT-0001"
        assert loaded.reason == "Persistence test"


class TestCriticalityTypeMapping:
    """Tests for CriticalityTypeMapping."""

    def test_get_default_epic(self):
        """Test default criticality for epic type."""
        assert CriticalityTypeMapping.get_default("epic") == CriticalityLevel.HIGH

    def test_get_default_feature(self):
        """Test default criticality for feature type."""
        assert CriticalityTypeMapping.get_default("feature") == CriticalityLevel.MEDIUM

    def test_get_default_chore(self):
        """Test default criticality for chore type."""
        assert CriticalityTypeMapping.get_default("chore") == CriticalityLevel.LOW

    def test_get_default_fix(self):
        """Test default criticality for fix type."""
        assert CriticalityTypeMapping.get_default("fix") == CriticalityLevel.HIGH

    def test_get_default_unknown_type(self):
        """Test default for unknown type falls back to MEDIUM."""
        assert CriticalityTypeMapping.get_default("unknown") == CriticalityLevel.MEDIUM

    def test_get_all_mappings(self):
        """Test getting all default mappings."""
        mappings = CriticalityTypeMapping.get_all_mappings()
        assert "epic" in mappings
        assert "feature" in mappings
        assert "chore" in mappings
        assert "fix" in mappings


class TestCriticalityValidator:
    """Tests for CriticalityValidator."""

    def test_can_modify_same_level(self):
        """Test that same-level modification is allowed."""
        can_modify, error = CriticalityValidator.can_modify_criticality(
            CriticalityLevel.MEDIUM,
            CriticalityLevel.MEDIUM,
        )
        assert can_modify is True
        assert error is None

    def test_cannot_lower_criticality(self):
        """Test that lowering criticality is prohibited."""
        can_modify, error = CriticalityValidator.can_modify_criticality(
            CriticalityLevel.HIGH,
            CriticalityLevel.LOW,
        )
        assert can_modify is False
        assert error is not None
        assert "cannot be lowered" in error.lower()

    def test_escalation_requires_approval(self):
        """Test that escalation without approval is rejected."""
        can_modify, error = CriticalityValidator.can_modify_criticality(
            CriticalityLevel.LOW,
            CriticalityLevel.HIGH,
            is_escalation_approved=False,
        )
        assert can_modify is False
        assert "requires approval" in error.lower()

    def test_escalation_with_approval_allowed(self):
        """Test that approved escalation is allowed."""
        can_modify, error = CriticalityValidator.can_modify_criticality(
            CriticalityLevel.MEDIUM,
            CriticalityLevel.CRITICAL,
            is_escalation_approved=True,
        )
        assert can_modify is True
        assert error is None

    def test_validate_policy_compliance_no_violations(self):
        """Test compliance check with no violations."""
        violations = CriticalityValidator.validate_policy_compliance(
            criticality=CriticalityLevel.LOW,
            actual_coverage=80.0,
            has_agent_review=True,
            has_human_review=False,
        )
        assert len(violations) == 0

    def test_validate_policy_coverage_violation(self):
        """Test coverage violation detection."""
        violations = CriticalityValidator.validate_policy_compliance(
            criticality=CriticalityLevel.HIGH,
            actual_coverage=70.0,  # Below 85% requirement
            has_agent_review=True,
            has_human_review=True,
        )
        assert len(violations) > 0
        assert any("coverage" in v.lower() for v in violations)

    def test_validate_policy_agent_review_violation(self):
        """Test agent review violation detection."""
        violations = CriticalityValidator.validate_policy_compliance(
            criticality=CriticalityLevel.MEDIUM,
            actual_coverage=80.0,
            has_agent_review=False,
            has_human_review=True,
        )
        assert len(violations) > 0
        assert any("agent review" in v.lower() for v in violations)

    def test_validate_policy_human_review_violation(self):
        """Test human review violation for high criticality."""
        violations = CriticalityValidator.validate_policy_compliance(
            criticality=CriticalityLevel.HIGH,
            actual_coverage=90.0,
            has_agent_review=True,
            has_human_review=False,  # Required for HIGH
        )
        assert len(violations) > 0
        assert any("human review" in v.lower() for v in violations)
