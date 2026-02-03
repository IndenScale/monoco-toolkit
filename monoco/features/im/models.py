"""
IM (Instant Messaging) Core Data Models (FEAT-0167).

Defines the core data models for IM system, independent of Memo storage.
Provides foundation for platform adapters and Agent integration.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Literal, Optional, Set
from pydantic import BaseModel, Field


class PlatformType(str, Enum):
    """Supported IM platforms."""
    FEISHU = "feishu"
    DINGTALK = "dingtalk"
    SLACK = "slack"
    DISCORD = "discord"
    WECHAT = "wechat"
    CUSTOM = "custom"


class ChannelType(str, Enum):
    """Types of IM channels."""
    GROUP = "group"
    PRIVATE = "private"
    THREAD = "thread"


class MessageStatus(str, Enum):
    """Status of an IM message in the processing pipeline."""
    RECEIVED = "received"
    ROUTING = "routing"
    AGENT_PROCESSING = "agent_processing"
    REPLIED = "replied"
    ERROR = "error"
    IGNORED = "ignored"


class ParticipantType(str, Enum):
    """Type of participant in a channel."""
    USER = "user"
    AGENT = "agent"
    BOT = "bot"
    SYSTEM = "system"


class ContentType(str, Enum):
    """Types of message content."""
    TEXT = "text"
    IMAGE = "image"
    CARD = "card"
    FILE = "file"
    MIXED = "mixed"
    SYSTEM = "system"


class IMParticipant(BaseModel):
    """
    Represents a participant in an IM channel.
    
    Can be a user, agent, bot, or system.
    """
    participant_id: str = Field(..., description="Unique ID (platform-specific)")
    platform: PlatformType
    participant_type: ParticipantType = ParticipantType.USER
    name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    # Agent-specific fields
    agent_role: Optional[str] = None  # e.g., "engineer", "reviewer", "planner"
    is_admin: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Attachment(BaseModel):
    """
    Represents an attachment in a message.
    
    Can be an image, file, or other media.
    """
    attachment_id: str
    content_type: str  # MIME type
    file_name: str
    file_size: int
    url: Optional[str] = None
    local_path: Optional[str] = None
    # For images
    width: Optional[int] = None
    height: Optional[int] = None
    # Platform-specific raw data
    platform_raw: Dict[str, Any] = Field(default_factory=dict)


class MessageContent(BaseModel):
    """
    Represents the content of an IM message.
    
    Supports rich media including text, images, cards, and files.
    """
    type: ContentType = ContentType.TEXT
    text: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    attachments: List[Attachment] = Field(default_factory=list)
    # For card messages (platform-specific structured content)
    card_data: Optional[Dict[str, Any]] = None
    # Platform-specific raw content
    platform_raw: Dict[str, Any] = Field(default_factory=dict)


class ProcessingStep(BaseModel):
    """
    Represents a step in the message processing pipeline.
    
    Used for tracking message flow and debugging.
    """
    step: str
    status: str  # "started", "completed", "failed"
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IMMessage(BaseModel):
    """
    Represents an IM message.
    
    Core message model with rich content support and processing pipeline tracking.
    Completely independent of Memo model.
    """
    message_id: str = Field(..., description="Unique message ID")
    channel_id: str = Field(..., description="ID of the channel this message belongs to")
    platform: PlatformType
    sender: IMParticipant
    content: MessageContent
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Threading support
    reply_to: Optional[str] = Field(None, description="ID of the message this is replying to")
    thread_id: Optional[str] = Field(None, description="Thread ID for grouped messages")
    
    # Mentions
    mentions: List[str] = Field(default_factory=list, description="List of mentioned participant IDs")
    mention_all: bool = False
    
    # Processing state
    status: MessageStatus = MessageStatus.RECEIVED
    processing_log: List[ProcessingStep] = Field(default_factory=list)
    
    # Optional links to other systems (not required)
    linked_memo_id: Optional[str] = None
    linked_issue_id: Optional[str] = None
    linked_task_id: Optional[str] = None
    
    # Platform-specific raw data
    platform_raw: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        frozen = False


class IMChannel(BaseModel):
    """
    Represents an IM channel (group chat, private chat, or thread).
    
    Contains configuration for agent behavior and project bindings.
    """
    channel_id: str = Field(..., description="Unique channel ID")
    platform: PlatformType
    channel_type: ChannelType = ChannelType.GROUP
    name: Optional[str] = None
    description: Optional[str] = None
    
    # Project binding
    project_binding: Optional[str] = Field(None, description="Path to bound project")
    
    # Context management
    context_window: int = Field(10, description="Number of messages to keep in context")
    context_strategy: Literal["sliding", "summarized", "full"] = "sliding"
    
    # Participants
    participants: List[IMParticipant] = Field(default_factory=list)
    participant_ids: Set[str] = Field(default_factory=set)
    
    # Agent configuration
    auto_reply: bool = True
    default_agent: Optional[str] = Field(None, description="Default agent role for this channel")
    require_mention: bool = True  # Require @mention to trigger agent
    allowed_agents: List[str] = Field(default_factory=list, description="List of allowed agent roles")
    
    # Webhook configuration (platform-specific)
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    platform_raw: Dict[str, Any] = Field(default_factory=dict)
    
    def add_participant(self, participant: IMParticipant) -> None:
        """Add a participant to the channel."""
        if participant.participant_id not in self.participant_ids:
            self.participants.append(participant)
            self.participant_ids.add(participant.participant_id)
    
    def remove_participant(self, participant_id: str) -> None:
        """Remove a participant from the channel."""
        self.participants = [p for p in self.participants if p.participant_id != participant_id]
        self.participant_ids.discard(participant_id)
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()


class IMAgentSession(BaseModel):
    """
    Represents an Agent session bound to an IM channel.
    
    Tracks the interaction between an Agent and an IM channel.
    """
    session_id: str = Field(..., description="Unique session ID")
    channel_id: str = Field(..., description="Associated channel ID")
    agent_role: str = Field(..., description="Agent role (e.g., 'engineer')")
    
    # Session state
    status: Literal["active", "paused", "completed", "error"] = "active"
    
    # Message tracking
    message_ids: List[str] = Field(default_factory=list)
    context_message_count: int = 0
    
    # Linked Monoco entities
    linked_issue_id: Optional[str] = None
    linked_task_id: Optional[str] = None
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    # Session result
    result_summary: Optional[str] = None
    result_artifacts: List[str] = Field(default_factory=list)
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()
    
    def end_session(self, status: Literal["completed", "error"] = "completed") -> None:
        """End the session."""
        self.status = status
        self.ended_at = datetime.now()


class IMWebhookConfig(BaseModel):
    """
    Configuration for platform webhooks.
    
    Stores webhook URLs and secrets for receiving platform events.
    """
    config_id: str
    platform: PlatformType
    channel_id: str
    
    # Webhook settings
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    encrypt_key: Optional[str] = None
    
    # Event filtering
    event_types: List[str] = Field(default_factory=list)
    
    # Status
    is_active: bool = True
    last_verified: Optional[datetime] = None
    error_count: int = 0
    
    # Platform-specific raw config
    platform_raw: Dict[str, Any] = Field(default_factory=dict)


class IMStats(BaseModel):
    """
    Statistics for IM system.
    
    Used for monitoring and health checks.
    """
    total_channels: int = 0
    active_channels: int = 0
    total_messages: int = 0
    messages_today: int = 0
    active_sessions: int = 0
    total_sessions: int = 0
    
    # Platform breakdown
    platform_counts: Dict[PlatformType, int] = Field(default_factory=dict)
    
    # Message status breakdown
    status_counts: Dict[MessageStatus, int] = Field(default_factory=dict)
    
    # Timestamps
    last_updated: datetime = Field(default_factory=datetime.now)
