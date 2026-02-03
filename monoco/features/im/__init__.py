"""
IM (Instant Messaging) Infrastructure (FEAT-0167).

Provides core data models, storage, and routing for IM system integration.

Example:
    >>> from monoco.features.im import IMManager
    >>> im = IMManager(project_root)
    >>> channel = im.channels.create_channel("group123", PlatformType.FEISHU, name="Test Group")
    >>> message = IMMessage(message_id="msg1", channel_id="group123", ...)
    >>> im.messages.save_message(message)
"""

from .models import (
    PlatformType,
    ChannelType,
    MessageStatus,
    ParticipantType,
    ContentType,
    IMParticipant,
    Attachment,
    MessageContent,
    ProcessingStep,
    IMMessage,
    IMChannel,
    IMAgentSession,
    IMWebhookConfig,
    IMStats,
)

from .core import (
    IMManager,
    IMChannelManager,
    MessageStore,
    IMRouter,
    IMAgentSessionManager,
    IMStorageError,
    ChannelNotFoundError,
    MessageNotFoundError,
)

__all__ = [
    # Models
    "PlatformType",
    "ChannelType",
    "MessageStatus",
    "ParticipantType",
    "ContentType",
    "IMParticipant",
    "Attachment",
    "MessageContent",
    "ProcessingStep",
    "IMMessage",
    "IMChannel",
    "IMAgentSession",
    "IMWebhookConfig",
    "IMStats",
    # Core
    "IMManager",
    "IMChannelManager",
    "MessageStore",
    "IMRouter",
    "IMAgentSessionManager",
    "IMStorageError",
    "ChannelNotFoundError",
    "MessageNotFoundError",
]
