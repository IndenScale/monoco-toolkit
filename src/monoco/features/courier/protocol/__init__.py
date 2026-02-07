"""
Courier Protocol - Re-export from connector protocol.

This module re-exports the shared protocol definitions from the connector
feature, providing a stable import path for courier-related code.
"""

# Re-export from connector.protocol
from monoco.features.connector.protocol import (
    # Enums
    Provider,
    Direction,
    SessionType,
    ContentType,
    ArtifactType,
    Role,
    MentionType,
    MessageStatus,
    # Models
    Participant,
    Mention,
    Session,
    Content,
    Artifact,
    InboundMessage,
    OutboundMessage,
    Message,
    # Constants
    MAILBOX_DIR,
    INBOUND_DIR,
    OUTBOUND_DIR,
    ARCHIVE_DIR,
    STATE_DIR,
    DEADLETTER_DIR,
    TMP_DIR,
    DEFAULT_MAILBOX_ROOT,
    CLAIM_TIMEOUT_SECONDS,
    MAX_RETRY_ATTEMPTS,
    API_PREFIX,
    API_MESSAGE_CLAIM,
    API_MESSAGE_COMPLETE,
    API_MESSAGE_FAIL,
    # Validators
    validate_inbound_message,
    validate_outbound_message,
    validate_provider,
    validate_content_type,
    validate_message_id,
    validate_filename,
    get_validation_errors,
)

__all__ = [
    # Enums
    "Provider",
    "Direction",
    "SessionType",
    "ContentType",
    "ArtifactType",
    "Role",
    "MentionType",
    "MessageStatus",
    # Models
    "Participant",
    "Mention",
    "Session",
    "Content",
    "Artifact",
    "InboundMessage",
    "OutboundMessage",
    "Message",
    # Constants
    "MAILBOX_DIR",
    "INBOUND_DIR",
    "OUTBOUND_DIR",
    "ARCHIVE_DIR",
    "STATE_DIR",
    "DEADLETTER_DIR",
    "TMP_DIR",
    "DEFAULT_MAILBOX_ROOT",
    "CLAIM_TIMEOUT_SECONDS",
    "MAX_RETRY_ATTEMPTS",
    "API_PREFIX",
    "API_MESSAGE_CLAIM",
    "API_MESSAGE_COMPLETE",
    "API_MESSAGE_FAIL",
    # Validators
    "validate_inbound_message",
    "validate_outbound_message",
    "validate_provider",
    "validate_content_type",
    "validate_message_id",
    "validate_filename",
    "get_validation_errors",
]
