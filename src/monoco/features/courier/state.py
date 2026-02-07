"""
Courier State Management - Lock, archive, and retry logic.

Manages message state including:
- Claim locks (who is processing which message)
- Archive operations (move completed messages to archive)
- Retry logic (handle failed messages with exponential backoff)
"""

import json
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading

from monoco.features.connector.protocol.schema import MessageStatus
from monoco.features.connector.protocol.constants import (
    CLAIM_TIMEOUT_SECONDS,
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE_MS,
    RETRY_BACKOFF_MULTIPLIER,
    RETRY_MAX_BACKOFF_MS,
)


class LockError(Exception):
    """Base exception for lock-related errors."""

    class MessageNotFoundError(Exception):
        """Raised when a message is not found."""
        pass

    class MessageAlreadyClaimedError(Exception):
        """Raised when trying to claim a message that's already claimed."""
        def __init__(self, message: str, claimed_by: Optional[str] = None, claimed_at: Optional[datetime] = None):
            super().__init__(message)
            self.claimed_by = claimed_by
            self.claimed_at = claimed_at

    class MessageNotClaimedError(Exception):
        """Raised when trying to complete/fail a message that isn't claimed."""
        pass

    class MessageClaimedByOtherError(Exception):
        """Raised when trying to complete/fail a message claimed by another agent."""
        pass



@dataclass
class LockEntry:
    """Represents a lock entry for a claimed message."""
    message_id: str
    status: str
    claimed_by: Optional[str] = None
    claimed_at: Optional[str] = None
    expires_at: Optional[str] = None
    retry_count: int = 0
    fail_reason: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LockEntry":
        return cls(
            message_id=data.get("message_id", ""),
            status=data.get("status", "new"),
            claimed_by=data.get("claimed_by"),
            claimed_at=data.get("claimed_at"),
            expires_at=data.get("expires_at"),
            retry_count=data.get("retry_count", 0),
            fail_reason=data.get("fail_reason"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_expired(self) -> bool:
        """Check if this lock has expired."""
        if not self.expires_at:
            return False
        try:
            expires = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return datetime.utcnow() > expires.replace(tzinfo=None)
        except (ValueError, TypeError):
            return False


class LockManager:
    """
    Manages message claim locks.

    Thread-safe in-memory lock storage with periodic persistence.
    """

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.locks_file = state_dir / "locks.json"
        self._locks: Dict[str, LockEntry] = {}
        self._lock = threading.RLock()

    def _load_locks(self) -> None:
        """Load locks from disk."""
        if self.locks_file.exists():
            try:
                with open(self.locks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._locks = {
                        k: LockEntry.from_dict(v) for k, v in data.items()
                    }
            except (json.JSONDecodeError, IOError):
                self._locks = {}

    def _save_locks(self) -> None:
        """Save locks to disk."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with open(self.locks_file, "w", encoding="utf-8") as f:
            json.dump(
                {k: v.to_dict() for k, v in self._locks.items()},
                f,
                indent=2,
                default=str,
            )

    def initialize(self) -> None:
        """Initialize the lock manager."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._load_locks()
        self._cleanup_expired_locks()

    def _cleanup_expired_locks(self) -> None:
        """Remove expired locks."""
        expired = [
            msg_id for msg_id, entry in self._locks.items()
            if entry.status == MessageStatus.CLAIMED.value and entry.is_expired()
        ]
        for msg_id in expired:
            self._locks[msg_id].status = MessageStatus.NEW.value
            self._locks[msg_id].claimed_by = None
            self._locks[msg_id].claimed_at = None
            self._locks[msg_id].expires_at = None

    def get_lock(self, message_id: str) -> Optional[LockEntry]:
        """Get the lock entry for a message."""
        with self._lock:
            self._cleanup_expired_locks()
            return self._locks.get(message_id)

    def claim_message(
        self,
        message_id: str,
        agent_id: str,
        timeout: int = CLAIM_TIMEOUT_SECONDS,
    ) -> LockEntry:
        """
        Claim a message for processing.

        Args:
            message_id: The message ID to claim
            agent_id: The agent claiming the message
            timeout: Claim timeout in seconds

        Returns:
            LockEntry with claim details

        Raises:
            MessageNotFoundError: If message doesn't exist
            MessageAlreadyClaimedError: If message is already claimed
        """
        with self._lock:
            self._cleanup_expired_locks()

            existing = self._locks.get(message_id)
            if existing:
                if existing.status == MessageStatus.CLAIMED.value and not existing.is_expired():
                    raise LockError.MessageAlreadyClaimedError(
                        f"Message already claimed by {existing.claimed_by}",
                        claimed_by=existing.claimed_by,
                        claimed_at=datetime.fromisoformat(existing.claimed_at) if existing.claimed_at else None,
                    )

            now = datetime.utcnow()
            expires = now + timedelta(seconds=timeout)

            entry = LockEntry(
                message_id=message_id,
                status=MessageStatus.CLAIMED.value,
                claimed_by=agent_id,
                claimed_at=now.isoformat() + "Z",
                expires_at=expires.isoformat() + "Z",
            )
            self._locks[message_id] = entry
            self._save_locks()
            return entry

    def complete_message(self, message_id: str, agent_id: str) -> None:
        """
        Mark a message as complete.

        Args:
            message_id: The message ID
            agent_id: The agent completing the message

        Raises:
            MessageNotFoundError: If message not found
            MessageNotClaimedError: If message not claimed
            MessageClaimedByOtherError: If claimed by another agent
        """
        with self._lock:
            entry = self._locks.get(message_id)
            if not entry:
                raise LockError.MessageNotFoundError(f"Message '{message_id}' not found")

            if entry.status != MessageStatus.CLAIMED.value:
                raise LockError.MessageNotClaimedError(f"Message '{message_id}' is not claimed")

            if entry.claimed_by != agent_id:
                raise LockError.MessageClaimedByOtherError(
                    f"Message claimed by {entry.claimed_by}, not {agent_id}"
                )

            entry.status = MessageStatus.COMPLETED.value
            entry.retry_count = 0
            self._save_locks()

    def fail_message(
        self,
        message_id: str,
        agent_id: str,
        reason: str = "",
        retryable: bool = True,
    ) -> LockEntry:
        """
        Mark a message as failed.

        Args:
            message_id: The message ID
            agent_id: The agent failing the message
            reason: Failure reason
            retryable: Whether the failure is retryable

        Returns:
            Updated LockEntry

        Raises:
            MessageNotFoundError: If message not found
            MessageNotClaimedError: If message not claimed
            MessageClaimedByOtherError: If claimed by another agent
        """
        with self._lock:
            entry = self._locks.get(message_id)
            if not entry:
                raise LockError.MessageNotFoundError(f"Message '{message_id}' not found")

            if entry.status != MessageStatus.CLAIMED.value:
                raise LockError.MessageNotClaimedError(f"Message '{message_id}' is not claimed")

            if entry.claimed_by != agent_id:
                raise LockError.MessageClaimedByOtherError(
                    f"Message claimed by {entry.claimed_by}, not {agent_id}"
                )

            entry.fail_reason = reason
            entry.retry_count += 1

            if retryable and entry.retry_count < MAX_RETRY_ATTEMPTS:
                # Reset to new for retry
                entry.status = MessageStatus.NEW.value
                entry.claimed_by = None
                entry.claimed_at = None
                entry.expires_at = None
            else:
                # Move to deadletter
                entry.status = MessageStatus.DEADLETTER.value

            self._save_locks()
            return entry

    def get_status(self, message_id: str) -> MessageStatus:
        """Get the current status of a message."""
        with self._lock:
            entry = self._locks.get(message_id)
            if not entry:
                return MessageStatus.NEW
            if entry.status == MessageStatus.CLAIMED.value and entry.is_expired():
                return MessageStatus.NEW
            return MessageStatus(entry.status)


class MessageStateManager:
    """
    High-level message state management.

    Coordinates lock management with file system operations for:
    - Archiving completed messages
    - Moving failed messages to deadletter
    - Managing outbound message state
    """

    def __init__(
        self,
        lock_manager: LockManager,
        mailbox_root: Path,
    ):
        self.lock_manager = lock_manager
        self.mailbox_root = Path(mailbox_root)
        self.inbound_path = self.mailbox_root / "inbound"
        self.outbound_path = self.mailbox_root / "outbound"
        self.archive_path = self.mailbox_root / "archive"
        self.deadletter_path = self.mailbox_root / ".deadletter"

    def initialize(self) -> None:
        """Initialize state directories."""
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.deadletter_path.mkdir(parents=True, exist_ok=True)
        self.lock_manager.initialize()

    def _find_message_file(self, message_id: str) -> Optional[Path]:
        """Find a message file by ID."""
        # Search in inbound
        for provider_dir in self.inbound_path.iterdir():
            if provider_dir.is_dir():
                for file in provider_dir.glob(f"*{message_id}*.md"):
                    return file
        # Search in archive
        for provider_dir in self.archive_path.iterdir():
            if provider_dir.is_dir():
                for file in provider_dir.glob(f"*{message_id}*.md"):
                    return file
        return None

    def archive_message(self, message_id: str) -> Optional[Path]:
        """
        Move a completed message to archive.

        Args:
            message_id: The message ID to archive

        Returns:
            Path to archived file, or None if not found
        """
        source = self._find_message_file(message_id)
        if not source:
            return None

        # Determine provider from path
        provider = source.parent.name
        archive_dir = self.archive_path / provider
        archive_dir.mkdir(parents=True, exist_ok=True)

        dest = archive_dir / source.name
        shutil.move(str(source), str(dest))
        return dest

    def move_to_deadletter(self, message_id: str) -> Optional[Path]:
        """
        Move a failed message to deadletter queue.

        Args:
            message_id: The message ID

        Returns:
            Path to deadletter file, or None if not found
        """
        source = self._find_message_file(message_id)
        if not source:
            return None

        provider = source.parent.name
        deadletter_dir = self.deadletter_path / provider
        deadletter_dir.mkdir(parents=True, exist_ok=True)

        dest = deadletter_dir / source.name
        shutil.move(str(source), str(dest))
        return dest

    def get_retry_delay_ms(self, retry_count: int) -> int:
        """
        Calculate retry delay with exponential backoff.

        Args:
            retry_count: Number of retries so far

        Returns:
            Delay in milliseconds
        """
        delay = int(
            RETRY_BACKOFF_BASE_MS * (RETRY_BACKOFF_MULTIPLIER ** retry_count)
        )
        return min(delay, RETRY_MAX_BACKOFF_MS)
