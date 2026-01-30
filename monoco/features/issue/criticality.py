"""
Issue Criticality System with Immutable Policy Enforcement.

This module implements the criticality system that:
1. Assigns criticality levels (low, medium, high, critical) to issues
2. Derives policies based on criticality (agent_review, human_review, coverage, etc.)
3. Enforces immutable policy compliance (can only escalate, never lower)
4. Supports escalation workflow with approval process
"""

from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import datetime
from pathlib import Path


class CriticalityLevel(str, Enum):
    """Criticality levels for issues, ordered from lowest to highest."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_string(cls, value: str) -> "CriticalityLevel":
        """Parse criticality level from string (case-insensitive)."""
        mapping = {
            "low": cls.LOW,
            "medium": cls.MEDIUM,
            "high": cls.HIGH,
            "critical": cls.CRITICAL,
        }
        return mapping.get(value.lower(), cls.MEDIUM)

    @property
    def numeric_value(self) -> int:
        """Return numeric value for comparison."""
        return {
            CriticalityLevel.LOW: 1,
            CriticalityLevel.MEDIUM: 2,
            CriticalityLevel.HIGH: 3,
            CriticalityLevel.CRITICAL: 4,
        }[self]

    def __lt__(self, other: "CriticalityLevel") -> bool:
        return self.numeric_value < other.numeric_value

    def __le__(self, other: "CriticalityLevel") -> bool:
        return self.numeric_value <= other.numeric_value

    def __gt__(self, other: "CriticalityLevel") -> bool:
        return self.numeric_value > other.numeric_value

    def __ge__(self, other: "CriticalityLevel") -> bool:
        return self.numeric_value >= other.numeric_value


class AgentReviewLevel(str, Enum):
    """Agent review intensity levels."""

    LIGHTWEIGHT = "lightweight"
    STANDARD = "standard"
    STRICT = "strict"
    STRICT_AUDIT = "strict+audit"


class HumanReviewLevel(str, Enum):
    """Human review requirements."""

    OPTIONAL = "optional"
    RECOMMENDED = "recommended"
    REQUIRED = "required"
    REQUIRED_RECORD = "required+record"


class RollbackAction(str, Enum):
    """Rollback behavior on failure."""

    WARN = "warn"
    ROLLBACK = "rollback"
    BLOCK = "block"
    BLOCK_NOTIFY = "block+notify"


class Policy(BaseModel):
    """
    Derived policy based on criticality level.
    Defines quality standards and review requirements.
    """

    agent_review: AgentReviewLevel = Field(
        default=AgentReviewLevel.STANDARD, description="Agent code review intensity"
    )
    human_review: HumanReviewLevel = Field(
        default=HumanReviewLevel.RECOMMENDED, description="Human review requirement"
    )
    min_coverage: int = Field(
        default=70, ge=0, le=100, description="Minimum test coverage percentage"
    )
    rollback_on_failure: RollbackAction = Field(
        default=RollbackAction.ROLLBACK, description="Action on failure"
    )
    require_security_scan: bool = Field(
        default=False, description="Require security vulnerability scan"
    )
    require_performance_check: bool = Field(
        default=False, description="Require performance regression check"
    )
    max_reviewers: int = Field(
        default=1, ge=1, le=5, description="Number of reviewers required"
    )

    model_config = ConfigDict(frozen=True)  # Policies are immutable once derived


class EscalationStatus(str, Enum):
    """Status of an escalation request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class EscalationRequest(BaseModel):
    """
    Request to escalate issue criticality.
    Requires approval from authorized personnel.
    """

    id: str = Field(description="Unique escalation request ID")
    issue_id: str = Field(description="Target issue ID")
    from_level: CriticalityLevel = Field(description="Current criticality level")
    to_level: CriticalityLevel = Field(description="Requested criticality level")
    reason: str = Field(description="Business/technical justification")
    requested_by: str = Field(description="User who requested escalation")
    requested_at: datetime = Field(default_factory=datetime.now)
    status: EscalationStatus = Field(default=EscalationStatus.PENDING)
    approved_by: Optional[str] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    rejection_reason: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def validate_escalation_direction(self) -> "EscalationRequest":
        """Ensure escalation is upward only."""
        if self.to_level <= self.from_level:
            raise ValueError(
                f"Escalation must be to a higher level: "
                f"{self.from_level.value} -> {self.to_level.value}"
            )
        return self


class PolicyResolver:
    """
    Resolves policies based on criticality level.
    Centralized policy definition to ensure consistency.
    """

    # Criticality to Policy mapping (source of truth)
    _POLICY_MAP: Dict[CriticalityLevel, Policy] = {
        CriticalityLevel.LOW: Policy(
            agent_review=AgentReviewLevel.LIGHTWEIGHT,
            human_review=HumanReviewLevel.OPTIONAL,
            min_coverage=0,
            rollback_on_failure=RollbackAction.WARN,
            require_security_scan=False,
            require_performance_check=False,
            max_reviewers=1,
        ),
        CriticalityLevel.MEDIUM: Policy(
            agent_review=AgentReviewLevel.STANDARD,
            human_review=HumanReviewLevel.RECOMMENDED,
            min_coverage=70,
            rollback_on_failure=RollbackAction.ROLLBACK,
            require_security_scan=False,
            require_performance_check=False,
            max_reviewers=1,
        ),
        CriticalityLevel.HIGH: Policy(
            agent_review=AgentReviewLevel.STRICT,
            human_review=HumanReviewLevel.REQUIRED,
            min_coverage=85,
            rollback_on_failure=RollbackAction.BLOCK,
            require_security_scan=True,
            require_performance_check=False,
            max_reviewers=2,
        ),
        CriticalityLevel.CRITICAL: Policy(
            agent_review=AgentReviewLevel.STRICT_AUDIT,
            human_review=HumanReviewLevel.REQUIRED_RECORD,
            min_coverage=90,
            rollback_on_failure=RollbackAction.BLOCK_NOTIFY,
            require_security_scan=True,
            require_performance_check=True,
            max_reviewers=3,
        ),
    }

    @classmethod
    def resolve(cls, criticality: CriticalityLevel) -> Policy:
        """Get the policy for a given criticality level."""
        return cls._POLICY_MAP.get(
            criticality, cls._POLICY_MAP[CriticalityLevel.MEDIUM]
        )

    @classmethod
    def get_all_policies(cls) -> Dict[CriticalityLevel, Policy]:
        """Get all defined policies (for reporting/documentation)."""
        return cls._POLICY_MAP.copy()


class CriticalityInheritanceService:
    """
    Handles criticality inheritance rules for child issues.
    Child issues must inherit at least the parent's criticality.
    """

    @staticmethod
    def resolve_child_criticality(
        parent_criticality: Optional[CriticalityLevel],
        proposed_criticality: CriticalityLevel,
    ) -> CriticalityLevel:
        """
        Resolve the effective criticality for a child issue.
        Child must be at least as critical as parent.
        """
        if parent_criticality is None:
            return proposed_criticality

        # Child must inherit parent's minimum criticality
        if proposed_criticality < parent_criticality:
            return parent_criticality
        return proposed_criticality

    @staticmethod
    def can_lower_child_criticality(
        child_criticality: CriticalityLevel, parent_criticality: CriticalityLevel
    ) -> bool:
        """
        Check if a child's criticality can be lowered.
        Can only lower if it won't go below parent's level.
        """
        # This is a theoretical check - actual lowering is prohibited
        # This method is for validation purposes
        return child_criticality > parent_criticality


class AutoEscalationRule(BaseModel):
    """Rule for automatically escalating criticality based on conditions."""

    name: str
    description: str
    path_patterns: List[str] = Field(default_factory=list)
    tag_patterns: List[str] = Field(default_factory=list)
    type_patterns: List[str] = Field(default_factory=list)
    target_level: CriticalityLevel


class AutoEscalationDetector:
    """
    Detects when an issue should be auto-escalated based on:
    - File path patterns (e.g., payment/** -> critical)
    - Tags (e.g., "security", "payment")
    - Issue type mappings
    """

    # Default auto-escalation rules
    DEFAULT_RULES: List[AutoEscalationRule] = [
        AutoEscalationRule(
            name="payment_critical",
            description="Payment-related code requires critical handling",
            path_patterns=["**/payment/**", "**/billing/**", "**/finance/**"],
            tag_patterns=["payment", "billing", "finance"],
            target_level=CriticalityLevel.CRITICAL,
        ),
        AutoEscalationRule(
            name="security_high",
            description="Security-related changes require high scrutiny",
            path_patterns=["**/auth/**", "**/security/**", "**/crypto/**"],
            tag_patterns=["security", "auth", "authentication", "authorization"],
            target_level=CriticalityLevel.HIGH,
        ),
        AutoEscalationRule(
            name="database_high",
            description="Database schema changes require high scrutiny",
            path_patterns=["**/migrations/**", "**/schema/**"],
            tag_patterns=["database", "migration", "schema"],
            target_level=CriticalityLevel.HIGH,
        ),
    ]

    def __init__(self, custom_rules: Optional[List[AutoEscalationRule]] = None):
        self.rules = custom_rules or self.DEFAULT_RULES

    def detect_escalation(
        self,
        current_level: CriticalityLevel,
        file_paths: List[str],
        tags: List[str],
        issue_type: Optional[str] = None,
    ) -> Optional[CriticalityLevel]:
        """
        Detect if issue should be escalated based on rules.
        Returns the highest applicable level or None if no escalation needed.
        """
        max_level = current_level
        should_escalate = False

        for rule in self.rules:
            if self._matches_rule(rule, file_paths, tags, issue_type):
                if rule.target_level > max_level:
                    max_level = rule.target_level
                    should_escalate = True

        return max_level if should_escalate else None

    def _matches_rule(
        self,
        rule: AutoEscalationRule,
        file_paths: List[str],
        tags: List[str],
        issue_type: Optional[str],
    ) -> bool:
        """Check if an issue matches an escalation rule."""
        import fnmatch

        # Check path patterns
        for pattern in rule.path_patterns:
            for path in file_paths:
                if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(
                    path, f"*/{pattern}"
                ):
                    return True

        # Check tag patterns
        for pattern in rule.tag_patterns:
            for tag in tags:
                if pattern.lower() in tag.lower():
                    return True

        # Check type patterns
        if issue_type and rule.type_patterns:
            if issue_type.lower() in [t.lower() for t in rule.type_patterns]:
                return True

        return False


class EscalationApprovalWorkflow:
    """
    Manages the escalation approval workflow.
    Tracks pending requests and handles approval/rejection.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path
        self._requests: Dict[str, EscalationRequest] = {}
        self._load_requests()

    def _load_requests(self) -> None:
        """Load persisted escalation requests."""
        if self.storage_path and self.storage_path.exists():
            import yaml

            try:
                data = yaml.safe_load(self.storage_path.read_text()) or {}
                for req_data in data.get("requests", []):
                    req = EscalationRequest(**req_data)
                    self._requests[req.id] = req
            except Exception:
                pass  # Start fresh if corrupted

    def _save_requests(self) -> None:
        """Persist escalation requests."""
        if self.storage_path:
            import yaml

            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "requests": [
                    req.model_dump(mode="json") for req in self._requests.values()
                ]
            }
            self.storage_path.write_text(yaml.dump(data, sort_keys=False))

    def create_request(
        self,
        issue_id: str,
        from_level: CriticalityLevel,
        to_level: CriticalityLevel,
        reason: str,
        requested_by: str,
    ) -> EscalationRequest:
        """Create a new escalation request."""
        import secrets

        request_id = f"ESC-{secrets.token_hex(4).upper()}"
        request = EscalationRequest(
            id=request_id,
            issue_id=issue_id,
            from_level=from_level,
            to_level=to_level,
            reason=reason,
            requested_by=requested_by,
        )
        self._requests[request_id] = request
        self._save_requests()
        return request

    def approve(self, request_id: str, approved_by: str) -> EscalationRequest:
        """Approve an escalation request."""
        if request_id not in self._requests:
            raise ValueError(f"Escalation request {request_id} not found")

        request = self._requests[request_id]
        if request.status != EscalationStatus.PENDING:
            raise ValueError(f"Request is already {request.status.value}")

        request.status = EscalationStatus.APPROVED
        request.approved_by = approved_by
        request.approved_at = datetime.now()
        self._save_requests()
        return request

    def reject(
        self, request_id: str, rejected_by: str, reason: str
    ) -> EscalationRequest:
        """Reject an escalation request."""
        if request_id not in self._requests:
            raise ValueError(f"Escalation request {request_id} not found")

        request = self._requests[request_id]
        if request.status != EscalationStatus.PENDING:
            raise ValueError(f"Request is already {request.status.value}")

        request.status = EscalationStatus.REJECTED
        request.approved_by = rejected_by  # Using same field for rejector
        request.approved_at = datetime.now()
        request.rejection_reason = reason
        self._save_requests()
        return request

    def get_pending_for_issue(self, issue_id: str) -> List[EscalationRequest]:
        """Get all pending escalation requests for an issue."""
        return [
            req
            for req in self._requests.values()
            if req.issue_id == issue_id and req.status == EscalationStatus.PENDING
        ]

    def get_request(self, request_id: str) -> Optional[EscalationRequest]:
        """Get a specific escalation request."""
        return self._requests.get(request_id)


class CriticalityTypeMapping:
    """
    Default criticality mappings based on issue type.
    These are starting points, can be overridden at creation.
    """

    DEFAULT_MAPPINGS: Dict[str, CriticalityLevel] = {
        "epic": CriticalityLevel.HIGH,  # Epics are strategic
        "feature": CriticalityLevel.MEDIUM,  # Features are value-delivering
        "chore": CriticalityLevel.LOW,  # Chores are maintenance
        "fix": CriticalityLevel.HIGH,  # Fixes address problems
    }

    @classmethod
    def get_default(cls, issue_type: str) -> CriticalityLevel:
        """Get default criticality for an issue type."""
        return cls.DEFAULT_MAPPINGS.get(issue_type.lower(), CriticalityLevel.MEDIUM)

    @classmethod
    def get_all_mappings(cls) -> Dict[str, CriticalityLevel]:
        """Get all default type mappings."""
        return cls.DEFAULT_MAPPINGS.copy()


class CriticalityValidator:
    """
    Validates criticality-related constraints and permissions.
    Enforces the immutable policy: can only escalate, never lower.
    """

    @staticmethod
    def can_modify_criticality(
        current_level: CriticalityLevel,
        proposed_level: CriticalityLevel,
        is_escalation_approved: bool = False,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if criticality modification is allowed.
        Returns (is_allowed, reason_if_denied).
        """
        # Direct lowering is never allowed
        if proposed_level < current_level:
            return (
                False,
                "Criticality cannot be lowered. Use escalation workflow to increase.",
            )

        # Same level is always allowed (no-op)
        if proposed_level == current_level:
            return True, None

        # Escalation requires approval
        if proposed_level > current_level and not is_escalation_approved:
            return (
                False,
                f"Escalation from {current_level.value} to {proposed_level.value} requires approval.",
            )

        return True, None

    @staticmethod
    def validate_policy_compliance(
        criticality: CriticalityLevel,
        actual_coverage: Optional[float],
        has_agent_review: bool,
        has_human_review: bool,
    ) -> List[str]:
        """
        Validate that an issue complies with its criticality policy.
        Returns list of violations.
        """
        policy = PolicyResolver.resolve(criticality)
        violations = []

        # Coverage check
        if actual_coverage is not None and actual_coverage < policy.min_coverage:
            violations.append(
                f"Test coverage {actual_coverage:.1f}% below minimum {policy.min_coverage}%"
            )

        # Agent review check
        if not has_agent_review:
            violations.append(f"Agent review ({policy.agent_review.value}) required")

        # Human review check
        if policy.human_review in [
            HumanReviewLevel.REQUIRED,
            HumanReviewLevel.REQUIRED_RECORD,
        ]:
            if not has_human_review:
                violations.append(
                    f"Human review ({policy.human_review.value}) required"
                )

        return violations
