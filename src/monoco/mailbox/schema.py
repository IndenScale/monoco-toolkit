"""
Mailbox Protocol Schema Definitions.

This module defines the Pydantic models for the Mailbox protocol,
supporting both Inbound (external -> Monoco) and Outbound (Monoco -> external) messages.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class MessageType(str, Enum):
    """Message content types."""

    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    CARD = "card"  # Interactive card (Lark/WeChat)
    MARKDOWN = "markdown"
    MIXED = "mixed"  # Multi-part message


class SessionType(str, Enum):
    """Session/Conversation types."""

    DIRECT = "direct"  # One-on-one chat
    GROUP = "group"  # Group chat
    THREAD = "thread"  # Threaded conversation
    CHANNEL = "channel"  # Public channel (Discord/Slack style)


class Provider(str, Enum):
    """Supported message providers."""

    LARK = "lark"  # Feishu/Lark
    EMAIL = "email"  # SMTP/IMAP
    DISCORD = "discord"
    SLACK = "slack"
    WECHAT = "wechat"
    TELEGRAM = "telegram"
    CUSTOM = "custom"  # Generic webhook


class DeliveryMethod(str, Enum):
    """Message delivery methods for outbound messages."""

    REPLY = "reply"  # Reply to existing message
    DIRECT = "direct"  # Direct message
    BROADCAST = "broadcast"  # Group/channel message


class Participant(BaseModel):
    """
    A participant in a conversation.

    Attributes:
        id: Unique identifier (platform-specific)
        name: Display name
        platform_id: Platform-specific ID (e.g., Lark open_id)
        email: Email address (if applicable)
        role: Role in the conversation (owner, admin, member)
        metadata: Additional platform-specific attributes
    """

    id: str = Field(description="Unique participant identifier")
    name: str = Field(description="Display name")
    platform_id: str | None = Field(default=None, description="Platform-specific ID")
    email: str | None = Field(default=None, description="Email address")
    role: Literal["owner", "admin", "member", "guest", "bot"] = Field(
        default="member", description="Role in the conversation"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional attributes")


class Participants(BaseModel):
    """
    Multi-source compatible participants structure.

    Supports both IM-style (sender + mentions) and Email-style (from + to + cc) patterns.
    This unified model allows seamless handling of messages from different sources.

    Attributes:
        sender: The message sender (required)
        recipients: Primary recipients (Email style)
        cc: Carbon copy recipients (Email style)
        bcc: Blind carbon copy recipients (Email style)
        mentions: Mentioned users (IM style, e.g., [@Prime, @user123])
        reply_to: Participant to reply to (for threading)
    """

    sender: Participant = Field(description="Message sender")
    recipients: list[Participant] = Field(default_factory=list, description="Primary recipients")
    cc: list[Participant] = Field(default_factory=list, description="CC recipients")
    bcc: list[Participant] = Field(default_factory=list, description="BCC recipients")
    mentions: list[str] = Field(default_factory=list, description="Mentioned user IDs/names")
    reply_to: Participant | None = Field(default=None, description="Reply-to participant")

    @field_validator("mentions")
    @classmethod
    def validate_mentions(cls, v: list[str]) -> list[str]:
        """Normalize mentions to include @ prefix."""
        return [m if m.startswith("@") else f"@{m}" for m in v]


class Session(BaseModel):
    """
    Session context for message aggregation and threading.

    This model implements the dual-key strategy:
    - session.id: Physical aggregation identifier (e.g., chat_id, channel_id)
    - session.thread_key: Logical topic identifier (e.g., IM thread_id, Email In-Reply-To hash)

    Attributes:
        id: Physical session identifier (e.g., Lark chat_id, Email thread hash)
        type: Session type (direct/group/thread)
        name: Human-readable session name
        thread_key: Logical thread identifier for topic grouping
        parent_id: Parent message ID for nested threading (IM-style)
        root_id: Root message ID for thread reconstruction
        metadata: Additional session attributes
    """

    id: str = Field(description="Physical session/channel identifier")
    type: SessionType = Field(default=SessionType.DIRECT, description="Session type")
    name: str | None = Field(default=None, description="Session display name")
    thread_key: str | None = Field(
        default=None, description="Logical thread identifier (topic aggregation)"
    )
    parent_id: str | None = Field(
        default=None, description="Parent message ID for nested threading"
    )
    root_id: str | None = Field(
        default=None, description="Root message ID for thread reconstruction"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional attributes")


class ArtifactRef(BaseModel):
    """
    Reference to an artifact in the Monoco Artifact Store.

    Attributes:
        hash: Content-addressed hash (sha256:...)
        name: Original filename
        mime_type: MIME type
        size: File size in bytes
        alt_text: Alternative text for images
    """

    hash: str = Field(description="Content hash (sha256:...)")
    name: str | None = Field(default=None, description="Original filename")
    mime_type: str | None = Field(default=None, description="MIME type")
    size: int | None = Field(default=None, description="File size in bytes")
    alt_text: str | None = Field(default=None, description="Alternative text for images")


class CorrelationContext(BaseModel):
    """
    Correlation context for tracking message chains and task associations.

    The correlation_id enables Agent to trace back historical context and
    understand the full conversation lineage.

    Attributes:
        correlation_id: Unique identifier for tracking a specific task chain
        request_id: Request identifier for idempotency
        ref_issue: Associated Issue ID (e.g., FEAT-0189)
        ref_memo: Associated Memo ID
        ref_agent: Agent that handled this message
        chain: List of message IDs in the correlation chain
    """

    correlation_id: str | None = Field(
        default=None, description="Correlation ID for task tracking"
    )
    request_id: str | None = Field(default=None, description="Request ID for idempotency")
    ref_issue: str | None = Field(default=None, description="Associated Issue ID")
    ref_memo: str | None = Field(default=None, description="Associated Memo ID")
    ref_agent: str | None = Field(default=None, description="Handling agent identifier")
    chain: list[str] = Field(default_factory=list, description="Message ID chain")


class InboundMessage(BaseModel):
    """
    Inbound message schema (External -> Monoco).

    This is the standard format for messages written by Courier to
    .monoco/mailbox/inbound/{provider}/.

    Attributes:
        id: Unique message identifier
        provider: Message source provider
        session: Session context
        participants: Sender and recipient information
        timestamp: Message timestamp (ISO8601)
        type: Message content type
        artifacts: Attached artifact references
        correlation: Correlation context for task tracking
        content: Message content (in body, not frontmatter)
    """

    # Core identifiers
    id: str = Field(description="Unique message identifier")
    provider: Provider = Field(description="Message source provider")

    # Context
    session: Session = Field(description="Session context")
    participants: Participants = Field(description="Participant information")

    # Metadata
    timestamp: datetime = Field(description="Message timestamp")
    type: MessageType = Field(default=MessageType.TEXT, description="Message type")

    # Attachments and tracking
    artifacts: list[ArtifactRef] = Field(default_factory=list, description="Artifact references")
    correlation: CorrelationContext = Field(
        default_factory=CorrelationContext, description="Correlation context"
    )

    # Provider-specific extensions
    raw_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific raw data"
    )

    # Content (stored in markdown body, not frontmatter)
    # This field is for programmatic access only
    content: str | None = Field(default=None, exclude=True)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str, info) -> str:
        """Ensure message ID follows naming convention."""
        if "_" not in v:
            raise ValueError(f"Message ID must follow format: {{provider}}_{{uid}}, got: {v}")
        return v


class OutboundMessage(BaseModel):
    """
    Outbound message schema (Monoco -> External).

    This is the format for messages written to
    .monoco/mailbox/outbound/{provider}/ by the CLI.

    Attributes:
        id: Unique message identifier (assigned by CLI)
        reply_to: Reference to original message being replied to
        provider: Target provider
        delivery_method: How to deliver the message
        session: Target session context
        participants: Target recipients
        timestamp: Creation timestamp
        type: Message content type
        artifacts: Attached artifact references
        correlation: Correlation context
        template: Template ID for interactive cards
    """

    # Core identifiers
    id: str | None = Field(default=None, description="Message ID (assigned on submit)")
    reply_to: str | None = Field(
        default=None, description="Original message ID being replied to"
    )
    thread_to: str | None = Field(
        default=None, description="Thread key for continuing a conversation"
    )

    # Target
    provider: Provider = Field(description="Target provider")
    delivery_method: DeliveryMethod = Field(
        default=DeliveryMethod.REPLY, description="Delivery method"
    )

    # Context
    session: Session | None = Field(default=None, description="Target session")
    participants: Participants | None = Field(default=None, description="Target recipients")

    # Content
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: MessageType = Field(default=MessageType.TEXT)

    # Attachments
    artifacts: list[ArtifactRef] = Field(default_factory=list)

    # Tracking
    correlation: CorrelationContext = Field(default_factory=CorrelationContext)

    # Interactive content
    template: str | None = Field(default=None, description="Card template ID")
    template_data: dict[str, Any] = Field(default_factory=dict, description="Template variables")

    # Content (stored in markdown body)
    content: str | None = Field(default=None, exclude=True)


class DraftMessage(BaseModel):
    """
    Draft message schema for Agent workspace.

    Agents write drafts in their workspace (e.g., Issues/Features/work/drafts/),
    then use `monoco courier send <file>` to submit.

    Drafts have a simplified schema - the CLI will enrich them on submission.

    Attributes:
        to: Target recipient (user-friendly identifier)
        reply_to: Message being replied to
        provider: Target provider
        msg_type: Message type hint
        artifacts: Artifact references
        priority: Message priority
        draft_version: Schema version
    """

    # Target (can be resolved by CLI)
    to: str | None = Field(default=None, description="Target recipient (@user, email, or channel)")
    reply_to: str | None = Field(default=None, description="Message ID being replied to")
    thread_to: str | None = Field(default=None, description="Thread key for continuing")

    # Provider hint (CLI may override based on config)
    provider: Provider | None = Field(default=None, description="Target provider")

    # Content hints
    msg_type: MessageType = Field(default=MessageType.TEXT, description="Message type")
    artifacts: list[str | ArtifactRef] = Field(
        default_factory=list, description="Artifact hashes or references"
    )

    # Metadata
    priority: Literal["low", "normal", "high", "urgent"] = Field(default="normal")
    draft_version: str = Field(default="1.0", description="Draft schema version")

    # Correlation hints
    ref_issue: str | None = Field(default=None, description="Related Issue ID")
    ref_agent: str | None = Field(default=None, description="Creating agent ID")

    # Content (in markdown body)
    content: str | None = Field(default=None, exclude=True)

    def to_outbound(self) -> OutboundMessage:
        """Convert draft to outbound message (CLI uses this)."""
        correlation = CorrelationContext(
            ref_issue=self.ref_issue,
            ref_agent=self.ref_agent,
        )

        # Handle artifact references
        artifact_refs = []
        for art in self.artifacts:
            if isinstance(art, str):
                artifact_refs.append(ArtifactRef(hash=art))
            else:
                artifact_refs.append(art)

        return OutboundMessage(
            reply_to=self.reply_to,
            thread_to=self.thread_to,
            provider=self.provider or Provider.CUSTOM,
            type=self.msg_type,
            artifacts=artifact_refs,
            correlation=correlation,
        )
