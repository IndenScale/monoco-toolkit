"""
Mailbox Models - Data models for mailbox operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from monoco.features.connector.protocol.schema import (
    InboundMessage,
    OutboundMessage,
    MessageStatus,
    Provider,
)


class ListFormat(str, Enum):
    """Output format for message listing."""
    TABLE = "table"
    JSON = "json"
    COMPACT = "compact"
    ID = "id"


@dataclass
class MailboxConfig:
    """Configuration for the mailbox feature."""
    root_path: Path
    courier_api_url: str = "http://localhost:8080"
    courier_api_prefix: str = "/api/v1"

    @property
    def inbound_path(self) -> Path:
        """Path to inbound messages directory."""
        return self.root_path / "inbound"

    @property
    def outbound_path(self) -> Path:
        """Path to outbound messages directory."""
        return self.root_path / "outbound"

    @property
    def archive_path(self) -> Path:
        """Path to archive directory."""
        return self.root_path / "archive"

    @property
    def state_path(self) -> Path:
        """Path to state directory."""
        return self.root_path / ".state"


@dataclass
class MessageFilter:
    """Filter criteria for message listing."""
    status: Optional[MessageStatus] = None
    provider: Optional[Provider] = None
    since: Optional[datetime] = None
    correlation_id: Optional[str] = None
    all: bool = False  # Include archived messages

    def matches(self, message: InboundMessage) -> bool:
        """Check if a message matches this filter."""
        # Note: Status filtering is done via lock state, not message itself

        if self.provider and message.provider != self.provider:
            return False

        if self.since and message.timestamp < self.since:
            return False

        if self.correlation_id and message.correlation_id != self.correlation_id:
            return False

        return True


@dataclass
class MessageListItem:
    """Summary item for message listing."""
    id: str
    provider: Provider
    from_name: str
    from_id: str
    status: MessageStatus
    timestamp: datetime
    preview: str
    session_name: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "id": self.id,
            "provider": self.provider.value,
            "from": {
                "name": self.from_name,
                "id": self.from_id,
            },
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "preview": self.preview,
            "session_name": self.session_name,
            "correlation_id": self.correlation_id,
        }


@dataclass
class LockInfo:
    """Lock information for a claimed message."""
    message_id: str
    status: MessageStatus
    claimed_by: Optional[str] = None
    claimed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        """Check if the lock has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_claimed(self) -> bool:
        """Check if the message is currently claimed."""
        return self.status == MessageStatus.CLAIMED and not self.is_expired

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "message_id": self.message_id,
            "status": self.status.value,
        }
        if self.claimed_by:
            result["claimed_by"] = self.claimed_by
        if self.claimed_at:
            result["claimed_at"] = self.claimed_at.isoformat()
        if self.expires_at:
            result["expires_at"] = self.expires_at.isoformat()
        return result


@dataclass
class OutboundDraft:
    """Draft for an outbound message."""
    id: str
    to: str
    provider: Provider
    content_text: str
    reply_to: Optional[str] = None
    thread_key: Optional[str] = None
    type: str = "text"
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)

    def to_frontmatter(self) -> Dict[str, Any]:
        """Convert to frontmatter dictionary."""
        return {
            "id": self.id,
            "to": self.to,
            "provider": self.provider.value,
            "reply_to": self.reply_to,
            "thread_key": self.thread_key,
            "type": self.type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "artifacts": self.artifacts,
            "options": self.options,
        }
