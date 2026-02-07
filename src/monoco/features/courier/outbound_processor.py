"""
Outbound Processor - Handles post-send processing and message lifecycle.

Manages:
- Success: Archive messages and update status
- Failure: Retry with exponential backoff or move to deadletter
- State persistence in message frontmatter
"""

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import yaml

from monoco.features.connector.protocol.constants import (
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE_MS,
    RETRY_BACKOFF_MULTIPLIER,
    RETRY_MAX_BACKOFF_MS,
)
from monoco.features.connector.protocol.schema import Provider
from .adapters.base import SendResult
from .outbound_watcher import OutboundMessageEntry

logger = logging.getLogger("courier.outbound_processor")


class OutboundProcessor:
    """
    Processes outbound messages after sending attempt.

    Responsibilities:
    - Update message frontmatter with send status
    - Archive successful messages
    - Retry failed messages with exponential backoff
    - Move permanently failed messages to deadletter
    """

    def __init__(
        self,
        outbound_path: Path,
        archive_path: Path,
        deadletter_path: Path,
        max_retries: int = MAX_RETRY_ATTEMPTS,
    ):
        """
        Initialize the outbound processor.

        Args:
            outbound_path: Path to mailbox/outbound directory
            archive_path: Path to mailbox/archive directory
            deadletter_path: Path to mailbox/.deadletter directory
            max_retries: Maximum number of retry attempts
        """
        self.outbound_path = Path(outbound_path)
        self.archive_path = Path(archive_path)
        self.deadletter_path = Path(deadletter_path)
        self.max_retries = max_retries

    def initialize(self) -> None:
        """Ensure directory structure exists."""
        self.outbound_path.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.deadletter_path.mkdir(parents=True, exist_ok=True)
        logger.info("OutboundProcessor initialized")

    def _calculate_next_retry(self, retry_count: int) -> datetime:
        """
        Calculate next retry time with exponential backoff.

        Args:
            retry_count: Current retry count

        Returns:
            Datetime for next retry attempt
        """
        delay_ms = int(
            RETRY_BACKOFF_BASE_MS * (RETRY_BACKOFF_MULTIPLIER ** retry_count)
        )
        delay_ms = min(delay_ms, RETRY_MAX_BACKOFF_MS)
        delay_seconds = delay_ms / 1000.0

        return datetime.utcnow() + timedelta(seconds=delay_seconds)

    def _update_frontmatter(
        self,
        file_path: Path,
        updates: Dict,
    ) -> bool:
        """
        Update message file frontmatter.

        Args:
            file_path: Path to message file
            updates: Dict of fields to update

        Returns:
            True if update succeeded
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Parse existing frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                        body = parts[2].strip()
                    except Exception as e:
                        logger.warning(f"Failed to parse frontmatter: {e}")
                        return False
                else:
                    return False
            else:
                return False

            # Apply updates
            frontmatter.update(updates)

            # Rebuild file content
            new_content = f"---\n{yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)}---\n{body}\n"

            file_path.write_text(new_content, encoding="utf-8")
            return True

        except Exception as e:
            logger.error(f"Failed to update frontmatter for {file_path}: {e}")
            return False

    def _move_to_archive(self, entry: OutboundMessageEntry) -> Optional[Path]:
        """
        Move a successfully sent message to archive.

        Args:
            entry: The message entry to archive

        Returns:
            Path to archived file or None if failed
        """
        try:
            provider_dir = self.archive_path / entry.provider.value
            provider_dir.mkdir(parents=True, exist_ok=True)

            dest_path = provider_dir / entry.file_path.name

            # Handle name collision
            counter = 1
            while dest_path.exists():
                stem = entry.file_path.stem
                suffix = entry.file_path.suffix
                dest_path = provider_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            shutil.move(str(entry.file_path), str(dest_path))
            logger.info(f"Archived message {entry.id} to {dest_path}")
            return dest_path

        except Exception as e:
            logger.error(f"Failed to archive message {entry.id}: {e}")
            return None

    def _move_to_deadletter(self, entry: OutboundMessageEntry) -> Optional[Path]:
        """
        Move a permanently failed message to deadletter queue.

        Args:
            entry: The message entry to move

        Returns:
            Path to deadletter file or None if failed
        """
        try:
            provider_dir = self.deadletter_path / entry.provider.value
            provider_dir.mkdir(parents=True, exist_ok=True)

            dest_path = provider_dir / entry.file_path.name

            # Handle name collision
            counter = 1
            while dest_path.exists():
                stem = entry.file_path.stem
                suffix = entry.file_path.suffix
                dest_path = provider_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            shutil.move(str(entry.file_path), str(dest_path))
            logger.warning(f"Moved message {entry.id} to deadletter: {dest_path}")
            return dest_path

        except Exception as e:
            logger.error(f"Failed to move message {entry.id} to deadletter: {e}")
            return None

    def process_success(
        self,
        entry: OutboundMessageEntry,
        result: SendResult,
    ) -> bool:
        """
        Process a successful send.

        Args:
            entry: The message entry
            result: Send result from adapter

        Returns:
            True if processing succeeded
        """
        logger.info(f"Message {entry.id} sent successfully")

        # Update frontmatter with success status
        updates = {
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat() + "Z",
        }

        if result.provider_message_id:
            updates["provider_message_id"] = result.provider_message_id

        if not self._update_frontmatter(entry.file_path, updates):
            logger.warning(f"Failed to update frontmatter for {entry.id}")

        # Move to archive
        archived_path = self._move_to_archive(entry)

        return archived_path is not None

    def process_failure(
        self,
        entry: OutboundMessageEntry,
        result: SendResult,
    ) -> bool:
        """
        Process a failed send.

        Args:
            entry: The message entry
            result: Send result from adapter

        Returns:
            True if retry scheduled, False if moved to deadletter
        """
        new_retry_count = entry.retry_count + 1

        logger.warning(
            f"Message {entry.id} failed (attempt {new_retry_count}/{self.max_retries}): {result.error}"
        )

        if new_retry_count >= self.max_retries:
            # Max retries exceeded, move to deadletter
            updates = {
                "status": "failed",
                "retry_count": new_retry_count,
                "error_message": result.error,
                "failed_at": datetime.utcnow().isoformat() + "Z",
            }

            self._update_frontmatter(entry.file_path, updates)
            self._move_to_deadletter(entry)
            return False

        # Schedule retry
        next_retry = self._calculate_next_retry(new_retry_count)

        updates = {
            "status": "pending",
            "retry_count": new_retry_count,
            "next_retry_at": next_retry.isoformat() + "Z",
            "error_message": result.error,
        }

        if self._update_frontmatter(entry.file_path, updates):
            logger.info(f"Scheduled retry for {entry.id} at {next_retry.isoformat()}")
            return True
        else:
            logger.error(f"Failed to schedule retry for {entry.id}")
            return False

    def process_send_result(
        self,
        entry: OutboundMessageEntry,
        result: SendResult,
    ) -> bool:
        """
        Process send result (success or failure).

        Args:
            entry: The message entry
            result: Send result from adapter

        Returns:
            True if message was successfully processed
        """
        if result.success:
            return self.process_success(entry, result)
        else:
            return self.process_failure(entry, result)

    def get_stats(self) -> Dict[str, any]:
        """Get processor statistics."""
        stats = {
            "archive_path": str(self.archive_path),
            "deadletter_path": str(self.deadletter_path),
            "max_retries": self.max_retries,
        }

        # Count archived messages
        archive_count = 0
        if self.archive_path.exists():
            for provider_dir in self.archive_path.iterdir():
                if provider_dir.is_dir():
                    archive_count += len(list(provider_dir.glob("*.md")))

        # Count deadletter messages
        deadletter_count = 0
        if self.deadletter_path.exists():
            for provider_dir in self.deadletter_path.iterdir():
                if provider_dir.is_dir():
                    deadletter_count += len(list(provider_dir.glob("*.md")))

        stats["archived_count"] = archive_count
        stats["deadletter_count"] = deadletter_count

        return stats
