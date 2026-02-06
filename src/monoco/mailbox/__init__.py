"""
Mailbox Protocol - File-based Message Bus for Monoco Courier.

This module defines the schema and validation logic for the Mailbox protocol,
a standardized file-based messaging system that enables communication between
Monoco agents and external services (IM, Email, etc.).

Key Concepts:
- Physical Structure: Maildir-style directories (inbound/, outbound/, archive/)
- Message Format: Markdown + YAML Frontmatter
- Session Model: Physical aggregation (session.id) + Logical threading (session.thread_key)
- Participants: Multi-source compatible structure supporting IM and Email patterns

Protocol Version: 1.0.0
"""

from .schema import (
    Participant,
    Participants,
    Session,
    ArtifactRef,
    InboundMessage,
    OutboundMessage,
    DraftMessage,
    MessageType,
    SessionType,
    Provider,
    DeliveryMethod,
)
from .validators import MessageValidator, ValidationResult, ValidationError
from .constants import (
    MAILBOX_DIR,
    INBOUND_DIR,
    OUTBOUND_DIR,
    ARCHIVE_DIR,
    DROPZONE_DIR,
    DEFAULT_DEBOUNCE_WINDOW_IM,
    DEFAULT_DEBOUNCE_WINDOW_EMAIL,
)

__version__ = "1.0.0"

__all__ = [
    # Schema models
    "Participant",
    "Participants",
    "Session",
    "ArtifactRef",
    "InboundMessage",
    "OutboundMessage",
    "DraftMessage",
    # Enums
    "MessageType",
    "SessionType",
    "Provider",
    "DeliveryMethod",
    # Validation
    "MessageValidator",
    "ValidationResult",
    "ValidationError",
    # Constants
    "MAILBOX_DIR",
    "INBOUND_DIR",
    "OUTBOUND_DIR",
    "ARCHIVE_DIR",
    "DROPZONE_DIR",
    "DEFAULT_DEBOUNCE_WINDOW_IM",
    "DEFAULT_DEBOUNCE_WINDOW_EMAIL",
]
