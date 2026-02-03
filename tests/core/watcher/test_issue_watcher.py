"""
Unit tests for IssueWatcher.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from monoco.core.watcher import IssueWatcher, IssueFileEvent, WatchConfig, ChangeType
from monoco.core.scheduler import AgentEventType, EventBus


class TestIssueWatcher:
    """Test suite for IssueWatcher."""
    
    @pytest.fixture
    def sample_issue_content(self):
        """Sample issue markdown content."""
        return """---
id: FEAT-0123
type: feature
status: open
stage: doing
title: Test Issue
---

## FEAT-0123: Test Issue

- [ ] Task 1
- [ ] Task 2
"""
    
    @pytest.fixture
    def modified_issue_content(self):
        """Modified issue markdown content."""
        return """---
id: FEAT-0123
type: feature
status: open
stage: done
title: Test Issue
---

## FEAT-0123: Test Issue

- [x] Task 1
- [x] Task 2
"""
    
    @pytest.mark.asyncio
    async def test_issue_watcher_lifecycle(self, tmp_path):
        """IssueWatcher can be started and stopped."""
        config = WatchConfig(
            path=tmp_path,
            poll_interval=0.1,
        )
        
        watcher = IssueWatcher(config)
        
        assert not watcher.is_running()
        
        await watcher.start()
        assert watcher.is_running()
        
        await watcher.stop()
        assert not watcher.is_running()
    
    def test_parse_issue(self, tmp_path, sample_issue_content):
        """IssueWatcher can parse issue files."""
        config = WatchConfig(path=tmp_path)
        watcher = IssueWatcher(config)
        
        issue = watcher._parse_issue(sample_issue_content, tmp_path / "test.md")
        
        assert issue is not None
        assert issue.frontmatter.id == "FEAT-0123"
        assert issue.frontmatter.status == "open"
        assert issue.frontmatter.stage == "doing"
        assert issue.frontmatter.title == "Test Issue"
    
    def test_extract_tracked_fields(self, tmp_path, sample_issue_content):
        """IssueWatcher extracts tracked fields correctly."""
        config = WatchConfig(path=tmp_path)
        watcher = IssueWatcher(config)
        
        issue = watcher._parse_issue(sample_issue_content, tmp_path / "test.md")
        fields = watcher._extract_tracked_fields(issue)
        
        assert fields["status"] == "open"
        assert fields["stage"] == "doing"
        assert fields["title"] == "Test Issue"
    
    def test_detect_field_changes(self, tmp_path, sample_issue_content, modified_issue_content):
        """IssueWatcher detects field changes."""
        config = WatchConfig(path=tmp_path)
        watcher = IssueWatcher(config)
        
        # Parse initial issue
        issue1 = watcher._parse_issue(sample_issue_content, tmp_path / "test.md")
        watcher._issue_cache["FEAT-0123"] = watcher._extract_tracked_fields(issue1)
        
        # Parse modified issue
        issue2 = watcher._parse_issue(modified_issue_content, tmp_path / "test.md")
        changes = watcher._detect_field_changes("FEAT-0123", issue2)
        
        assert len(changes) == 1
        assert changes[0].field_name == "stage"
        assert changes[0].old_value == "doing"
        assert changes[0].new_value == "done"
    
    @pytest.mark.asyncio
    async def test_handle_new_file(self, tmp_path, sample_issue_content):
        """IssueWatcher handles new file creation."""
        config = WatchConfig(path=tmp_path)
        mock_event_bus = AsyncMock(spec=EventBus)
        watcher = IssueWatcher(config, event_bus=mock_event_bus)
        
        # Track emitted events
        emitted_events = []
        watcher.register_callback(lambda e: emitted_events.append(e))
        
        # Simulate new file
        state = {
            "content": sample_issue_content,
            "hash": "abc123",
        }
        
        await watcher._handle_new_file(tmp_path / "test.md", state)
        
        # Should emit event
        assert len(emitted_events) == 1
        assert emitted_events[0].issue_id == "FEAT-0123"
        assert emitted_events[0].change_type == ChangeType.CREATED
        
        # Should cache the issue
        assert "FEAT-0123" in watcher._issue_cache
    
    @pytest.mark.asyncio
    async def test_handle_modified_file(self, tmp_path, sample_issue_content, modified_issue_content):
        """IssueWatcher handles file modification."""
        config = WatchConfig(path=tmp_path)
        mock_event_bus = AsyncMock(spec=EventBus)
        watcher = IssueWatcher(config, event_bus=mock_event_bus)
        
        # Track emitted events
        emitted_events = []
        watcher.register_callback(lambda e: emitted_events.append(e))
        
        # Pre-populate cache
        issue1 = watcher._parse_issue(sample_issue_content, tmp_path / "test.md")
        watcher._issue_cache["FEAT-0123"] = watcher._extract_tracked_fields(issue1)
        
        # Simulate modification
        old_state = {"content": sample_issue_content, "hash": "abc123"}
        new_state = {"content": modified_issue_content, "hash": "def456"}
        
        await watcher._handle_modified_file(tmp_path / "test.md", old_state, new_state)
        
        # Should emit event
        assert len(emitted_events) == 1
        assert emitted_events[0].issue_id == "FEAT-0123"
        assert emitted_events[0].change_type == ChangeType.MODIFIED
        assert len(emitted_events[0].field_changes) == 1
    
    @pytest.mark.asyncio
    async def test_emit_field_change_event(self, tmp_path, sample_issue_content):
        """IssueWatcher emits field-specific events."""
        config = WatchConfig(path=tmp_path)
        mock_event_bus = AsyncMock(spec=EventBus)
        watcher = IssueWatcher(config, event_bus=mock_event_bus)
        
        from monoco.core.watcher.base import FieldChange, ChangeType
        
        issue = watcher._parse_issue(sample_issue_content, tmp_path / "test.md")
        field_change = FieldChange(
            field_name="stage",
            old_value="backlog",
            new_value="doing",
            change_type=ChangeType.MODIFIED,
        )
        
        await watcher._emit_field_change_event(issue, field_change)
        
        # Should publish to EventBus
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        assert call_args[0][0] == AgentEventType.ISSUE_STAGE_CHANGED
    
    def test_get_stats(self, tmp_path):
        """IssueWatcher provides statistics."""
        config = WatchConfig(path=tmp_path)
        watcher = IssueWatcher(config)
        
        stats = watcher.get_stats()
        
        assert stats["name"] == "IssueWatcher"
        assert "tracked_issues" in stats
        assert "tracked_fields" in stats
        assert stats["tracked_fields"] == IssueWatcher.TRACKED_FIELDS


class TestIssueFileEvent:
    """Test suite for IssueFileEvent."""
    
    def test_to_agent_event_type_created(self):
        """IssueFileEvent maps CREATED to ISSUE_CREATED."""
        event = IssueFileEvent(
            path=Path("/test.md"),
            change_type=ChangeType.CREATED,
            issue_id="FEAT-0123",
        )
        
        assert event.to_agent_event_type() == AgentEventType.ISSUE_CREATED
    
    def test_to_agent_event_type_stage_changed(self):
        """IssueFileEvent with stage change maps to ISSUE_STAGE_CHANGED."""
        from monoco.core.watcher.base import FieldChange
        
        event = IssueFileEvent(
            path=Path("/test.md"),
            change_type=ChangeType.MODIFIED,
            issue_id="FEAT-0123",
            field_changes=[
                FieldChange("stage", "backlog", "doing"),
            ],
        )
        
        assert event.to_agent_event_type() == AgentEventType.ISSUE_STAGE_CHANGED
    
    def test_to_agent_event_type_status_changed(self):
        """IssueFileEvent with status change maps to ISSUE_STATUS_CHANGED."""
        from monoco.core.watcher.base import FieldChange
        
        event = IssueFileEvent(
            path=Path("/test.md"),
            change_type=ChangeType.MODIFIED,
            issue_id="FEAT-0123",
            field_changes=[
                FieldChange("status", "open", "closed"),
            ],
        )
        
        assert event.to_agent_event_type() == AgentEventType.ISSUE_STATUS_CHANGED
    
    def test_to_payload(self):
        """IssueFileEvent includes issue-specific fields in payload."""
        from monoco.core.watcher.base import FieldChange
        
        event = IssueFileEvent(
            path=Path("/test.md"),
            change_type=ChangeType.MODIFIED,
            issue_id="FEAT-0123",
            field_changes=[
                FieldChange("stage", "backlog", "doing"),
            ],
        )
        
        payload = event.to_payload()
        
        assert payload["issue_id"] == "FEAT-0123"
        assert len(payload["field_changes"]) == 1
        assert payload["field_changes"][0]["field"] == "stage"
