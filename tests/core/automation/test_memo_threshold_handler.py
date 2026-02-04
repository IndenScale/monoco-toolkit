"""
Unit tests for MemoThresholdHandler (Signal Queue Model).

Tests the "consume on read" semantics of FEAT-0165:
- Memos are loaded and cleared BEFORE scheduling Architect
- Prompt contains embedded memos, not file path
- File cleared = consumed, no state needed
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from monoco.core.automation.handlers import MemoThresholdHandler
from monoco.core.scheduler.events import AgentEvent, AgentEventType
from monoco.core.scheduler.base import AgentScheduler
from monoco.features.memo.models import Memo


class TestMemoThresholdHandler:
    """Test suite for MemoThresholdHandler Signal Queue semantics."""
    
    @pytest.fixture
    def mock_scheduler(self):
        """Create a mock AgentScheduler."""
        scheduler = MagicMock(spec=AgentScheduler)
        scheduler.schedule = AsyncMock(return_value="session-123")
        return scheduler
    
    @pytest.fixture
    def handler(self, mock_scheduler):
        """Create a MemoThresholdHandler instance."""
        return MemoThresholdHandler(scheduler=mock_scheduler, threshold=5)
    
    @pytest.fixture
    def memo_event(self):
        """Create a sample MEMO_THRESHOLD event."""
        return AgentEvent(
            type=AgentEventType.MEMO_THRESHOLD,
            payload={
                "path": "Memos/inbox.md",
                "pending_count": 5,
                "threshold": 5,
            },
            timestamp=datetime.now(),
        )
    
    def test_should_handle_threshold_crossed(self, handler, memo_event):
        """Handler should handle events above threshold."""
        assert handler._should_handle(memo_event) is True
    
    def test_should_not_handle_below_threshold(self, handler):
        """Handler should not handle events below threshold."""
        event = AgentEvent(
            type=AgentEventType.MEMO_THRESHOLD,
            payload={
                "path": "Memos/inbox.md",
                "pending_count": 3,
                "threshold": 5,
            },
            timestamp=datetime.now(),
        )
        assert handler._should_handle(event) is False
    
    @pytest.mark.asyncio
    async def test_handle_consumes_memos_before_scheduling(self, handler, mock_scheduler, tmp_path):
        """CRITICAL: Memos are loaded and cleared BEFORE scheduling Architect."""
        # Setup inbox with memos (need both Memos and Issues directories)
        issues_dir = tmp_path / "Issues"
        issues_dir.mkdir()
        memos_dir = tmp_path / "Memos"
        memos_dir.mkdir()
        inbox_path = memos_dir / "inbox.md"
        inbox_path.write_text("""# Monoco Memos Inbox

## [abc123] 2026-01-15 10:00:00
- **Type**: insight

Test memo content
""", encoding="utf-8")
        
        event = AgentEvent(
            type=AgentEventType.MEMO_THRESHOLD,
            payload={
                "path": str(inbox_path),
                "pending_count": 1,
                "threshold": 5,
            },
            timestamp=datetime.now(),
        )
        
        # Execute
        result = await handler._handle(event)
        
        # Verify: Inbox should be cleared
        content_after = inbox_path.read_text(encoding="utf-8")
        assert "Test memo content" not in content_after
        assert "# Monoco Memos Inbox" in content_after
        
        # Verify: Architect was scheduled
        mock_scheduler.schedule.assert_called_once()
        call_args = mock_scheduler.schedule.call_args[0][0]
        assert "Test memo content" in call_args.prompt
    
    @pytest.mark.asyncio
    async def test_handle_embeds_memos_in_prompt(self, handler, mock_scheduler, tmp_path):
        """Memos are embedded in prompt, not read from file."""
        # Setup inbox (need both Memos and Issues directories)
        issues_dir = tmp_path / "Issues"
        issues_dir.mkdir()
        memos_dir = tmp_path / "Memos"
        memos_dir.mkdir()
        inbox_path = memos_dir / "inbox.md"
        inbox_path.write_text("""# Monoco Memos Inbox

## [abc123] 2026-01-15 10:00:00
- **Type**: insight
- **Source**: cli

First memo

## [def456] 2026-01-15 10:30:00
- **Type**: feature
- **Source**: agent

Second memo
""", encoding="utf-8")
        
        event = AgentEvent(
            type=AgentEventType.MEMO_THRESHOLD,
            payload={
                "path": str(inbox_path),
                "pending_count": 2,
                "threshold": 5,
            },
            timestamp=datetime.now(),
        )
        
        # Execute
        result = await handler._handle(event)
        
        # Verify: Prompt contains embedded memos
        call_args = mock_scheduler.schedule.call_args[0][0]
        prompt = call_args.prompt
        
        assert "First memo" in prompt
        assert "Second memo" in prompt
        assert "abc123" in prompt
        assert "def456" in prompt
        assert "Signal Queue Model" in prompt
    
    @pytest.mark.asyncio
    async def test_handle_empty_inbox(self, handler, mock_scheduler, tmp_path):
        """Handler handles empty inbox gracefully."""
        issues_dir = tmp_path / "Issues"
        issues_dir.mkdir()
        memos_dir = tmp_path / "Memos"
        memos_dir.mkdir()
        inbox_path = memos_dir / "inbox.md"
        inbox_path.write_text("# Monoco Memos Inbox\n\n", encoding="utf-8")
        
        event = AgentEvent(
            type=AgentEventType.MEMO_THRESHOLD,
            payload={
                "path": str(inbox_path),
                "pending_count": 0,
                "threshold": 5,
            },
            timestamp=datetime.now(),
        )
        
        # Execute - should not fail
        result = await handler._handle(event)
        
        # Should return None for empty inbox
        assert result is None
        mock_scheduler.schedule.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_nonexistent_inbox(self, handler, mock_scheduler, tmp_path):
        """Handler handles non-existent inbox gracefully."""
        inbox_path = tmp_path / "Memos" / "inbox.md"
        
        event = AgentEvent(
            type=AgentEventType.MEMO_THRESHOLD,
            payload={
                "path": str(inbox_path),
                "pending_count": 5,
                "threshold": 5,
            },
            timestamp=datetime.now(),
        )
        
        # Execute
        result = await handler._handle(event)
        
        # Should return None for non-existent inbox
        assert result is None
        mock_scheduler.schedule.assert_not_called()
    
    def test_load_and_clear_memos(self, handler, tmp_path):
        """Test the load_and_clear_memos helper method."""
        # Setup (need both Memos and Issues directories)
        issues_dir = tmp_path / "Issues"
        issues_dir.mkdir()
        memos_dir = tmp_path / "Memos"
        memos_dir.mkdir()
        inbox_path = memos_dir / "inbox.md"
        inbox_path.write_text("""# Monoco Memos Inbox

## [abc123] 2026-01-15 10:00:00
- **Type**: insight

Test memo
""", encoding="utf-8")
        
        # Execute
        memos = handler._load_and_clear_memos(inbox_path)
        
        # Verify: Memos loaded
        assert len(memos) == 1
        assert memos[0].uid == "abc123"
        assert memos[0].content == "Test memo"
        
        # Verify: File cleared
        content = inbox_path.read_text(encoding="utf-8")
        assert content == "# Monoco Memos Inbox\n\n"
    
    def test_load_and_clear_empty_inbox(self, handler, tmp_path):
        """Test load_and_clear with empty inbox."""
        memos_dir = tmp_path / "Memos"
        memos_dir.mkdir()
        inbox_path = memos_dir / "inbox.md"
        inbox_path.write_text("# Monoco Memos Inbox\n\n", encoding="utf-8")
        
        memos = handler._load_and_clear_memos(inbox_path)
        
        assert len(memos) == 0
    
    def test_build_prompt_with_memos(self, handler):
        """Test prompt building with embedded memos."""
        memos = [
            Memo(
                uid="abc123",
                content="First idea",
                timestamp=datetime(2026, 1, 15, 10, 0, 0),
                type="insight",
                source="cli",
                author="User",
            ),
            Memo(
                uid="def456",
                content="Second idea",
                timestamp=datetime(2026, 1, 15, 10, 30, 0),
                type="feature",
                source="agent",
                author="Assistant",
                context="file.py:42",
            ),
        ]
        
        prompt = handler._build_prompt("Memos/inbox.md", memos)
        
        # Verify prompt structure
        assert "Architect" in prompt
        assert "Signal Queue Model" in prompt
        assert "First idea" in prompt
        assert "Second idea" in prompt
        assert "abc123" in prompt
        assert "def456" in prompt
        assert "file.py:42" in prompt
        assert "Consumed Memos" in prompt


class TestMemoSignalQueueIdempotency:
    """Test idempotency properties of Signal Queue model."""
    
    @pytest.mark.asyncio
    async def test_restart_does_not_reprocess(self, tmp_path):
        """CRITICAL: After restart, consumed memos are not reprocessed.
        
        This is the key behavior that Signal Queue Model fixes:
        - Old model: relied on _last_processed_count in memory
        - New model: file cleared = consumed, no state needed
        """
        # Setup (need both Memos and Issues directories)
        issues_dir = tmp_path / "Issues"
        issues_dir.mkdir()
        memos_dir = tmp_path / "Memos"
        memos_dir.mkdir()
        inbox_path = memos_dir / "inbox.md"
        
        # Setup: Add a memo
        inbox_path.write_text("""# Monoco Memos Inbox

## [abc123] 2026-01-15 10:00:00
- **Type**: insight

Test memo
""", encoding="utf-8")
        
        mock_scheduler = MagicMock(spec=AgentScheduler)
        mock_scheduler.schedule = AsyncMock(return_value="session-1")
        
        handler1 = MemoThresholdHandler(scheduler=mock_scheduler, threshold=1)
        
        event = AgentEvent(
            type=AgentEventType.MEMO_THRESHOLD,
            payload={
                "path": str(inbox_path),
                "pending_count": 1,
                "threshold": 1,
            },
            timestamp=datetime.now(),
        )
        
        # First handler consumes the memo
        await handler1._handle(event)
        
        # Verify: File is cleared
        content = inbox_path.read_text(encoding="utf-8")
        assert "Test memo" not in content
        
        # Simulate restart: Create new handler (no memory of previous state)
        handler2 = MemoThresholdHandler(scheduler=mock_scheduler, threshold=1)
        
        # New event with same payload (simulating watcher detecting file)
        event2 = AgentEvent(
            type=AgentEventType.MEMO_THRESHOLD,
            payload={
                "path": str(inbox_path),
                "pending_count": 1,  # Old model would skip this
                "threshold": 1,
            },
            timestamp=datetime.now(),
        )
        
        # Second handler processes the event
        result = await handler2._handle(event2)
        
        # Verify: Second handler sees empty inbox and does nothing
        # (because file is already cleared)
        assert result is None
        
        # Scheduler should only be called once (by first handler)
        assert mock_scheduler.schedule.call_count == 1
