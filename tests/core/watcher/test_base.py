"""
Unit tests for Watcher base classes.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from monoco.core.watcher.base import (
    ChangeType,
    FieldChange,
    FileEvent,
    FilesystemWatcher,
    PollingWatcher,
    WatchConfig,
)
from monoco.core.scheduler import AgentEventType, EventBus


class TestChangeType:
    """Test suite for ChangeType enum."""
    
    def test_change_type_values(self):
        """All expected change types should be defined."""
        assert ChangeType.CREATED.value == "created"
        assert ChangeType.MODIFIED.value == "modified"
        assert ChangeType.DELETED.value == "deleted"
        assert ChangeType.MOVED.value == "moved"
        assert ChangeType.RENAMED.value == "renamed"


class TestFileEvent:
    """Test suite for FileEvent dataclass."""
    
    def test_file_event_creation(self):
        """FileEvent can be created with required fields."""
        event = FileEvent(
            path=Path("/test/file.md"),
            change_type=ChangeType.CREATED,
            watcher_name="TestWatcher",
        )
        
        assert event.path == Path("/test/file.md")
        assert event.change_type == ChangeType.CREATED
        assert event.watcher_name == "TestWatcher"
        assert event.metadata == {}
    
    def test_file_event_to_payload(self):
        """FileEvent can be converted to payload dict."""
        event = FileEvent(
            path=Path("/test/file.md"),
            change_type=ChangeType.MODIFIED,
            watcher_name="TestWatcher",
            metadata={"key": "value"},
        )
        
        payload = event.to_payload()
        
        assert payload["path"] == str(Path("/test/file.md"))
        assert payload["change_type"] == "modified"
        assert payload["watcher_name"] == "TestWatcher"
        assert payload["metadata"] == {"key": "value"}
    
    def test_file_event_to_agent_event_type(self):
        """Base FileEvent returns None for agent event type."""
        event = FileEvent(
            path=Path("/test/file.md"),
            change_type=ChangeType.CREATED,
            watcher_name="TestWatcher",
        )
        
        assert event.to_agent_event_type() is None


class TestWatchConfig:
    """Test suite for WatchConfig dataclass."""
    
    def test_watch_config_defaults(self):
        """WatchConfig has sensible defaults."""
        config = WatchConfig(path=Path("/test"))
        
        assert config.path == Path("/test")
        assert config.patterns == ["*"]
        assert config.exclude_patterns == []
        assert config.recursive is True
        assert config.poll_interval == 5.0
    
    def test_watch_config_should_watch(self):
        """WatchConfig correctly filters files by pattern."""
        config = WatchConfig(
            path=Path("/test"),
            patterns=["*.md"],
            exclude_patterns=["*.tmp.md"],
        )
        
        assert config.should_watch(Path("file.md")) is True
        assert config.should_watch(Path("file.txt")) is False
        assert config.should_watch(Path("file.tmp.md")) is False


class TestFilesystemWatcher:
    """Test suite for FilesystemWatcher ABC."""
    
    def test_cannot_instantiate_abc(self):
        """Cannot instantiate abstract base class."""
        config = WatchConfig(path=Path("/test"))
        
        with pytest.raises(TypeError):
            FilesystemWatcher(config)
    
    def test_concrete_watcher_must_implement(self):
        """Concrete watchers must implement abstract methods."""
        config = WatchConfig(path=Path("/test"))
        
        class IncompleteWatcher(FilesystemWatcher):
            pass
        
        with pytest.raises(TypeError):
            IncompleteWatcher(config)
    
    @pytest.mark.asyncio
    async def test_emit_calls_callbacks(self):
        """Emit calls registered callbacks."""
        config = WatchConfig(path=Path("/test"))
        
        class TestWatcher(FilesystemWatcher):
            async def start(self):
                pass
            
            async def stop(self):
                pass
        
        watcher = TestWatcher(config)
        
        # Register callback
        callback_mock = Mock()
        watcher.register_callback(callback_mock)
        
        # Create and emit event
        event = FileEvent(
            path=Path("/test/file.md"),
            change_type=ChangeType.CREATED,
            watcher_name="TestWatcher",
        )
        
        await watcher.emit(event)
        
        # Callback should be called
        callback_mock.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_emit_publishes_to_event_bus(self):
        """Emit publishes to EventBus when available."""
        config = WatchConfig(path=Path("/test"))
        
        class TestEvent(FileEvent):
            def to_agent_event_type(self):
                return AgentEventType.ISSUE_CREATED
        
        class TestWatcher(FilesystemWatcher):
            async def start(self):
                pass
            
            async def stop(self):
                pass
        
        # Mock event bus
        mock_event_bus = AsyncMock(spec=EventBus)
        
        watcher = TestWatcher(config, event_bus=mock_event_bus)
        
        # Create and emit event
        event = TestEvent(
            path=Path("/test/file.md"),
            change_type=ChangeType.CREATED,
            watcher_name="TestWatcher",
        )
        
        await watcher.emit(event)
        
        # EventBus.publish should be called
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        assert call_args[0][0] == AgentEventType.ISSUE_CREATED


class TestPollingWatcher:
    """Test suite for PollingWatcher."""
    
    @pytest.mark.asyncio
    async def test_polling_watcher_lifecycle(self, tmp_path):
        """PollingWatcher can be started and stopped."""
        config = WatchConfig(
            path=tmp_path,
            poll_interval=0.1,
        )
        
        class TestPollingWatcher(PollingWatcher):
            async def _check_changes(self):
                pass
        
        watcher = TestPollingWatcher(config)
        
        assert not watcher.is_running()
        
        await watcher.start()
        assert watcher.is_running()
        
        await watcher.stop()
        assert not watcher.is_running()
    
    def test_scan_files(self, tmp_path):
        """PollingWatcher scans files correctly."""
        # Create test files
        (tmp_path / "file1.md").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "file3.md").write_text("content3")
        
        config = WatchConfig(
            path=tmp_path,
            patterns=["*.md"],
        )
        
        class TestPollingWatcher(PollingWatcher):
            async def _check_changes(self):
                pass
        
        watcher = TestPollingWatcher(config)
        
        states = watcher._scan_files()
        
        # Should only find .md files
        assert len(states) == 2
        assert any("file1.md" in str(p) for p in states.keys())
        assert any("file3.md" in str(p) for p in states.keys())


class TestFieldChange:
    """Test suite for FieldChange dataclass."""
    
    def test_field_change_creation(self):
        """FieldChange can be created."""
        change = FieldChange(
            field_name="status",
            old_value="open",
            new_value="closed",
            change_type=ChangeType.MODIFIED,
        )
        
        assert change.field_name == "status"
        assert change.old_value == "open"
        assert change.new_value == "closed"
        assert change.change_type == ChangeType.MODIFIED
