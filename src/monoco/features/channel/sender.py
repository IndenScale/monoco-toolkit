"""
Channel Sender - Message sending through configured channels.

This module provides:
- ChannelSender: Send messages through various channel types
- Message formatting for different providers
"""

import hashlib
import logging
from typing import Any, Dict, Optional

from .models import (
    BaseChannel,
    ChannelSendResult,
    DingtalkChannel,
    EmailChannel,
    LarkChannel,
)

logger = logging.getLogger(__name__)


class ChannelSender:
    """
    Message sender for notification channels.

    Handles message formatting and delivery through different
    channel types (DingTalk, Lark, Email).
    """

    def send(
        self,
        channel: BaseChannel,
        message: str,
        title: Optional[str] = None,
        markdown: bool = False,
        **kwargs: Any,
    ) -> ChannelSendResult:
        """
        Send a message through a channel.

        Args:
            channel: Channel to send through
            message: Message content
            title: Optional title (for markdown messages)
            markdown: Whether to send as markdown
            **kwargs: Additional provider-specific options

        Returns:
            Send result with success status
        """
        if not channel.enabled:
            return ChannelSendResult(
                channel_id=channel.id,
                success=False,
                error="Channel is disabled",
            )

        try:
            if isinstance(channel, DingtalkChannel):
                return self._send_dingtalk(channel, message, title, markdown, **kwargs)
            elif isinstance(channel, LarkChannel):
                return self._send_lark(channel, message, title, markdown, **kwargs)
            elif isinstance(channel, EmailChannel):
                return self._send_email(channel, message, title, **kwargs)
            else:
                return ChannelSendResult(
                    channel_id=channel.id,
                    success=False,
                    error=f"Unsupported channel type: {channel.type}",
                )
        except Exception as e:
            logger.exception(f"Failed to send message through {channel.id}")
            return ChannelSendResult(
                channel_id=channel.id,
                success=False,
                error=str(e),
            )

    def _send_dingtalk(
        self,
        channel: DingtalkChannel,
        message: str,
        title: Optional[str] = None,
        markdown: bool = False,
        **kwargs: Any,
    ) -> ChannelSendResult:
        """Send message through DingTalk webhook."""
        import requests

        # Build payload
        if markdown or title:
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title or message[:20],
                    "text": message if markdown else f"## {title}\n\n{message}",
                },
            }
        else:
            payload = {
                "msgtype": "text",
                "text": {"content": message},
            }

        # Add keywords if configured
        if channel.keywords and not markdown:
            if channel.keywords not in message:
                payload["text"]["content"] = f"[{channel.keywords}] {message}"

        # Build URL with signature if secret is configured
        url = channel.webhook_url
        if channel.secret:
            import base64
            import hmac
            import time

            timestamp = str(int(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{channel.secret}"
            hmac_code = hmac.new(
                channel.secret.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
            sign = base64.b64encode(hmac_code).decode("utf-8")
            url = f"{url}&timestamp={timestamp}&sign={sign}"

        # Send request
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()

        if result.get("errcode") == 0:
            return ChannelSendResult(
                channel_id=channel.id,
                success=True,
                message_id=result.get("message_id"),
            )
        else:
            return ChannelSendResult(
                channel_id=channel.id,
                success=False,
                error=f"DingTalk API error: {result.get('errmsg')}",
            )

    def _send_lark(
        self,
        channel: LarkChannel,
        message: str,
        title: Optional[str] = None,
        markdown: bool = False,
        **kwargs: Any,
    ) -> ChannelSendResult:
        """Send message through Lark webhook."""
        import requests

        # Build payload
        if markdown or title:
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": title or "Message",
                        }
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md" if markdown else "plain_text",
                                "content": message,
                            },
                        }
                    ],
                },
            }
        else:
            payload = {
                "msg_type": "text",
                "content": {"text": message},
            }

        # Build headers with signature if secret is configured
        headers: Dict[str, str] = {}
        if channel.secret:
            import base64
            import hashlib
            import time

            timestamp = str(int(time.time()))
            string_to_sign = f"{timestamp}\n{channel.secret}"
            hmac_code = hmac.new(
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
            sign = base64.b64encode(hmac_code).decode("utf-8")

            headers["X-Lark-Request-Timestamp"] = timestamp
            headers["X-Lark-Request-Signature"] = sign

        # Send request
        response = requests.post(channel.webhook_url, json=payload, headers=headers, timeout=30)
        result = response.json()

        if result.get("code") == 0:
            return ChannelSendResult(
                channel_id=channel.id,
                success=True,
                message_id=result.get("data", {}).get("message_id"),
            )
        else:
            return ChannelSendResult(
                channel_id=channel.id,
                success=False,
                error=f"Lark API error: {result.get('msg')}",
            )

    def _send_email(
        self,
        channel: EmailChannel,
        message: str,
        title: Optional[str] = None,
        **kwargs: Any,
    ) -> ChannelSendResult:
        """Send message through SMTP."""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # Build message
        msg = MIMEMultipart()
        msg["From"] = channel.from_address or channel.username

        # Get recipients
        to_addresses = kwargs.get("to_addresses", channel.to_addresses)
        if not to_addresses:
            return ChannelSendResult(
                channel_id=channel.id,
                success=False,
                error="No recipient addresses configured",
            )

        msg["To"] = ", ".join(to_addresses)
        msg["Subject"] = title or "Message from Monoco"

        # Attach body
        msg.attach(MIMEText(message, "plain", "utf-8"))

        # Send via SMTP
        if channel.use_ssl:
            server = smtplib.SMTP_SSL(channel.smtp_host, channel.smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(channel.smtp_host, channel.smtp_port, timeout=30)

        try:
            if channel.use_tls and not channel.use_ssl:
                server.starttls()

            server.login(channel.username, channel.password)
            server.sendmail(
                channel.from_address or channel.username,
                to_addresses,
                msg.as_string(),
            )
            server.quit()

            return ChannelSendResult(
                channel_id=channel.id,
                success=True,
                message_id=hashlib.sha256(message.encode()).hexdigest()[:16],
            )

        except Exception as e:
            return ChannelSendResult(
                channel_id=channel.id,
                success=False,
                error=str(e),
            )
