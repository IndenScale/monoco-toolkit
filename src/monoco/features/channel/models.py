"""
Channel Configuration Models - Data models for unified channel management.

This module provides:
- ChannelType: Enum for supported channel types
- BaseChannel: Abstract base for all channel configurations
- DingtalkChannel: DingTalk webhook configuration
- LarkChannel: Lark/Feishu webhook configuration
- EmailChannel: SMTP email configuration
- ChannelManager: Management interface for channels
"""

import hashlib
import secrets
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class ChannelType(str, Enum):
    """Supported channel types."""

    DINGTALK = "dingtalk"
    LARK = "lark"
    EMAIL = "email"


class ChannelStatus(str, Enum):
    """Channel operational status."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class BaseChannel(BaseModel, ABC):
    """Abstract base class for all channel configurations."""

    id: str = Field(..., description="Unique identifier for the channel")
    name: str = Field(..., description="Display name for the channel")
    type: ChannelType = Field(..., description="Channel type")
    enabled: bool = Field(default=True, description="Whether the channel is enabled")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate channel ID format."""
        if not v:
            raise ValueError("Channel ID cannot be empty")
        if not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError("Channel ID can only contain alphanumeric, hyphen, and underscore")
        return v

    @abstractmethod
    def get_provider_type(self) -> str:
        """Return the provider type identifier."""
        pass

    @abstractmethod
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test the channel connection.

        Returns:
            Tuple of (success, error_message)
        """
        pass

    @abstractmethod
    def to_sender_config(self) -> Dict[str, Any]:
        """
        Convert to sender configuration dict for Courier.

        Returns:
            Configuration dict for sending messages
        """
        pass

    def model_dump_encrypted(self) -> Dict[str, Any]:
        """
        Dump model with sensitive fields encrypted.

        Returns:
            Dict with encrypted sensitive fields
        """
        data = self.model_dump(mode="json")
        # Subclasses should override to encrypt sensitive fields
        return data

    @classmethod
    def model_load_encrypted(cls, data: Dict[str, Any]) -> "BaseChannel":
        """
        Load model with encrypted fields decrypted.

        Args:
            data: Dict potentially containing encrypted fields

        Returns:
            Decoded channel instance
        """
        # Subclasses should override to decrypt sensitive fields
        return cls(**data)


class DingtalkChannel(BaseChannel):
    """DingTalk channel configuration (supports both Webhook and Flow modes)."""

    type: ChannelType = Field(default=ChannelType.DINGTALK, frozen=True)
    
    # Webhook mode fields (legacy)
    webhook_url: str = Field(default="", description="DingTalk webhook URL (for webhook mode)")
    keywords: str = Field(default="", description="DingTalk bot keywords")
    secret: str = Field(default="", description="DingTalk bot secret for signature")
    
    # Flow mode fields
    client_id: str = Field(default="", description="DingTalk Client ID / App Key (for Flow mode)")
    client_secret: str = Field(default="", description="DingTalk Client Secret / App Secret (for Flow mode)")
    robot_code: str = Field(default="", description="DingTalk Robot Code for sending (for Flow mode)")

    @model_validator(mode="after")
    def validate_config(self) -> "DingtalkChannel":
        """Validate that at least one mode is configured."""
        has_webhook = self.webhook_url and self.webhook_url.startswith("https://oapi.dingtalk.com/robot/send")
        has_flow = self.client_id and self.client_secret
        
        if not has_webhook and not has_flow:
            raise ValueError("Either webhook_url (webhook mode) or client_id + client_secret (Flow mode) must be configured")
        
        return self

    def get_provider_type(self) -> str:
        return "dingtalk"

    def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test DingTalk webhook by sending a test message."""
        import requests

        try:
            # Send a simple test message
            payload = {
                "msgtype": "text",
                "text": {"content": "Channel test message from Monoco"},
            }

            # Add signature if secret is configured
            if self.secret:
                import base64
                import hmac
                import time

                timestamp = str(int(time.time() * 1000))
                string_to_sign = f"{timestamp}\n{self.secret}"
                hmac_code = hmac.new(
                    self.secret.encode("utf-8"),
                    string_to_sign.encode("utf-8"),
                    digestmod=hashlib.sha256,
                ).digest()
                sign = base64.b64encode(hmac_code).decode("utf-8")

                url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
            else:
                url = self.webhook_url

            response = requests.post(url, json=payload, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                return True, None
            else:
                return False, f"DingTalk API error: {result.get('errmsg')}"

        except requests.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Test failed: {str(e)}"

    def to_sender_config(self) -> Dict[str, Any]:
        """Convert to sender configuration."""
        config = {
            "provider": "dingtalk",
            "webhook_url": self.webhook_url,
            "keywords": self.keywords,
            "secret": self.secret,
        }
        
        # Add Flow mode fields if configured
        if self.client_id:
            config["client_id"] = self.client_id
        if self.client_secret:
            config["client_secret"] = self.client_secret
        if self.robot_code:
            config["robot_code"] = self.robot_code
            
        return config
    
    def is_flow_mode(self) -> bool:
        """Check if channel is configured for Flow mode."""
        return bool(self.client_id and self.client_secret)


class LarkChannel(BaseChannel):
    """Lark/Feishu webhook channel configuration."""

    type: ChannelType = Field(default=ChannelType.LARK, frozen=True)
    webhook_url: str = Field(..., description="Lark webhook URL")
    secret: str = Field(default="", description="Lark bot secret for signature")

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str) -> str:
        """Validate webhook URL format."""
        if not v.startswith("https://open.feishu.cn/open-apis/bot/v2/hook/"):
            raise ValueError("Invalid Lark webhook URL")
        return v

    def get_provider_type(self) -> str:
        return "lark"

    def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test Lark webhook by sending a test message."""
        import requests

        try:
            # Send a simple test message
            payload = {
                "msg_type": "text",
                "content": {"text": "Channel test message from Monoco"},
            }

            # Add signature if secret is configured
            if self.secret:
                import base64
                import hashlib
                import time

                timestamp = str(int(time.time()))
                string_to_sign = f"{timestamp}\n{self.secret}"
                hmac_code = hmac.new(
                    string_to_sign.encode("utf-8"),
                    digestmod=hashlib.sha256,
                ).digest()
                sign = base64.b64encode(hmac_code).decode("utf-8")

                headers = {"X-Lark-Request-Timestamp": timestamp, "X-Lark-Request-Signature": sign}
            else:
                headers = {}

            response = requests.post(self.webhook_url, json=payload, headers=headers, timeout=10)
            result = response.json()

            if result.get("code") == 0:
                return True, None
            else:
                return False, f"Lark API error: {result.get('msg')}"

        except requests.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Test failed: {str(e)}"

    def to_sender_config(self) -> Dict[str, Any]:
        """Convert to sender configuration."""
        return {
            "provider": "lark",
            "webhook_url": self.webhook_url,
            "secret": self.secret,
        }


class EmailChannel(BaseChannel):
    """SMTP email channel configuration."""

    type: ChannelType = Field(default=ChannelType.EMAIL, frozen=True)
    smtp_host: str = Field(..., description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    username: str = Field(..., description="SMTP username")
    password: str = Field(..., description="SMTP password")
    use_tls: bool = Field(default=True, description="Use TLS encryption")
    use_ssl: bool = Field(default=False, description="Use SSL connection")
    from_address: Optional[str] = Field(default=None, description="From email address")
    to_addresses: List[str] = Field(default_factory=list, description="Default recipient addresses")

    @model_validator(mode="after")
    def validate_email_config(self) -> "EmailChannel":
        """Validate email configuration."""
        if self.smtp_port < 1 or self.smtp_port > 65535:
            raise ValueError("Invalid SMTP port")
        if not self.username:
            raise ValueError("SMTP username is required")
        if not self.password:
            raise ValueError("SMTP password is required")
        return self

    def get_provider_type(self) -> str:
        return "email"

    def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test SMTP connection."""
        import smtplib

        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)

            if self.use_tls and not self.use_ssl:
                server.starttls()

            server.login(self.username, self.password)
            server.quit()
            return True, None

        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed - check username and password"
        except smtplib.SMTPConnectError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Test failed: {str(e)}"

    def to_sender_config(self) -> Dict[str, Any]:
        """Convert to sender configuration."""
        return {
            "provider": "email",
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "username": self.username,
            "password": self.password,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "from_address": self.from_address or self.username,
            "to_addresses": self.to_addresses,
        }


# Union type for all channel types
Channel = Union[DingtalkChannel, LarkChannel, EmailChannel]


class ChannelDefaults(BaseModel):
    """Default channel configuration."""

    send: Optional[str] = Field(default=None, description="Default channel for sending")
    receive: List[str] = Field(default_factory=list, description="Default channels for receiving")


class ChannelsConfig(BaseModel):
    """Root configuration for all channels."""

    version: str = Field(default="1.0", description="Configuration version")
    channels: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict, description="Channels grouped by type"
    )
    defaults: ChannelDefaults = Field(
        default_factory=ChannelDefaults, description="Default channel settings"
    )

    @model_validator(mode="after")
    def validate_version(self) -> "ChannelsConfig":
        """Validate configuration version."""
        if not self.version.startswith("1."):
            raise ValueError(f"Unsupported configuration version: {self.version}")
        return self


class ChannelTestResult(BaseModel):
    """Result of channel connection test."""

    channel_id: str
    success: bool
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float] = None


class ChannelSendResult(BaseModel):
    """Result of sending message through channel."""

    channel_id: str
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
