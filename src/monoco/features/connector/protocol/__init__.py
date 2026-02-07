"""
Connector Protocol - Shared Schema between Mailbox and Courier.

This module defines the protocol layer for message exchange.
"""

from .schema import (
    Provider,
    Direction,
    SessionType,
    ContentType,
    ArtifactType,
    Role,
    MentionType,
    MessageStatus,
    Participant,
    Mention,
    Session,
    Content,
    Artifact,
    InboundMessage,
    OutboundMessage,
    Message,
)
from .constants import (
    MAILBOX_DIR,
    INBOUND_DIR,
    OUTBOUND_DIR,
    ARCHIVE_DIR,
    STATE_DIR,
    DEADLETTER_DIR,
    TMP_DIR,
    DEFAULT_MAILBOX_ROOT,
)
from .validators import validate_inbound_message, validate_outbound_message

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
    # Validators
    "validate_inbound_message",
    "validate_outbound_message",
]
