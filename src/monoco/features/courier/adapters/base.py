"""
Base Adapter - Abstract base class for platform adapters.

All platform adapters must inherit from BaseAdapter and implement
the required methods for sending and receiving messages.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import AsyncIterator, Optional, Dict, Any
from datetime import datetime

from monoco.features.connector.protocol.schema import InboundMessage, OutboundMessage


class HealthStatus(str, Enum):
    """Health status for adapters."""
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class SendResult:
    """Result of a send operation."""
    success: bool
    message_id: Optional[str] = None
    provider_message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class AdapterConfig:
    """Base configuration for adapters."""
    provider: str
    enabled: bool = True
    retry_policy: Optional[Dict[str, Any]] = None


class BaseAdapter(ABC):
    """
    Abstract base class for message platform adapters.

    Adapters are responsible for:
    - Connecting to external platforms
    - Receiving inbound messages
    - Sending outbound messages
    - Health checking
    """

    def __init__(self, config: AdapterConfig):
        self.config = config
        self._connected = False

    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider identifier (e.g., 'lark', 'email')."""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the external platform."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the external platform."""
        pass

    @abstractmethod
    async def listen(self) -> AsyncIterator[InboundMessage]:
        """
        Listen for inbound messages.

        Yields:
            InboundMessage objects as they arrive
        """
        pass

    @abstractmethod
    async def send(self, message: OutboundMessage) -> SendResult:
        """
        Send an outbound message.

        Args:
            message: The outbound message to send

        Returns:
            SendResult with success/failure information
        """
        pass

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """
        Check the health of the adapter connection.

        Returns:
            HealthStatus indicating current state
        """
        pass

    def is_connected(self) -> bool:
        """Check if adapter is currently connected."""
        return self._connected

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
