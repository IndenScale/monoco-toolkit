"""
MemoWatcher - Monitors Memo inbox for changes.

Part of Layer 1 (File Watcher) in the event automation framework.
Emits events when memo count crosses thresholds.
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from monoco.core.scheduler import AgentEventType, EventBus, event_bus

from .base import (
    ChangeType,
    FileEvent,
    FilesystemWatcher,
    WatchConfig,
    PollingWatcher,
)

logger = logging.getLogger(__name__)


class MemoFileEvent(FileEvent):
    """FileEvent specific to Memo files."""
    
    def __init__(
        self,
        path: Path,
        change_type: ChangeType,
        pending_count: int = 0,
        threshold: int = 5,
        **kwargs,
    ):
        super().__init__(
            path=path,
            change_type=change_type,
            watcher_name="MemoWatcher",
            **kwargs,
        )
        self.pending_count = pending_count
        self.threshold = threshold
    
    @property
    def threshold_crossed(self) -> bool:
        """Check if threshold has been crossed."""
        return self.pending_count >= self.threshold
    
    def to_agent_event_type(self) -> Optional[AgentEventType]:
        """Convert to appropriate AgentEventType."""
        if self.pending_count >= self.threshold:
            return AgentEventType.MEMO_THRESHOLD
        return AgentEventType.MEMO_CREATED
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to payload with Memo-specific fields."""
        payload = super().to_payload()
        payload["pending_count"] = self.pending_count
        payload["threshold"] = self.threshold
        payload["threshold_crossed"] = self.pending_count >= self.threshold
        return payload


class MemoWatcher(PollingWatcher):
    """
    Watcher for Memo inbox file.
    
    Monitors the Memos/inbox.md file for:
    - New memo entries
    - Pending memo count changes
    - Threshold crossing events
    
    Example:
        >>> config = WatchConfig(
        ...     path=Path("./Memos/inbox.md"),
        ...     patterns=["*.md"],
        ... )
        >>> watcher = MemoWatcher(config, threshold=5)
        >>> await watcher.start()
    """
    
    # Regex to match memo entries (lines starting with "- " that aren't checkboxes)
    MEMO_PATTERN = re.compile(r"^-\s+(?!\[)[^\n]*$", re.MULTILINE)
    # Regex to match checkbox items
    CHECKBOX_PATTERN = re.compile(r"^-\s*\[([ xX-])\]", re.MULTILINE)
    
    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        name: str = "MemoWatcher",
        threshold: int = 5,
    ):
        super().__init__(config, event_bus, name)
        self.threshold = threshold
        self._last_pending_count = 0
        self._threshold_crossed = False
    
    async def _check_changes(self) -> None:
        """Check for memo changes."""
        if not self.config.path.exists():
            return
        
        try:
            content = self._read_file_content(self.config.path) or ""
            pending_count = self._count_pending_memos(content)
            
            # Check if count changed
            if pending_count != self._last_pending_count:
                await self._handle_count_change(pending_count)
                self._last_pending_count = pending_count
        
        except Exception as e:
            logger.error(f"Error checking memo file: {e}")
    
    async def _handle_count_change(self, pending_count: int) -> None:
        """Handle memo count change."""
        # Check for threshold crossing
        threshold_crossed = pending_count >= self.threshold
        
        if threshold_crossed and not self._threshold_crossed:
            # Threshold just crossed
            event = MemoFileEvent(
                path=self.config.path,
                change_type=ChangeType.MODIFIED,
                pending_count=pending_count,
                threshold=self.threshold,
                metadata={
                    "previous_count": self._last_pending_count,
                    "event_type": "threshold_crossed",
                },
            )
            await self.emit(event)
            logger.info(f"Memo threshold crossed: {pending_count} >= {self.threshold}")
        
        elif pending_count > self._last_pending_count:
            # New memos added
            event = MemoFileEvent(
                path=self.config.path,
                change_type=ChangeType.MODIFIED,
                pending_count=pending_count,
                threshold=self.threshold,
                metadata={
                    "previous_count": self._last_pending_count,
                    "event_type": "memos_added",
                },
            )
            await self.emit(event)
            logger.debug(f"New memos added: {pending_count} total")
        
        self._threshold_crossed = threshold_crossed
    
    def _count_pending_memos(self, content: str) -> int:
        """
        Count pending (unchecked) memos in content.
        
        Counts:
        - Lines starting with "- " that are not checkboxes
        - Checkbox items with empty or "-" state
        """
        count = 0
        lines = content.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line.startswith("-"):
                continue
            
            # Check if it's a checkbox
            checkbox_match = self.CHECKBOX_PATTERN.match(line)
            if checkbox_match:
                state = checkbox_match.group(1).lower()
                # Count if not checked (x or X)
                if state not in ("x", "X"):
                    count += 1
            else:
                # Regular memo entry
                count += 1
        
        return count
    
    def set_threshold(self, threshold: int) -> None:
        """Update the threshold value."""
        self.threshold = threshold
        self._threshold_crossed = self._last_pending_count >= threshold
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        stats = super().get_stats()
        stats.update({
            "pending_count": self._last_pending_count,
            "threshold": self.threshold,
            "threshold_crossed": self._threshold_crossed,
        })
        return stats
