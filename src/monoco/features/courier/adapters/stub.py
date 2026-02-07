"""
Stub Adapter - Placeholder adapter for providers without full implementation.

Can be used for:
- Testing
- Providers not yet implemented
- Fallback behavior
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, AsyncIterator

from monoco.features.connector.protocol.schema import (
    InboundMessage,
    OutboundMessage,
    Provider,
)
from .base import BaseAdapter, AdapterConfig, SendResult, HealthStatus

logger = logging.getLogger("courier.adapters.stub")


class StubAdapter(BaseAdapter):
    """
    Stub adapter that logs messages but doesn't actually send them.

    Useful for testing or when a provider is not configured.
    """

    def __init__(self, config: AdapterConfig, provider: Optional[Provider] = None):
        super().__init__(config)
        self._provider = provider or Provider.DINGTALK
        self._should_succeed = config.__dict__.get("should_succeed", True)
        self._simulated_delay = config.__dict__.get("simulated_delay", 0.0)

    @property
    def provider(self) -> str:
        return self._provider.value

    async def connect(self) -> None:
        """Connect (no-op)."""
        self._connected = True
        logger.debug(f"Stub adapter for {self._provider.value} connected")

    async def disconnect(self) -> None:
        """Disconnect (no-op)."""
        self._connected = False
        logger.debug(f"Stub adapter for {self._provider.value} disconnected")

    async def send(self, message: OutboundMessage) -> SendResult:
        """
        Log the message and return success (or configured failure).

        Args:
            message: The outbound message

        Returns:
            SendResult based on configuration
        """
        if self._simulated_delay > 0:
            import asyncio

            await asyncio.sleep(self._simulated_delay)

        content = message.content.text or message.content.markdown or ""
        preview = content[:100] + "..." if len(content) > 100 else content

        logger.info(
            f"[STUB] Would send to {self._provider.value}: "
            f"to={message.to}, type={message.type.value}, content={preview}"
        )

        if self._should_succeed:
            return SendResult(
                success=True,
                provider_message_id=f"stub_{datetime.utcnow().timestamp()}",
                timestamp=datetime.utcnow(),
            )
        else:
            return SendResult(
                success=False,
                error="Stub adapter configured to fail",
                timestamp=datetime.utcnow(),
            )

    async def health_check(self) -> HealthStatus:
        """Always healthy."""
        return HealthStatus.CONNECTED if self._connected else HealthStatus.DISCONNECTED

    async def listen(self) -> AsyncIterator[InboundMessage]:
        """No-op listener."""
        return
        yield  # Make it an async generator


class LarkAdapter(StubAdapter):
    """Lark/Feishu adapter (stub)."""

    def __init__(self, config: AdapterConfig):
        super().__init__(config, Provider.LARK)


class EmailAdapter(StubAdapter):
    """Email adapter (stub)."""

    def __init__(self, config: AdapterConfig):
        super().__init__(config, Provider.EMAIL)


class SlackAdapter(StubAdapter):
    """Slack adapter (stub)."""

    def __init__(self, config: AdapterConfig):
        super().__init__(config, Provider.SLACK)


class TeamsAdapter(StubAdapter):
    """Microsoft Teams adapter (stub)."""

    def __init__(self, config: AdapterConfig):
        super().__init__(config, Provider.TEAMS)


class WeComAdapter(StubAdapter):
    """WeCom/WeChat Work adapter (stub)."""

    def __init__(self, config: AdapterConfig):
        super().__init__(config, Provider.WECOM)
