"""
Mailbox Watcher Module - Watches mailbox directories for incoming messages.

This module provides:
- MailboxFileEvent: Specialized file event for mailbox operations
- MailboxWatcher: Base watcher for mailbox directories
- MailboxInboundWatcher: Watches inbound directory for new messages
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from monoco.core.scheduler import AgentEventType, EventBus
from monoco.core.watcher.base import (
    ChangeType,
    FileEvent,
    PollingWatcher,
    WatchConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class MailboxFileEvent(FileEvent):
    """
    Specialized file event for mailbox operations.

    Extends FileEvent with mailbox-specific metadata:
    - provider: Message provider (dingtalk, email, etc.)
    - session_id: Conversation session identifier
    - message_id: Unique message identifier
    """

    provider: Optional[str] = None
    session_id: Optional[str] = None
    message_id: Optional[str] = None

    def to_agent_event_type(self) -> Optional[AgentEventType]:
        """Convert MailboxFileEvent to AgentEventType."""
        if self.change_type == ChangeType.CREATED:
            return AgentEventType.MAILBOX_INBOUND_RECEIVED
        return None

    def to_payload(self) -> Dict[str, Any]:
        """Convert to payload dict for EventBus with mailbox metadata."""
        payload = super().to_payload()
        payload.update(
            {
                "provider": self.provider,
                "session_id": self.session_id,
                "message_id": self.message_id,
                "mailbox_event": True,
            }
        )
        return payload


class MailboxWatcher(PollingWatcher):
    """
    Base watcher for mailbox directories.

    This watcher specializes in monitoring mailbox directories and
    extracting mailbox-specific metadata from message files.
    """

    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        name: Optional[str] = None,
    ):
        super().__init__(config, event_bus, name or "mailbox_watcher")
        self._last_scan_time: Dict[Path, float] = {}

    def _extract_mailbox_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract mailbox-specific metadata from a message file.

        Args:
            file_path: Path to the message file

        Returns:
            Dictionary with metadata (provider, session_id, message_id)
        """
        try:
            from monoco.features.mailbox.store import MailboxStore

            # Create a temporary store to parse the file
            store = MailboxStore.__new__(MailboxStore)
            frontmatter, _ = store._parse_frontmatter(file_path.read_text())

            if not frontmatter:
                return {}

            return {
                "provider": frontmatter.get("provider"),
                "session_id": frontmatter.get("session", {}).get("id"),
                "message_id": frontmatter.get("id"),
            }
        except Exception as e:
            logger.debug(f"Failed to extract metadata from {file_path}: {e}")
            return {}

    async def _check_changes(self) -> None:
        """Check for changes in watched mailbox directory."""
        current_states = self._scan_files()

        # Debug logging
        logger.debug(
            f"_check_changes: current_states keys: {list(current_states.keys())}"
        )
        logger.debug(
            f"_check_changes: _file_states keys: {list(self._file_states.keys())}"
        )

        # Check for new files
        for file_path, state in current_states.items():
            if file_path not in self._file_states:
                # New file detected
                logger.debug(f"New file detected: {file_path}")
                metadata = self._extract_mailbox_metadata(file_path)
                event = MailboxFileEvent(
                    path=file_path,
                    change_type=ChangeType.CREATED,
                    watcher_name=self.name,
                    new_content=state.get("content"),
                    metadata=metadata,
                    provider=metadata.get("provider"),
                    session_id=metadata.get("session_id"),
                    message_id=metadata.get("message_id"),
                )
                await self.emit(event)

        # Check for modified files
        for file_path, state in current_states.items():
            if file_path in self._file_states:
                old_state = self._file_states[file_path]
                old_hash = old_state.get("hash")
                new_hash = state.get("hash")
                logger.debug(
                    f"Checking modification for {file_path}: old_hash={old_hash}, new_hash={new_hash}"
                )
                if new_hash != old_hash:
                    # File modified
                    logger.debug(
                        f"File modified detected: {file_path}, hash changed: {old_hash} -> {new_hash}"
                    )
                    metadata = self._extract_mailbox_metadata(file_path)
                    event = MailboxFileEvent(
                        path=file_path,
                        change_type=ChangeType.MODIFIED,
                        watcher_name=self.name,
                        old_content=old_state.get("content"),
                        new_content=state.get("content"),
                        metadata=metadata,
                        provider=metadata.get("provider"),
                        session_id=metadata.get("session_id"),
                        message_id=metadata.get("message_id"),
                    )
                    await self.emit(event)
                else:
                    logger.debug(
                        f"No modification detected for {file_path}: hashes are equal"
                    )

        # Check for deleted files
        for file_path in list(self._file_states.keys()):
            if file_path not in current_states:
                # File deleted
                logger.debug(f"File deleted detected: {file_path}")
                event = MailboxFileEvent(
                    path=file_path,
                    change_type=ChangeType.DELETED,
                    watcher_name=self.name,
                    old_content=self._file_states[file_path].get("content"),
                )
                await self.emit(event)

        # Update state
        self._file_states = current_states
        logger.debug(
            f"_check_changes completed, updated _file_states keys: {list(self._file_states.keys())}"
        )


class MailboxInboundWatcher(MailboxWatcher):
    """
    Specialized watcher for inbound mailbox directory.

    Monitors .monoco/mailbox/inbound/ for new incoming messages
    and triggers appropriate agent events.
    """

    def __init__(
        self,
        mailbox_root: Path,
        event_bus: Optional[EventBus] = None,
        poll_interval: float = 2.0,
    ):
        config = WatchConfig(
            path=mailbox_root / "inbound",
            patterns=["*.md"],
            recursive=True,
            poll_interval=poll_interval,
        )
        super().__init__(config, event_bus, "mailbox_inbound_watcher")


class MailboxOutboundWatcher(MailboxWatcher):
    """
    Specialized watcher for outbound mailbox directory.

    Monitors .monoco/mailbox/outbound/ for new outbound messages
    that need to be sent to external providers.
    """

    def __init__(
        self,
        mailbox_root: Path,
        event_bus: Optional[EventBus] = None,
        poll_interval: float = 2.0,
    ):
        config = WatchConfig(
            path=mailbox_root / "outbound",
            patterns=["*.md"],
            recursive=True,
            poll_interval=poll_interval,
        )
        super().__init__(config, event_bus, "mailbox_outbound_watcher")


__all__ = [
    "MailboxFileEvent",
    "MailboxWatcher",
    "MailboxInboundWatcher",
    "MailboxOutboundWatcher",
]
