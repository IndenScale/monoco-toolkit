"""
Mailbox Protocol Schema - Core data models for message exchange.

This module defines the unified Schema for messages between Monoco and external platforms.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class Provider(str, Enum):
    """Message provider/platform types."""
    LARK = "lark"
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    WECOM = "wecom"
    DINGTALK = "dingtalk"


class Direction(str, Enum):
    """Message direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class SessionType(str, Enum):
    """Session/chat types."""
    DIRECT = "direct"  # 1-on-1 chat
    GROUP = "group"    # Group chat
    THREAD = "thread"  # Thread/topic-based discussion


class ContentType(str, Enum):
    """Content type of the message."""
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    CARD = "card"      # Structured card (Lark/Slack)
    MIXED = "mixed"    # Mixed content


class ArtifactType(str, Enum):
    """Type of attached artifact."""
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    CODE = "code"
    UNKNOWN = "unknown"


class Role(str, Enum):
    """Role of a participant in a session."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"
    EXTERNAL = "external"


class MentionType(str, Enum):
    """Type of mention in a message."""
    USER = "user"
    ALL = "all"        # @everyone/@all
    CHANNEL = "channel"  # @channel
    ROLE = "role"      # @role


class MessageStatus(str, Enum):
    """Status of a message in the processing pipeline."""
    NEW = "new"                # Just received, not yet claimed
    CLAIMED = "claimed"        # Claimed by an agent
    COMPLETED = "completed"    # Successfully processed
    FAILED = "failed"          # Processing failed
    ARCHIVED = "archived"      # Moved to archive
    DEADLETTER = "deadletter"  # Failed permanently


class Participant(BaseModel):
    """A participant (sender or recipient) in a message."""
    id: str = Field(..., description="Platform user unique identifier")
    name: str = Field(..., description="Display name")
    email: Optional[str] = Field(None, description="Email address (required for email)")
    platform_id: Optional[str] = Field(None, description="Platform-specific ID (e.g., open_id)")
    role: Role = Field(Role.MEMBER, description="Role in the session")
    avatar: Optional[str] = Field(None, description="Avatar URL")


class Mention(BaseModel):
    """An @mention in a message."""
    type: MentionType = Field(..., description="Type of mention")
    target: str = Field(..., description="Target user ID or special identifier")
    name: Optional[str] = Field(None, description="Display text of the mention")
    offset: Optional[int] = Field(None, description="Position in the text")


class Session(BaseModel):
    """Session/chat context for a message."""
    id: str = Field(..., description="Physical aggregation identifier (chat_id, email)")
    type: SessionType = Field(..., description="Type of session")
    name: Optional[str] = Field(None, description="Session display name")
    thread_key: Optional[str] = Field(None, description="Logical topic identifier")


class Content(BaseModel):
    """Message content in various formats."""
    text: Optional[str] = Field(None, description="Plain text content")
    html: Optional[str] = Field(None, description="HTML format (email mainly)")
    markdown: Optional[str] = Field(None, description="Markdown format")
    card: Optional[Dict[str, Any]] = Field(None, description="Structured card data")


class Artifact(BaseModel):
    """An attached artifact/file."""
    id: str = Field(..., description="Artifact ID (SHA256 hash)")
    name: str = Field(..., description="Original filename")
    type: ArtifactType = Field(..., description="Type of artifact")
    mime_type: Optional[str] = Field(None, description="MIME type")
    size: Optional[int] = Field(None, description="File size in bytes")
    path: str = Field(..., description="Path relative to ~/.monoco/dropbox/")
    url: Optional[str] = Field(None, description="Original download URL")
    downloaded_at: Optional[datetime] = Field(None, description="Download timestamp")
    inline: bool = Field(False, description="Whether this is an inline attachment")


class InboundMessage(BaseModel):
    """
    An inbound message received from an external platform.

    This is the primary data model for messages written by Courier and read by Mailbox.
    """
    # Core Identity
    id: str = Field(..., description="Global unique identifier: {provider}_{uid}")
    provider: Provider = Field(..., description="Message source platform")
    direction: Direction = Field(Direction.INBOUND, description="Message direction")

    # Session Context
    session: Session = Field(..., description="Session/chat context")

    # Participants
    participants: Dict[str, Any] = Field(
        default_factory=dict,
        description="Message participants: from, to, cc, bcc, mentions"
    )

    # Timestamps
    timestamp: datetime = Field(..., description="Original send time (UTC)")
    received_at: Optional[datetime] = Field(None, description="Courier received time (UTC)")
    processed_at: Optional[datetime] = Field(None, description="Agent processed time")

    # Content
    type: ContentType = Field(..., description="Content type")
    content: Content = Field(default_factory=Content, description="Message content")

    # Artifacts
    artifacts: List[Artifact] = Field(default_factory=list, description="Attached files")

    # Correlation
    correlation_id: Optional[str] = Field(None, description="Business correlation ID")
    reply_to: Optional[str] = Field(None, description="Reply target message ID")
    thread_root: Optional[str] = Field(None, description="Thread root message ID")

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific raw metadata"
    )

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate ID format: {provider}_{uid}"""
        if '_' not in v:
            raise ValueError(f"Message ID must follow format {{provider}}_{{uid}}, got: {v}")
        return v

    def get_sender(self) -> Optional[Participant]:
        """Get the sender participant."""
        from_participant = self.participants.get('from')
        if from_participant and isinstance(from_participant, dict):
            return Participant(**from_participant)
        return None

    def get_recipients(self) -> List[Participant]:
        """Get the recipient participants."""
        to_participants = self.participants.get('to', [])
        if to_participants and isinstance(to_participants, list):
            return [Participant(**p) if isinstance(p, dict) else p for p in to_participants]
        return []

    def get_mentions(self) -> List[Mention]:
        """Get @mentions in the message."""
        mentions = self.participants.get('mentions', [])
        if mentions and isinstance(mentions, list):
            return [Mention(**m) if isinstance(m, dict) else m for m in mentions]
        return []

    def get_preview(self, max_length: int = 50) -> str:
        """Get a preview of the message content."""
        text = self.content.text or self.content.markdown or ""
        if not text:
            return f"[{self.type.value}]"
        if len(text) > max_length:
            return text[:max_length - 3] + "..."
        return text

    def to_filename(self) -> str:
        """Generate the storage filename for this message."""
        ts = self.timestamp.strftime("%Y%m%dT%H%M%S")
        # Sanitize message id to be filesystem-safe
        safe_id = self.id.replace("/", "_").replace("\\", "_")
        return f"{ts}_{self.provider.value}_{safe_id}.md"


class OutboundMessage(BaseModel):
    """
    An outbound message to be sent to an external platform.

    This is created by Mailbox CLI and processed by Courier.
    """
    # Target
    to: Union[str, List[str]] = Field(..., description="Target user/group ID(s) or email(s)")
    cc: Optional[Union[str, List[str]]] = Field(None, description="CC recipients (email)")
    bcc: Optional[Union[str, List[str]]] = Field(None, description="BCC recipients (email)")

    # Context
    provider: Provider = Field(..., description="Target platform")
    reply_to: Optional[str] = Field(None, description="Message ID being replied to")
    thread_key: Optional[str] = Field(None, description="Thread identifier for context")

    # Content
    type: ContentType = Field(ContentType.TEXT, description="Content type")
    content: Content = Field(default_factory=Content, description="Message content")

    # Artifacts
    artifacts: List[Artifact] = Field(default_factory=list, description="Files to attach")

    # Options
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sending options: silent, urgent, schedule_at"
    )

    def to_filename(self, uid: str) -> str:
        """Generate the storage filename for this outbound message."""
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        # Sanitize uid to be filesystem-safe
        safe_uid = uid.replace("/", "_").replace("\\", "_")
        return f"{ts}_{self.provider.value}_{safe_uid}.md"


# Union type for generic message handling
Message = Union[InboundMessage, OutboundMessage]
