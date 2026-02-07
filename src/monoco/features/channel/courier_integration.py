"""
Courier Integration - Bridge between Courier and Channel systems.

This module provides:
- ChannelAdapter: Courier adapter that uses Channel configuration
- Outbound message processing through configured channels
"""

import logging
from typing import Any, Dict, List, Optional

from monoco.features.connector.protocol.schema import OutboundMessage

from .models import BaseChannel, ChannelSendResult
from .sender import ChannelSender
from .store import get_channel_store

logger = logging.getLogger(__name__)


class ChannelCourierAdapter:
    """
    Adapter for Courier to send messages through Channel configuration.

    This adapter bridges the Courier message queue system with the
    Channel configuration management system.
    """

    def __init__(self):
        self.sender = ChannelSender()
        self.store = get_channel_store()

    def send_to_channel(
        self,
        channel_id: str,
        message: str,
        title: Optional[str] = None,
        markdown: bool = False,
    ) -> ChannelSendResult:
        """
        Send a message to a specific channel by ID.

        Args:
            channel_id: Channel identifier
            message: Message content
            title: Optional title
            markdown: Whether to use markdown formatting

        Returns:
            Send result
        """
        channel = self.store.get(channel_id)
        if not channel:
            return ChannelSendResult(
                channel_id=channel_id,
                success=False,
                error=f"Channel '{channel_id}' not found",
            )

        if not channel.enabled:
            return ChannelSendResult(
                channel_id=channel_id,
                success=False,
                error=f"Channel '{channel_id}' is disabled",
            )

        return self.sender.send(channel, message, title=title, markdown=markdown)

    def send_to_default(self, message: str, title: Optional[str] = None, markdown: bool = False) -> ChannelSendResult:
        """
        Send a message to the default send channel.

        Args:
            message: Message content
            title: Optional title
            markdown: Whether to use markdown formatting

        Returns:
            Send result
        """
        default = self.store.get_default_send()
        if not default:
            return ChannelSendResult(
                channel_id="default",
                success=False,
                error="No default send channel configured",
            )

        return self.sender.send(default, message, title=title, markdown=markdown)

    def send_outbound_message(self, message: OutboundMessage) -> ChannelSendResult:
        """
        Send an OutboundMessage from the Courier system.

        Args:
            message: OutboundMessage from Courier

        Returns:
            Send result
        """
        # Extract channel ID from message metadata if available
        channel_id = message.metadata.get("channel_id") if message.metadata else None

        if channel_id:
            return self.send_to_channel(
                channel_id=channel_id,
                message=message.content.text or "",
                title=message.content.markdown,
            )
        else:
            # Use default channel
            return self.send_to_default(
                message=message.content.text or "",
                title=message.content.markdown,
            )

    def get_available_channels(self) -> List[Dict[str, Any]]:
        """
        Get list of available channels for sending.

        Returns:
            List of channel info dicts
        """
        channels = []
        for channel in self.store.list_all():
            if channel.enabled:
                channels.append({
                    "id": channel.id,
                    "name": channel.name,
                    "type": channel.type.value,
                    "provider": channel.get_provider_type(),
                })
        return channels

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all channels.

        Returns:
            Health status dict
        """
        results = []
        for channel in self.store.list_all():
            if channel.enabled:
                success, error = channel.test_connection()
                results.append({
                    "id": channel.id,
                    "name": channel.name,
                    "type": channel.type.value,
                    "status": "healthy" if success else "error",
                    "error": error,
                })

        return {
            "total_channels": len(self.store.list_all()),
            "enabled_channels": len([c for c in self.store.list_all() if c.enabled]),
            "healthy_channels": len([r for r in results if r["status"] == "healthy"]),
            "channels": results,
        }


# Global adapter instance
_adapter: Optional[ChannelCourierAdapter] = None


def get_channel_adapter() -> ChannelCourierAdapter:
    """Get the global channel adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = ChannelCourierAdapter()
    return _adapter
