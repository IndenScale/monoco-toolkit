"""
DingTalk Outbound Adapter - Sends messages to DingTalk.

Supports:
- Text messages
- Markdown messages
- Card messages (limited)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from monoco.features.connector.protocol.schema import (
    ContentType,
    OutboundMessage,
    Provider,
)

from .base import AdapterConfig, BaseAdapter, HealthStatus, SendResult

logger = logging.getLogger("courier.adapters.dingtalk_outbound")


class DingTalkOutboundAdapter(BaseAdapter):
    """
    DingTalk outbound message adapter.

    Uses DingTalk Bot Webhook API to send messages.
    Requires webhook URL with access token.
    """

    API_BASE = "https://oapi.dingtalk.com"

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.webhook_url: Optional[str] = None
        self.secret: Optional[str] = None
        self._access_token: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def provider(self) -> str:
        return Provider.DINGTALK.value

    def _extract_token_from_url(self, url: str) -> Optional[str]:
        """Extract access token from webhook URL."""
        # URL format: https://oapi.dingtalk.com/robot/send?access_token=xxx
        import urllib.parse

        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        tokens = params.get("access_token", [])
        return tokens[0] if tokens else None

    async def connect(self) -> None:
        """Initialize connection."""
        # Get webhook URL from config or environment
        self.webhook_url = self.config.__dict__.get("webhook_url")
        self.secret = self.config.__dict__.get("secret")

        if not self.webhook_url:
            import os

            self.webhook_url = os.environ.get("DINGTALK_WEBHOOK_URL")
            self.secret = os.environ.get("DINGTALK_WEBHOOK_SECRET")

        if self.webhook_url:
            self._access_token = self._extract_token_from_url(self.webhook_url)

        self._http_client = httpx.AsyncClient(timeout=30.0)
        self._connected = True

        logger.info("DingTalk outbound adapter connected")

    async def disconnect(self) -> None:
        """Close connection."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        self._connected = False
        logger.info("DingTalk outbound adapter disconnected")

    def _generate_sign(self, timestamp: str) -> str:
        """Generate signature for DingTalk webhook."""
        import base64
        import hashlib
        import hmac

        if not self.secret:
            return ""

        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    def _build_payload(self, message: OutboundMessage) -> Dict[str, Any]:
        """Build DingTalk API payload from OutboundMessage."""
        content = message.content

        if message.type == ContentType.MARKDOWN and content.markdown:
            return {
                "msgtype": "markdown",
                "markdown": {"title": "Message", "text": content.markdown},
            }
        elif message.type == ContentType.TEXT or content.text:
            return {
                "msgtype": "text",
                "text": {"content": content.text or ""},
            }
        elif message.type == ContentType.CARD and content.card:
            # Limited card support
            return {
                "msgtype": "action_card",
                "action_card": content.card,
            }
        else:
            # Default to text
            text = content.text or content.markdown or ""
            return {
                "msgtype": "text",
                "text": {"content": text},
            }

    async def send(self, message: OutboundMessage) -> SendResult:
        """
        Send a message to DingTalk.

        Args:
            message: The outbound message

        Returns:
            SendResult with success/failure information
        """
        if not self._connected or not self._http_client:
            return SendResult(
                success=False,
                error="Adapter not connected",
                timestamp=datetime.now(timezone.utc),
            )

        if not self.webhook_url:
            return SendResult(
                success=False,
                error="DingTalk webhook URL not configured",
                timestamp=datetime.now(timezone.utc),
            )

        try:
            import time

            timestamp = str(int(time.time() * 1000))
            sign = self._generate_sign(timestamp)

            # Build URL with signature
            url = self.webhook_url
            if self.secret and sign:
                url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

            payload = self._build_payload(message)

            # Add at info if specified in options
            at_mobiles = message.options.get("at_mobiles", [])
            at_user_ids = message.options.get("at_user_ids", [])
            is_at_all = message.options.get("is_at_all", False)

            if at_mobiles or at_user_ids or is_at_all:
                payload["at"] = {
                    "atMobiles": at_mobiles,
                    "atUserIds": at_user_ids,
                    "isAtAll": is_at_all,
                }

            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()

            if result.get("errcode") == 0:
                return SendResult(
                    success=True,
                    provider_message_id=result.get("message_id"),
                    timestamp=datetime.now(timezone.utc),
                )
            else:
                return SendResult(
                    success=False,
                    error=f"DingTalk API error: {result.get('errmsg', 'Unknown error')}",
                    timestamp=datetime.now(timezone.utc),
                )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending to DingTalk: {e}")
            return SendResult(
                success=False,
                error=f"HTTP error: {str(e)}",
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.exception(f"Error sending to DingTalk: {e}")
            return SendResult(
                success=False,
                error=f"Send error: {str(e)}",
                timestamp=datetime.now(timezone.utc),
            )

    async def health_check(self) -> HealthStatus:
        """Check adapter health."""
        if not self._connected:
            return HealthStatus.DISCONNECTED
        if not self.webhook_url:
            return HealthStatus.DISABLED
        return HealthStatus.CONNECTED

    async def listen(self):
        """Not implemented for outbound-only adapter."""
        raise NotImplementedError(
            "DingTalk outbound adapter does not support listening"
        )
