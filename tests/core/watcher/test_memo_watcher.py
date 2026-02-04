"""
Unit tests for MemoWatcher (Signal Queue Model).
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from monoco.core.watcher import MemoWatcher, MemoFileEvent, WatchConfig, ChangeType
from monoco.core.scheduler import AgentEventType, EventBus


class TestMemoWatcher:
    """Test suite for MemoWatcher (Signal Queue Model)."""
    
    @pytest.fixture
    def sample_memo_content(self):
        """Sample memo inbox content with headers."""
        return """# Monoco Memos Inbox

## [abc123] 2026-01-15 10:00:00
- **Type**: insight

Idea 1

## [def456] 2026-01-15 10:30:00
- **Type**: feature

Idea 2

## [ghi789] 2026-01-15 11:00:00
- **Type**: bug

Idea 3
"""
    
    @pytest.mark.asyncio
    async def test_memo_watcher_lifecycle(self, tmp_path):
        """MemoWatcher can be started and stopped."""
        memo_file = tmp_path / "inbox.md"
        memo_file.write_text("")
        
        config = WatchConfig(
            path=memo_file,
            poll_interval=0.1,
        )
        
        watcher = MemoWatcher(config)
        
        assert not watcher.is_running()
        
        await watcher.start()
        assert watcher.is_running()
        
        await watcher.stop()
        assert not watcher.is_running()
    
    def test_count_memos_simple(self, tmp_path):
        """MemoWatcher counts memos by header pattern."""
        config = WatchConfig(path=tmp_path / "inbox.md")
        watcher = MemoWatcher(config)
        
        content = """# Monoco Memos Inbox

## [abc123] 2026-01-15 10:00:00
Content 1

## [def456] 2026-01-15 10:30:00
Content 2

## [abc789] 2026-01-15 11:00:00
Content 3
"""
        
        count = watcher._count_memos(content)
        assert count == 3
    
    def test_count_memos_empty(self, tmp_path):
        """MemoWatcher returns 0 for empty or header-only content."""
        config = WatchConfig(path=tmp_path / "inbox.md")
        watcher = MemoWatcher(config)
        
        # Empty content
        assert watcher._count_memos("") == 0
        assert watcher._count_memos("   ") == 0
        
        # Header only (no memos)
        header_only = "# Monoco Memos Inbox\n\n"
        assert watcher._count_memos(header_only) == 0
    
    def test_count_memos_with_metadata(self, tmp_path):
        """MemoWatcher counts memos with metadata correctly."""
        config = WatchConfig(path=tmp_path / "inbox.md")
        watcher = MemoWatcher(config)
        
        content = """# Monoco Memos Inbox

## [abc123] 2026-01-15 10:00:00
- **From**: User
- **Type**: insight
- **Context**: `file.py:10`

This is the memo content
with multiple lines

## [def456] 2026-01-15 10:30:00
- **Type**: feature

Another memo
"""
        
        count = watcher._count_memos(content)
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_threshold_crossing(self, tmp_path):
        """MemoWatcher emits event when threshold is crossed."""
        memo_file = tmp_path / "inbox.md"
        memo_file.write_text("")
        
        config = WatchConfig(path=memo_file)
        mock_event_bus = AsyncMock(spec=EventBus)
        watcher = MemoWatcher(config, event_bus=mock_event_bus, threshold=3)
        
        # Track emitted events
        emitted_events = []
        watcher.register_callback(lambda e: emitted_events.append(e))
        
        # Simulate crossing threshold (0 -> 4)
        watcher._last_memo_count = 0
        await watcher._handle_count_change(4)
        
        # Should emit threshold event
        assert len(emitted_events) == 1
        assert emitted_events[0].pending_count == 4
        assert emitted_events[0].threshold_crossed is True
        assert watcher._threshold_crossed is True
    
    @pytest.mark.asyncio
    async def test_memos_added_below_threshold(self, tmp_path):
        """MemoWatcher emits event when memos added but threshold not crossed."""
        memo_file = tmp_path / "inbox.md"
        memo_file.write_text("")
        
        config = WatchConfig(path=memo_file)
        watcher = MemoWatcher(config, threshold=10)
        
        # Track emitted events
        emitted_events = []
        watcher.register_callback(lambda e: emitted_events.append(e))
        
        # Simulate adding memos (1 -> 3)
        watcher._last_memo_count = 1
        await watcher._handle_count_change(3)
        
        # Should emit event but not threshold
        assert len(emitted_events) == 1
        assert emitted_events[0].pending_count == 3
        assert emitted_events[0].threshold_crossed is False
    
    @pytest.mark.asyncio
    async def test_no_event_when_count_decreases(self, tmp_path):
        """MemoWatcher doesn't emit event when count decreases without consumption."""
        memo_file = tmp_path / "inbox.md"
        memo_file.write_text("")
        
        config = WatchConfig(path=memo_file)
        watcher = MemoWatcher(config, threshold=3)
        
        # Track emitted events
        emitted_events = []
        watcher.register_callback(lambda e: emitted_events.append(e))
        
        # Simulate decreasing count (5 -> 2)
        watcher._last_memo_count = 5
        watcher._threshold_crossed = True
        await watcher._handle_count_change(2)
        
        # Should not emit event for simple decrease
        assert len(emitted_events) == 0
    
    @pytest.mark.asyncio
    async def test_inbox_cleared_no_event(self, tmp_path):
        """MemoWatcher doesn't emit event when inbox is cleared (consumed).
        
        Note: State update (_last_memo_count) is done by _check_changes, 
        not _handle_count_change. This test verifies no event is emitted.
        """
        memo_file = tmp_path / "inbox.md"
        memo_file.write_text("")
        
        config = WatchConfig(path=memo_file)
        watcher = MemoWatcher(config, threshold=5)
        
        # Track emitted events
        emitted_events = []
        watcher.register_callback(lambda e: emitted_events.append(e))
        
        # Simulate inbox cleared (3 -> 0)
        watcher._last_memo_count = 3
        watcher._threshold_crossed = False
        await watcher._handle_count_change(0)
        
        # Should not emit an event when count decreases to 0
        assert len(emitted_events) == 0
        # _last_memo_count is not updated by _handle_count_change
        # It's updated by _check_changes which calls _handle_count_change
    
    def test_set_threshold(self, tmp_path):
        """Threshold can be updated dynamically."""
        memo_file = tmp_path / "inbox.md"
        config = WatchConfig(path=memo_file)
        watcher = MemoWatcher(config, threshold=5)
        
        assert watcher.threshold == 5
        
        watcher.set_threshold(10)
        
        assert watcher.threshold == 10
    
    def test_get_stats(self, tmp_path):
        """MemoWatcher provides statistics."""
        memo_file = tmp_path / "inbox.md"
        config = WatchConfig(path=memo_file)
        watcher = MemoWatcher(config, threshold=5)
        
        watcher._last_memo_count = 3
        watcher._threshold_crossed = False
        
        stats = watcher.get_stats()
        
        assert stats["name"] == "MemoWatcher"
        assert stats["memo_count"] == 3
        assert stats["threshold"] == 5
        assert stats["threshold_crossed"] is False


class TestMemoFileEvent:
    """Test suite for MemoFileEvent."""
    
    def test_to_agent_event_type_threshold(self):
        """MemoFileEvent above threshold maps to MEMO_THRESHOLD."""
        event = MemoFileEvent(
            path=Path("/inbox.md"),
            change_type=ChangeType.MODIFIED,
            pending_count=5,
            threshold=5,
        )
        
        assert event.to_agent_event_type() == AgentEventType.MEMO_THRESHOLD
    
    def test_to_agent_event_type_below_threshold(self):
        """MemoFileEvent below threshold maps to MEMO_CREATED."""
        event = MemoFileEvent(
            path=Path("/inbox.md"),
            change_type=ChangeType.MODIFIED,
            pending_count=3,
            threshold=5,
        )
        
        assert event.to_agent_event_type() == AgentEventType.MEMO_CREATED
    
    def test_to_payload(self):
        """MemoFileEvent includes memo-specific fields in payload."""
        event = MemoFileEvent(
            path=Path("/inbox.md"),
            change_type=ChangeType.MODIFIED,
            pending_count=5,
            threshold=5,
            metadata={"previous_count": 3},
        )
        
        payload = event.to_payload()
        
        assert payload["pending_count"] == 5
        assert payload["threshold"] == 5
        assert payload["threshold_crossed"] is True
