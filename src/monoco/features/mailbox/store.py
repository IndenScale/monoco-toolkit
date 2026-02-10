"""
Mailbox Store - Filesystem operations for message storage.

This module handles reading and writing message files to the mailbox directories.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from monoco.features.connector.protocol.schema import InboundMessage, OutboundMessage
from monoco.features.connector.protocol.constants import (
    INBOUND_DIR,
    OUTBOUND_DIR,
    ARCHIVE_DIR,
    STATE_DIR,
    LOCKS_FILE,
)

from .models import MailboxConfig, LockInfo, MessageStatus, OutboundDraft


class MailboxStore:
    """
    Manages filesystem operations for the mailbox.

    This class handles:
    - Reading messages from inbound/outbound/archive directories
    - Writing outbound message drafts
    - Managing lock state
    """

    def __init__(self, config: MailboxConfig):
        self.config = config
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.config.inbound_path.mkdir(parents=True, exist_ok=True)
        self.config.outbound_path.mkdir(parents=True, exist_ok=True)
        self.config.archive_path.mkdir(parents=True, exist_ok=True)
        self.config.state_path.mkdir(parents=True, exist_ok=True)

        # Create provider subdirectories
        from monoco.features.connector.protocol.schema import Provider
        for provider in Provider:
            (self.config.inbound_path / provider.value).mkdir(exist_ok=True)
            (self.config.outbound_path / provider.value).mkdir(exist_ok=True)
            (self.config.archive_path / provider.value).mkdir(exist_ok=True)

    def _parse_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """
        Parse YAML frontmatter from markdown content.

        Returns:
            Tuple of (frontmatter_dict, body_content)
        """
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)

        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
                body = match.group(2)
                return frontmatter, body
            except yaml.YAMLError:
                pass

        return None, content

    def _write_frontmatter_file(
        self,
        path: Path,
        frontmatter: Dict,
        body: str = ""
    ) -> None:
        """Write a file with YAML frontmatter."""
        yaml_content = yaml.dump(
            frontmatter,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
        content = f"---\n{yaml_content}---\n{body}"
        path.write_text(content, encoding="utf-8")

    def read_inbound_message(self, message_id: str) -> Optional[InboundMessage]:
        """
        Read an inbound message by ID.

        Args:
            message_id: Message identifier

        Returns:
            InboundMessage if found, None otherwise
        """
        # Search in inbound directories
        for provider_dir in self.config.inbound_path.iterdir():
            if not provider_dir.is_dir():
                continue

            for file_path in provider_dir.glob("*.md"):
                frontmatter, body = self._parse_frontmatter(file_path.read_text())
                if frontmatter and frontmatter.get("id") == message_id:
                    # Add body as text content if not present
                    if frontmatter.get("content", {}).get("text") is None:
                        if "content" not in frontmatter:
                            frontmatter["content"] = {}
                        frontmatter["content"]["text"] = body.strip()
                    try:
                        return InboundMessage.model_validate(frontmatter)
                    except Exception:
                        return None

        return None

    def read_outbound_message(self, message_id: str) -> Optional[OutboundMessage]:
        """
        Read an outbound message by ID.

        Args:
            message_id: Message identifier

        Returns:
            OutboundMessage if found, None otherwise
        """
        # Search in outbound directories
        for provider_dir in self.config.outbound_path.iterdir():
            if not provider_dir.is_dir():
                continue

            for file_path in provider_dir.glob("*.md"):
                frontmatter, body = self._parse_frontmatter(file_path.read_text())
                if frontmatter and frontmatter.get("id") == message_id:
                    if frontmatter.get("content", {}).get("text") is None:
                        if "content" not in frontmatter:
                            frontmatter["content"] = {}
                        frontmatter["content"]["text"] = body.strip()
                    try:
                        return OutboundMessage.model_validate(frontmatter)
                    except Exception:
                        return None

        return None

    def list_inbound_messages(
        self,
        provider: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[Tuple[Path, InboundMessage]]:
        """
        List all inbound messages, optionally filtered.

        Args:
            provider: Filter by provider
            since: Filter by timestamp

        Returns:
            List of (file_path, message) tuples
        """
        results = []

        search_paths = []
        if provider:
            search_paths = [self.config.inbound_path / provider]
        else:
            search_paths = [
                d for d in self.config.inbound_path.iterdir() if d.is_dir()
            ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            for file_path in search_path.glob("*.md"):
                try:
                    frontmatter, body = self._parse_frontmatter(file_path.read_text())
                    if not frontmatter:
                        continue

                    # Add body as text content
                    if "content" not in frontmatter:
                        frontmatter["content"] = {}
                    if frontmatter["content"].get("text") is None:
                        frontmatter["content"]["text"] = body.strip()

                    message = InboundMessage.model_validate(frontmatter)

                    if since and message.timestamp < since:
                        continue

                    results.append((file_path, message))
                except Exception:
                    continue

        # Sort by timestamp descending
        results.sort(key=lambda x: x[1].timestamp, reverse=True)
        return results

    def create_outbound_draft(
        self,
        draft: OutboundDraft,
    ) -> Path:
        """
        Create an outbound message draft.

        Args:
            draft: The draft to create

        Returns:
            Path to the created file
        """
        provider_dir = self.config.outbound_path / draft.provider.value
        provider_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_{draft.id}.md"
        file_path = provider_dir / filename

        frontmatter = draft.to_frontmatter()
        self._write_frontmatter_file(file_path, frontmatter, draft.content_text)

        return file_path

    def get_locks(self) -> Dict[str, LockInfo]:
        """
        Read the current locks from the state file.

        Returns:
            Dictionary mapping message_id to LockInfo
        """
        locks_path = self.config.state_path / LOCKS_FILE

        if not locks_path.exists():
            return {}

        try:
            data = json.loads(locks_path.read_text())
            locks = {}
            for msg_id, lock_data in data.items():
                locks[msg_id] = LockInfo(
                    message_id=msg_id,
                    status=MessageStatus(lock_data.get("status", "new")),
                    claimed_by=lock_data.get("claimed_by"),
                    claimed_at=datetime.fromisoformat(lock_data["claimed_at"])
                    if lock_data.get("claimed_at")
                    else None,
                    expires_at=datetime.fromisoformat(lock_data["expires_at"])
                    if lock_data.get("expires_at")
                    else None,
                )
            return locks
        except Exception:
            return {}

    def get_message_status(self, message_id: str) -> MessageStatus:
        """
        Get the current status of a message from locks.

        Args:
            message_id: Message identifier

        Returns:
            MessageStatus (defaults to NEW if not found)
        """
        locks = self.get_locks()
        lock = locks.get(message_id)

        if not lock:
            return MessageStatus.NEW

        if lock.is_expired:
            return MessageStatus.NEW

        return lock.status

    def save_locks(self, locks: Dict[str, LockInfo]) -> None:
        """
        Save locks to the state file.

        Args:
            locks: Dictionary of message locks
        """
        locks_path = self.config.state_path / LOCKS_FILE

        data = {}
        for msg_id, lock in locks.items():
            data[msg_id] = lock.to_dict()

        locks_path.write_text(json.dumps(data, indent=2, default=str))

    def find_message_file(self, message_id: str) -> Optional[Path]:
        """
        Find the file path for a message by ID.

        Searches in inbound, outbound, and archive directories.

        Args:
            message_id: Message identifier

        Returns:
            Path to the file if found, None otherwise
        """
        # Search inbound
        for provider_dir in self.config.inbound_path.iterdir():
            if not provider_dir.is_dir():
                continue
            for file_path in provider_dir.glob("*.md"):
                frontmatter, _ = self._parse_frontmatter(file_path.read_text())
                if frontmatter and frontmatter.get("id") == message_id:
                    return file_path

        # Search outbound
        for provider_dir in self.config.outbound_path.iterdir():
            if not provider_dir.is_dir():
                continue
            for file_path in provider_dir.glob("*.md"):
                frontmatter, _ = self._parse_frontmatter(file_path.read_text())
                if frontmatter and frontmatter.get("id") == message_id:
                    return file_path

        # Search archive
        for provider_dir in self.config.archive_path.iterdir():
            if not provider_dir.is_dir():
                continue
            for file_path in provider_dir.glob("*.md"):
                frontmatter, _ = self._parse_frontmatter(file_path.read_text())
                if frontmatter and frontmatter.get("id") == message_id:
                    return file_path

        return None

    def archive_message(self, message_id: str) -> Optional[Path]:
        """
        Move a message to the archive directory.

        Note: Artifacts are content-addressed and remain in place
        (they may be referenced by multiple messages). Only the
        message metadata file is moved.

        Args:
            message_id: Message identifier

        Returns:
            New path if archived, None if message not found
        """
        source_path = self.find_message_file(message_id)
        if not source_path:
            return None

        # Determine provider from message
        frontmatter, _ = self._parse_frontmatter(source_path.read_text())
        if not frontmatter:
            return None

        provider = frontmatter.get("provider", "unknown")
        archive_provider_dir = self.config.archive_path / provider
        archive_provider_dir.mkdir(parents=True, exist_ok=True)

        dest_path = archive_provider_dir / source_path.name
        source_path.rename(dest_path)

        # Note: Artifacts are content-addressed and shared across messages
        # They remain in ~/.monoco/artifacts/ and are not moved
        # The manifest records which messages reference each artifact

        return dest_path

    def get_message_artifacts(self, message_id: str) -> List[Dict]:
        """
        Get artifact information for a message.

        Args:
            message_id: Message identifier

        Returns:
            List of artifact metadata dicts
        """
        message = self.read_inbound_message(message_id)
        if not message:
            message = self.read_outbound_message(message_id)

        if message and message.artifacts:
            return [a.model_dump(mode="json") for a in message.artifacts]

        return []

    def create_inbound_message(
        self,
        message: InboundMessage,
        temp_suffix: str = ".tmp"
    ) -> Path:
        """
        Create an inbound message file atomically.

        Writes to a temp file first, then renames for atomicity.
        The file is stored in the provider-specific subdirectory.

        Args:
            message: The inbound message to store
            temp_suffix: Suffix for temporary file (default: .tmp)

        Returns:
            Path to the created file

        Raises:
            ValueError: If message validation fails
            IOError: If file operations fail
        """
        # Ensure provider directory exists
        provider_dir = self.config.inbound_path / message.provider.value
        provider_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from message
        filename = message.to_filename()
        final_path = provider_dir / filename
        temp_path = provider_dir / f"{filename}{temp_suffix}"

        # Build frontmatter from message model
        frontmatter = message.model_dump(mode="json", exclude_none=True)

        # Extract body text from content
        body = ""
        if message.content:
            body = message.content.text or message.content.markdown or ""

        # Write to temp file first (atomic write pattern)
        yaml_content = yaml.dump(
            frontmatter,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
        content = f"---\n{yaml_content}---\n{body}"

        try:
            temp_path.write_text(content, encoding="utf-8")
            # Atomic rename
            temp_path.rename(final_path)
        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise IOError(f"Failed to write inbound message: {e}") from e

        return final_path


# Global store instance
_store: Optional[MailboxStore] = None


def get_mailbox_store(config: Optional[MailboxConfig] = None) -> MailboxStore:
    """
    Get or create the global mailbox store instance.

    Args:
        config: Optional configuration (required on first call)

    Returns:
        MailboxStore instance
    """
    global _store
    if _store is None:
        if config is None:
            raise ValueError("Config required for initial store creation")
        _store = MailboxStore(config)
    return _store
