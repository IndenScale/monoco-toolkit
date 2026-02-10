"""
Channel Configuration Store - Storage layer for channel configurations.

This module provides:
- ChannelStore: YAML-based storage for channel configurations
- Encryption helpers for sensitive fields
- Channel loading and saving operations
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml

from .models import (
    BaseChannel,
    ChannelDefaults,
    ChannelsConfig,
    ChannelType,
    DingtalkChannel,
    EmailChannel,
    LarkChannel,
)

logger = logging.getLogger(__name__)

# Channel type mapping
CHANNEL_TYPE_MAP: Dict[ChannelType, Type[BaseChannel]] = {
    ChannelType.DINGTALK: DingtalkChannel,
    ChannelType.LARK: LarkChannel,
    ChannelType.EMAIL: EmailChannel,
}


class ChannelStore:
    """
    YAML-based storage for channel configurations.

    Stores configuration in ~/.monoco/channels.yaml with optional
    encryption for sensitive fields.
    """

    CONFIG_FILENAME = "channels.yaml"
    CONFIG_VERSION = "1.0"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the channel store.

        Args:
            config_path: Path to the configuration file.
                        Defaults to ~/.monoco/channels.yaml
        """
        if config_path is None:
            config_path = Path.home() / ".monoco" / self.CONFIG_FILENAME

        self.config_path = config_path
        self._config: Optional[ChannelsConfig] = None
        self._channels: Dict[str, BaseChannel] = {}

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_raw_config(self) -> Dict[str, Any]:
        """Load raw configuration from file."""
        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load channel config: {e}")
            return {}

    def _save_raw_config(self, data: Dict[str, Any]) -> None:
        """Save raw configuration to file."""
        self._ensure_config_dir()

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.error(f"Failed to save channel config: {e}")
            raise

    def _deserialize_channel(self, data: Dict[str, Any]) -> Optional[BaseChannel]:
        """
        Deserialize a channel from dict.

        Args:
            data: Channel configuration dict

        Returns:
            Deserialized channel or None if invalid
        """
        try:
            channel_type = data.get("type")
            if not channel_type:
                logger.warning("Channel missing type field")
                return None

            channel_class = CHANNEL_TYPE_MAP.get(ChannelType(channel_type))
            if not channel_class:
                logger.warning(f"Unknown channel type: {channel_type}")
                return None

            return channel_class.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to deserialize channel: {e}")
            return None

    def _serialize_channel(self, channel: BaseChannel) -> Dict[str, Any]:
        """
        Serialize a channel to dict.

        Args:
            channel: Channel to serialize

        Returns:
            Serialized channel dict
        """
        return channel.model_dump(mode="json")

    def load(self) -> "ChannelStore":
        """
        Load configuration from file.

        Returns:
            Self for chaining
        """
        raw_data = self._load_raw_config()

        if not raw_data:
            # Create empty config
            self._config = ChannelsConfig(version=self.CONFIG_VERSION)
            self._channels = {}
            return self

        try:
            self._config = ChannelsConfig.model_validate(raw_data)
        except Exception as e:
            logger.error(f"Failed to validate config: {e}")
            # Create empty config on validation error
            self._config = ChannelsConfig(version=self.CONFIG_VERSION)

        # Deserialize channels
        self._channels = {}
        for channel_type, channel_list in self._config.channels.items():
            for channel_data in channel_list:
                channel = self._deserialize_channel(channel_data)
                if channel:
                    self._channels[channel.id] = channel

        return self

    def save(self) -> None:
        """Save current configuration to file."""
        if self._config is None:
            self._config = ChannelsConfig(version=self.CONFIG_VERSION)

        # Serialize channels grouped by type
        channels_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for channel in self._channels.values():
            type_key = channel.type.value
            if type_key not in channels_by_type:
                channels_by_type[type_key] = []
            channels_by_type[type_key].append(self._serialize_channel(channel))

        self._config.channels = channels_by_type

        # Save to file
        raw_data = self._config.model_dump(mode="json")
        self._save_raw_config(raw_data)

    def get(self, channel_id: str) -> Optional[BaseChannel]:
        """
        Get a channel by ID.

        Args:
            channel_id: Channel identifier

        Returns:
            Channel or None if not found
        """
        return self._channels.get(channel_id)

    def list_all(self) -> List[BaseChannel]:
        """
        List all channels.

        Returns:
            List of all channels
        """
        return list(self._channels.values())

    def list_by_type(self, channel_type: ChannelType) -> List[BaseChannel]:
        """
        List channels by type.

        Args:
            channel_type: Type of channels to list

        Returns:
            List of matching channels
        """
        return [c for c in self._channels.values() if c.type == channel_type]

    def add(self, channel: BaseChannel) -> None:
        """
        Add or update a channel.

        Args:
            channel: Channel to add

        Raises:
            ValueError: If channel ID already exists
        """
        from datetime import datetime, timezone

        if channel.id in self._channels:
            # Update existing channel
            channel.updated_at = datetime.now(timezone.utc)
        else:
            # New channel
            channel.created_at = datetime.now(timezone.utc)

        self._channels[channel.id] = channel
        self.save()

    def remove(self, channel_id: str) -> bool:
        """
        Remove a channel.

        Args:
            channel_id: Channel identifier

        Returns:
            True if removed, False if not found
        """
        if channel_id not in self._channels:
            return False

        del self._channels[channel_id]
        self.save()
        return True

    def update(self, channel_id: str, **updates: Any) -> Optional[BaseChannel]:
        """
        Update a channel's properties.

        Args:
            channel_id: Channel identifier
            **updates: Properties to update

        Returns:
            Updated channel or None if not found
        """
        channel = self._channels.get(channel_id)
        if not channel:
            return None

        from datetime import datetime, timezone

        # Update allowed fields
        allowed_fields = {"name", "enabled", "metadata"}

        # Type-specific fields
        if isinstance(channel, DingtalkChannel):
            allowed_fields.update({"webhook_url", "keywords", "secret"})
        elif isinstance(channel, LarkChannel):
            allowed_fields.update({"webhook_url", "secret"})
        elif isinstance(channel, EmailChannel):
            allowed_fields.update(
                {
                    "smtp_host",
                    "smtp_port",
                    "username",
                    "password",
                    "use_tls",
                    "use_ssl",
                    "from_address",
                    "to_addresses",
                }
            )

        for key, value in updates.items():
            if key in allowed_fields and hasattr(channel, key):
                setattr(channel, key, value)

        channel.updated_at = datetime.now(timezone.utc)
        self.save()
        return channel

    def get_default_send(self) -> Optional[BaseChannel]:
        """
        Get the default channel for sending.

        Returns:
            Default send channel or None
        """
        if not self._config or not self._config.defaults.send:
            return None
        return self._channels.get(self._config.defaults.send)

    def get_default_receive(self) -> List[BaseChannel]:
        """
        Get default channels for receiving.

        Returns:
            List of default receive channels
        """
        if not self._config or not self._config.defaults.receive:
            return []
        return [
            self._channels.get(cid)
            for cid in self._config.defaults.receive
            if cid in self._channels
        ]

    def set_defaults(
        self, send: Optional[str] = None, receive: Optional[List[str]] = None
    ) -> None:
        """
        Set default channels.

        Args:
            send: Default channel ID for sending
            receive: List of channel IDs for receiving
        """
        if self._config is None:
            self._config = ChannelsConfig(version=self.CONFIG_VERSION)

        if send is not None:
            self._config.defaults.send = send

        if receive is not None:
            self._config.defaults.receive = receive

        self.save()

    def exists(self, channel_id: str) -> bool:
        """
        Check if a channel exists.

        Args:
            channel_id: Channel identifier

        Returns:
            True if exists, False otherwise
        """
        return channel_id in self._channels

    def count(self) -> int:
        """
        Get total number of channels.

        Returns:
            Number of channels
        """
        return len(self._channels)


# Global store instance
_store: Optional[ChannelStore] = None


def get_channel_store(config_path: Optional[Path] = None) -> ChannelStore:
    """
    Get the global channel store instance.

    Args:
        config_path: Optional path to config file

    Returns:
        ChannelStore instance
    """
    global _store
    if _store is None or config_path is not None:
        _store = ChannelStore(config_path).load()
    return _store


def reset_channel_store() -> None:
    """Reset the global store instance (for testing)."""
    global _store
    _store = None
