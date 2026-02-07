"""
Channel Management Feature - Unified channel configuration management.

This feature provides centralized management of notification channels:
- DingTalk webhook channels
- Lark/Feishu webhook channels  
- SMTP email channels

Usage:
    from monoco.features.channel import get_channel_store, ChannelSender
    
    # Get channel store
    store = get_channel_store()
    
    # List all channels
    channels = store.list_all()
    
    # Send message
    sender = ChannelSender()
    result = sender.send(channel, "Hello!")
"""

from .models import (
    BaseChannel,
    Channel,
    ChannelDefaults,
    ChannelSendResult,
    ChannelStatus,
    ChannelTestResult,
    ChannelType,
    DingtalkChannel,
    EmailChannel,
    LarkChannel,
)
from .sender import ChannelSender
from .store import get_channel_store, reset_channel_store

__all__ = [
    # Models
    "BaseChannel",
    "Channel",
    "ChannelDefaults",
    "ChannelSendResult",
    "ChannelStatus",
    "ChannelTestResult",
    "ChannelType",
    "DingtalkChannel",
    "EmailChannel",
    "LarkChannel",
    # Core classes
    "ChannelSender",
    "get_channel_store",
    "reset_channel_store",
]
