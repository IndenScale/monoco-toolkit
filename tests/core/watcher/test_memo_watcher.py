"""
Unit tests for MemoWatcher.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from monoco.core.watcher import MemoWatcher, MemoFileEvent, WatchConfig, ChangeType
from monoco.core.scheduler import AgentEventType, EventBus


class TestMemoWatcher:
    """Test suite for MemoWatcher."""
    
    @pytest.fixture
    def sample_memo_content(self):
        """Sample memo inbox content."""
        return """# Memo Inbox

- Idea 1
- Idea 2
- Idea 3
- Idea 4
- Idea 5
"""
    
    @pytest.fixture
    def memo_with_checkboxes(self):
        """Memo content with checkboxes."""
        return """# Memo Inbox

- [ ] Pending idea 1
- [ ] Pending idea 2
- [x] Completed idea 3
- [/] In progress idea 4
- [ ] Pending idea 5
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
    
    def test_count_pending_memos_simple(self, tmp_path):
        """MemoWatcher counts simple memo entries."""
        config = WatchConfig(path=tmp_path / "inbox.md")
        watcher = MemoWatcher(config)
        
        content = """# Memo Inbox

- Idea 1
- Idea 2
- Idea 3
"""
        
        count = watcher._count_pending_memos(content)
        assert count == 3
    
    def test_count_pending_memos_with_checkboxes(self, tmp_path):
        """MemoWatcher counts only unchecked items."""
        config = WatchConfig(path=tmp_path / "inbox.md")
        watcher = MemoWatcher(config)
        
        content = """# Memo Inbox

- [ ] Pending 1
- [x] Completed
- [ ] Pending 2
- [X] Also completed
- [/] In progress
- [-] Also in progress
"""
        
        count = watcher._count_pending_memos(content)
        assert count == 4  # 2 pending + 2 in progress
    
    def test_count_pending_memos_mixed(self, tmp_path):
        """MemoWatcher handles mixed content."""
        config = WatchConfig(path=tmp_path / "inbox.md")
        watcher = MemoWatcher(config)
        
        content = """# Memo Inbox

Some intro text

- Regular memo
- [ ] Checkbox pending
- [x] Checkbox done
- Another regular memo

## Section

- [ ] More pending
"""
        
        count = watcher._count_pending_memos(content)
        assert count == 4  # 2 regular + 2 checkbox pending (in progress counts as pending)
    
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
        watcher._last_pending_count = 0
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
        watcher._last_pending_count = 1
        await watcher._handle_count_change(3)
        
        # Should emit event but not threshold
        assert len(emitted_events) == 1
        assert emitted_events[0].pending_count == 3
        assert emitted_events[0].threshold_crossed is False
    
    @pytest.mark.asyncio
    async def test_no_event_when_count_decreases(self, tmp_path):
        """MemoWatcher doesn't emit event when count decreases."""
        memo_file = tmp_path / "inbox.md"
        memo_file.write_text("")
        
        config = WatchConfig(path=memo_file)
        watcher = MemoWatcher(config, threshold=3)
        
        # Track emitted events
        emitted_events = []
        watcher.register_callback(lambda e: emitted_events.append(e))
        
        # Simulate decreasing count (5 -> 2)
        watcher._last_pending_count = 5
        watcher._threshold_crossed = True
        await watcher._handle_count_change(2)
        
        # Should not emit event
        assert len(emitted_events) == 0
    
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
        
        watcher._last_pending_count = 3
        watcher._threshold_crossed = False
        
        stats = watcher.get_stats()
        
        assert stats["name"] == "MemoWatcher"
        assert stats["pending_count"] == 3
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
