"""
Mailbox Protocol Validators.

This module provides validation logic for Mailbox protocol messages,
including YAML Frontmatter validation and file structure checks.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .constants import (
    MAX_ARTIFACTS_PER_MESSAGE,
    MAX_MESSAGE_SIZE_BYTES,
    PROVIDER_SUBDIRS,
    YAML_END,
    YAML_START,
)
from .schema import DraftMessage, InboundMessage, OutboundMessage


@dataclass
class ValidationError:
    """Single validation error."""

    field: str | None
    message: str
    severity: str = "error"  # error, warning


@dataclass
class ValidationResult:
    """Validation result for a message."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)

    def add_error(self, field: str | None, message: str, severity: str = "error") -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(field=field, message=message, severity=severity))
        if severity == "error":
            self.valid = False

    def add_warning(self, field: str | None, message: str) -> None:
        """Add a validation warning."""
        self.errors.append(ValidationError(field=field, message=message, severity="warning"))


class MessageValidator:
    """
    Validator for Mailbox protocol messages.

    Validates:
    - YAML Frontmatter syntax and required fields
    - Message schema compliance
    - File naming conventions
    - Provider-specific rules
    """

    # Required fields by message type
    INBOUND_REQUIRED = ["id", "provider", "session", "participants", "timestamp"]
    OUTBOUND_REQUIRED = ["provider", "timestamp"]
    DRAFT_REQUIRED: list[str] = []  # Drafts are flexible

    def __init__(self, strict: bool = False):
        """
        Initialize validator.

        Args:
            strict: If True, warnings are treated as errors
        """
        self.strict = strict

    def validate_inbound(self, data: dict[str, Any]) -> ValidationResult:
        """
        Validate inbound message schema.

        Args:
            data: Parsed YAML frontmatter + content

        Returns:
            ValidationResult with errors/warnings
        """
        result = ValidationResult(valid=True)

        # Check required fields
        for field in self.INBOUND_REQUIRED:
            if field not in data:
                result.add_error(field, f"Missing required field: {field}")

        # Validate with Pydantic if basic check passes
        if result.valid:
            try:
                InboundMessage.model_validate(data)
            except Exception as e:
                result.add_error(None, f"Schema validation failed: {e}")

        # Validate message ID format
        if "id" in data:
            msg_id = data["id"]
            if "_" not in str(msg_id):
                result.add_error("id", "Message ID must follow format: {provider}_{uid}")

        # Validate session structure
        if "session" in data and isinstance(data["session"], dict):
            session = data["session"]
            if "id" not in session:
                result.add_error("session.id", "Session must have an 'id' field")

        # Validate participants structure
        if "participants" in data and isinstance(data["participants"], dict):
            participants = data["participants"]
            if "sender" not in participants:
                result.add_error("participants.sender", "Participants must have a 'sender'")

        # Check artifacts limit
        if "artifacts" in data and len(data["artifacts"]) > MAX_ARTIFACTS_PER_MESSAGE:
            result.add_error(
                "artifacts",
                f"Too many artifacts: {len(data['artifacts'])} > {MAX_ARTIFACTS_PER_MESSAGE}",
            )

        return result

    def validate_outbound(self, data: dict[str, Any]) -> ValidationResult:
        """
        Validate outbound message schema.

        Args:
            data: Parsed YAML frontmatter + content

        Returns:
            ValidationResult with errors/warnings
        """
        result = ValidationResult(valid=True)

        # Check required fields
        for field in self.OUTBOUND_REQUIRED:
            if field not in data:
                result.add_error(field, f"Missing required field: {field}")

        # Validate with Pydantic
        if result.valid:
            try:
                OutboundMessage.model_validate(data)
            except Exception as e:
                result.add_error(None, f"Schema validation failed: {e}")

        # Validate delivery_method consistency
        if "delivery_method" in data and "reply_to" in data:
            if data["delivery_method"] == "reply" and not data.get("reply_to"):
                result.add_warning("reply_to", "delivery_method is 'reply' but reply_to is empty")

        # Check artifacts limit
        if "artifacts" in data and len(data["artifacts"]) > MAX_ARTIFACTS_PER_MESSAGE:
            result.add_error(
                "artifacts",
                f"Too many artifacts: {len(data['artifacts'])} > {MAX_ARTIFACTS_PER_MESSAGE}",
            )

        return result

    def validate_draft(self, data: dict[str, Any]) -> ValidationResult:
        """
        Validate draft message schema.

        Drafts are more lenient as they're pre-submission.

        Args:
            data: Parsed YAML frontmatter + content

        Returns:
            ValidationResult with errors/warnings
        """
        result = ValidationResult(valid=True)

        # Validate with Pydantic (lenient)
        try:
            DraftMessage.model_validate(data)
        except Exception as e:
            result.add_error(None, f"Draft schema validation failed: {e}")

        # Warn if no target specified
        if not data.get("to") and not data.get("reply_to"):
            result.add_warning(None, "No target specified (to or reply_to)")

        # Validate artifact references
        if "artifacts" in data:
            for i, art in enumerate(data["artifacts"]):
                if isinstance(art, str) and not art.startswith("sha256:"):
                    result.add_warning(
                        f"artifacts[{i}]",
                        f"Artifact hash should start with 'sha256:': {art}",
                    )

        return result

    def validate_file_path(self, path: Path, expected_type: str | None = None) -> ValidationResult:
        """
        Validate message file path conforms to protocol.

        Args:
            path: Path to validate
            expected_type: Expected message type (inbound/outbound/draft)

        Returns:
            ValidationResult with errors/warnings
        """
        result = ValidationResult(valid=True)

        # Check extension
        if path.suffix != ".md":
            result.add_error(None, f"Message file must have .md extension: {path}")

        # Check parent directories for provider subdirs
        parts = path.parts

        if "inbound" in parts:
            # Check provider subdirectory exists
            inbound_idx = parts.index("inbound")
            if inbound_idx + 1 < len(parts):
                provider = parts[inbound_idx + 1]
                if provider not in PROVIDER_SUBDIRS:
                    result.add_warning(None, f"Unknown provider subdirectory: {provider}")

        elif "outbound" in parts:
            outbound_idx = parts.index("outbound")
            if outbound_idx + 1 < len(parts):
                provider = parts[outbound_idx + 1]
                if provider not in PROVIDER_SUBDIRS:
                    result.add_warning(None, f"Unknown provider subdirectory: {provider}")

        return result

    @staticmethod
    def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Full markdown content with frontmatter

        Returns:
            Tuple of (frontmatter_dict, markdown_body)

        Raises:
            ValueError: If frontmatter is malformed
        """
        if not content.startswith(YAML_START):
            raise ValueError("Content does not start with YAML frontmatter marker ---")

        # Find end of frontmatter
        end_idx = content.find(YAML_END, len(YAML_START))
        if end_idx == -1:
            raise ValueError("Could not find end of YAML frontmatter")

        yaml_content = content[len(YAML_START) : end_idx]
        body = content[end_idx + len(YAML_END) :]

        try:
            frontmatter = yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}")

        return frontmatter, body

    @staticmethod
    def validate_content_size(content: str) -> ValidationResult:
        """Validate message content size."""
        result = ValidationResult(valid=True)

        size_bytes = len(content.encode("utf-8"))
        if size_bytes > MAX_MESSAGE_SIZE_BYTES:
            result.add_error(
                None,
                f"Message size {size_bytes} bytes exceeds limit {MAX_MESSAGE_SIZE_BYTES}",
            )

        return result
