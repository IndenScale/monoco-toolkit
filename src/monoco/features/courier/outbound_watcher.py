"""
Outbound Watcher - Polls for pending outbound messages.

Scans the mailbox/outbound directory for messages waiting to be sent,
filtering out locked or recently processed messages.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Set

from monoco.features.connector.protocol.constants import (
    MAX_RETRY_ATTEMPTS,
)
from monoco.features.connector.protocol.schema import Provider

logger = logging.getLogger("courier.outbound_watcher")


@dataclass
class OutboundMessageEntry:
    """Represents a pending outbound message found by the watcher."""

    id: str
    provider: Provider
    to: str
    content_type: str
    status: str
    file_path: Path
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None
    error_message: Optional[str] = None
    frontmatter: Dict = field(default_factory=dict)


class OutboundWatcher:
    """
    Watches the outbound directory for pending messages.

    Responsibilities:
    - Scan outbound/{provider} directories for *.md files
    - Parse message frontmatter to extract metadata
    - Filter out locked, processing, or scheduled messages
    - Track seen files to avoid redundant processing
    """

    # Supported providers
    SUPPORTED_PROVIDERS = [
        Provider.DINGTALK,
        Provider.LARK,
        Provider.EMAIL,
        Provider.SLACK,
        Provider.TEAMS,
        Provider.WECOM,
    ]

    def __init__(
        self,
        outbound_path: Path,
        poll_interval: float = 5.0,
        max_retries: int = MAX_RETRY_ATTEMPTS,
    ):
        """
        Initialize the outbound watcher.

        Args:
            outbound_path: Path to mailbox/outbound directory
            poll_interval: Seconds between directory scans
            max_retries: Maximum retry attempts before deadletter
        """
        self.outbound_path = Path(outbound_path)
        self.poll_interval = poll_interval
        self.max_retries = max_retries

        # Tracking state
        self._last_scan_time: Optional[datetime] = None
        self._processing_ids: Set[str] = set()
        self._lock = None  # Will be set if threading needed

    def initialize(self) -> None:
        """Ensure directory structure exists."""
        self.outbound_path.mkdir(parents=True, exist_ok=True)
        for provider in self.SUPPORTED_PROVIDERS:
            provider_dir = self.outbound_path / provider.value
            provider_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"OutboundWatcher initialized: {self.outbound_path}")

    def _parse_frontmatter(self, content: str) -> tuple[Dict, str]:
        """
        Parse YAML frontmatter from markdown content.

        Returns:
            Tuple of (frontmatter dict, message body)
        """
        frontmatter = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                import yaml

                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                except Exception as e:
                    logger.warning(f"Failed to parse frontmatter: {e}")

        return frontmatter, body

    def _should_process(self, entry: OutboundMessageEntry) -> bool:
        """
        Determine if a message should be processed now.

        Filters out:
        - Messages already being processed
        - Messages with status 'sent' or 'sending'
        - Messages scheduled for future retry
        - Messages that exceeded max retries
        """
        # Already being processed
        if entry.id in self._processing_ids:
            return False

        # Already sent
        if entry.status in ("sent", "sending"):
            return False

        # Check retry count
        if entry.retry_count >= self.max_retries:
            logger.warning(f"Message {entry.id} exceeded max retries")
            return False

        # Check if scheduled for future retry
        if entry.next_retry_at and datetime.utcnow() < entry.next_retry_at:
            return False

        return True

    def _scan_provider_dir(self, provider: Provider) -> Iterator[OutboundMessageEntry]:
        """Scan a single provider directory for pending messages."""
        provider_dir = self.outbound_path / provider.value
        if not provider_dir.exists():
            return

        pattern = "*.md"
        for file_path in provider_dir.glob(pattern):
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                frontmatter, body = self._parse_frontmatter(content)

                # Skip if no valid frontmatter
                if not frontmatter:
                    continue

                # Extract required fields
                msg_id = frontmatter.get("id")
                if not msg_id:
                    # Generate ID from filename if not present
                    msg_id = file_path.stem

                status = frontmatter.get("status", "pending")
                retry_count = frontmatter.get("retry_count", 0)
                next_retry_str = frontmatter.get("next_retry_at")
                next_retry = None

                if next_retry_str:
                    try:
                        next_retry = datetime.fromisoformat(
                            next_retry_str.replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                    except (ValueError, TypeError):
                        pass

                # Parse error message
                error_message = frontmatter.get("error_message")

                entry = OutboundMessageEntry(
                    id=msg_id,
                    provider=provider,
                    to=frontmatter.get("to", ""),
                    content_type=frontmatter.get("content_type", "text"),
                    status=status,
                    file_path=file_path,
                    retry_count=retry_count,
                    next_retry_at=next_retry,
                    error_message=error_message,
                    frontmatter=frontmatter,
                )

                if self._should_process(entry):
                    yield entry

            except Exception as e:
                logger.warning(f"Failed to scan {file_path}: {e}")

    def scan(self) -> List[OutboundMessageEntry]:
        """
        Scan all provider directories for pending messages.

        Returns:
            List of OutboundMessageEntry ready to be sent
        """
        pending = []
        self._last_scan_time = datetime.utcnow()

        for provider in self.SUPPORTED_PROVIDERS:
            try:
                for entry in self._scan_provider_dir(provider):
                    pending.append(entry)
            except Exception as e:
                logger.error(f"Error scanning {provider.value}: {e}")

        if pending:
            logger.info(f"Found {len(pending)} pending outbound messages")

        return pending

    def mark_processing(self, message_id: str) -> None:
        """Mark a message as being processed to prevent duplicate pickup."""
        self._processing_ids.add(message_id)

    def mark_done(self, message_id: str) -> None:
        """Mark a message as done processing."""
        self._processing_ids.discard(message_id)

    def wait_for_next_scan(self) -> None:
        """Sleep until next poll interval."""
        time.sleep(self.poll_interval)

    def get_stats(self) -> Dict[str, any]:
        """Get watcher statistics."""
        stats = {
            "outbound_path": str(self.outbound_path),
            "poll_interval": self.poll_interval,
            "last_scan": self._last_scan_time.isoformat()
            if self._last_scan_time
            else None,
            "processing_count": len(self._processing_ids),
        }

        # Count messages per provider
        provider_counts = {}
        for provider in self.SUPPORTED_PROVIDERS:
            provider_dir = self.outbound_path / provider.value
            if provider_dir.exists():
                count = len(list(provider_dir.glob("*.md")))
                provider_counts[provider.value] = count

        stats["provider_counts"] = provider_counts
        return stats
