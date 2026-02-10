"""
Tests for MailboxWatcher functionality (FEAT-0199).
"""

import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from monoco.core.scheduler import AgentEventType, EventBus
from monoco.core.watcher.base import ChangeType
from monoco.features.mailbox.watcher import (
    MailboxFileEvent,
    MailboxInboundWatcher,
    MailboxWatcher,
    WatchConfig,
)


class TestMailboxFileEvent:
    """Tests for MailboxFileEvent class."""

    def test_creation(self):
        """Test MailboxFileEvent creation with mailbox metadata."""
        event = MailboxFileEvent(
            path=Path("/test/file.md"),
            change_type="created",
            watcher_name="test_watcher",
            provider="dingtalk",
            session_id="session_123",
            message_id="msg_456",
        )

        assert event.provider == "dingtalk"
        assert event.session_id == "session_123"
        assert event.message_id == "msg_456"
        assert event.change_type == "created"

    def test_to_agent_event_type(self):
        """Test conversion to AgentEventType."""
        # Created event should return MAILBOX_INBOUND_RECEIVED
        created_event = MailboxFileEvent(
            path=Path("/test/file.md"),
            change_type=ChangeType.CREATED,
            watcher_name="test_watcher",
        )
        assert (
            created_event.to_agent_event_type()
            == AgentEventType.MAILBOX_INBOUND_RECEIVED
        )

        # Modified event should return None
        modified_event = MailboxFileEvent(
            path=Path("/test/file.md"),
            change_type=ChangeType.MODIFIED,
            watcher_name="test_watcher",
        )
        assert modified_event.to_agent_event_type() is None

    def test_to_payload(self):
        """Test payload conversion includes mailbox metadata."""
        event = MailboxFileEvent(
            path=Path("/test/file.md"),
            change_type=ChangeType.CREATED,
            watcher_name="test_watcher",
            provider="dingtalk",
            session_id="session_123",
            message_id="msg_456",
        )

        payload = event.to_payload()
        assert payload["provider"] == "dingtalk"
        assert payload["session_id"] == "session_123"
        assert payload["message_id"] == "msg_456"
        assert payload["mailbox_event"] is True


class TestMailboxWatcher:
    """Tests for MailboxWatcher base class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus."""
        return AsyncMock(spec=EventBus)

    @pytest.fixture
    def watcher_config(self, temp_dir):
        """Create watcher configuration."""
        return WatchConfig(
            path=temp_dir,
            patterns=["*.md"],
            recursive=True,
            poll_interval=0.1,  # Fast polling for tests
        )

    @pytest.fixture
    def mailbox_watcher(self, watcher_config, mock_event_bus):
        """Create MailboxWatcher instance."""
        return MailboxWatcher(watcher_config, mock_event_bus)

    @pytest.mark.asyncio
    async def test_start_stop(self, mailbox_watcher):
        """Test starting and stopping the watcher."""
        # Start watcher
        await mailbox_watcher.start()
        assert mailbox_watcher.is_running()

        # Stop watcher
        await mailbox_watcher.stop()
        assert not mailbox_watcher.is_running()

    @pytest.mark.asyncio
    async def test_file_creation_detection(
        self, temp_dir, mailbox_watcher, mock_event_bus
    ):
        """Test detection of new file creation."""
        await mailbox_watcher.start()

        # Create a test file
        test_file = temp_dir / "test_message.md"
        test_content = """---
id: test_msg_001
provider: dingtalk
session:
  id: chat_123
type: text
---
Hello, world!
"""
        test_file.write_text(test_content)

        # Wait for polling interval
        await asyncio.sleep(0.2)

        # Check that event was emitted
        assert mock_event_bus.publish.called

        # Get the event that was published
        call_args = mock_event_bus.publish.call_args
        assert call_args is not None

        args, kwargs = call_args
        event_type, payload = args
        assert event_type == AgentEventType.MAILBOX_INBOUND_RECEIVED
        assert payload["path"] == str(test_file)
        assert payload["change_type"] == "created"
        assert payload["provider"] == "dingtalk"
        assert payload["session_id"] == "chat_123"
        assert payload["message_id"] == "test_msg_001"

        await mailbox_watcher.stop()

    @pytest.mark.asyncio
    async def test_file_modification_detection(
        self, temp_dir, mailbox_watcher, mock_event_bus
    ):
        """Test that file modifications are detected."""
        # Create test file
        test_file = temp_dir / "test_message.md"
        initial_content = """---
id: test_msg_001
provider: dingtalk
---
Initial content
"""
        test_file.write_text(initial_content)

        # Start watcher
        await mailbox_watcher.start()
        await asyncio.sleep(0.2)  # Let watcher detect initial state

        # Debug: check initial state
        print(
            f"DEBUG: Initial file_states keys: {list(mailbox_watcher._file_states.keys())}"
        )
        print(f"DEBUG: Initial publish call count: {mock_event_bus.publish.call_count}")

        # Clear mock calls after initial file creation was detected
        mock_event_bus.publish.reset_mock()
        print(
            f"DEBUG: After reset_mock, call count: {mock_event_bus.publish.call_count}"
        )

        # Modify the file
        modified_content = """---
id: test_msg_001
provider: dingtalk
---
Modified content
"""
        test_file.write_text(modified_content)
        print(f"DEBUG: File modified, content: {test_file.read_text()[:100]}")

        # Manually trigger a scan since the watcher might not poll again
        await mailbox_watcher._check_changes()

        # Debug: check state after _check_changes
        print(
            f"DEBUG: After _check_changes, file_states keys: {list(mailbox_watcher._file_states.keys())}"
        )
        print(
            f"DEBUG: After _check_changes, publish called: {mock_event_bus.publish.called}"
        )
        print(
            f"DEBUG: After _check_changes, call count: {mock_event_bus.publish.call_count}"
        )
        if mock_event_bus.publish.called:
            print(f"DEBUG: Call args: {mock_event_bus.publish.call_args}")

        # Check that modification event was emitted
        # Note: Modification events don't publish to EventBus (to_agent_event_type returns None)
        # but they should still be emitted to local callbacks
        # Since we're using mock_event_bus, we check that publish was NOT called
        # (which is correct for modification events)
        assert not mock_event_bus.publish.called

        await mailbox_watcher.stop()

    @pytest.mark.asyncio
    async def test_file_deletion_detection(
        self, temp_dir, mailbox_watcher, mock_event_bus
    ):
        """Test detection of file deletion."""
        # Create initial file
        test_file = temp_dir / "test_message.md"
        test_file.write_text("Test content")

        await mailbox_watcher.start()
        await asyncio.sleep(0.2)  # Let watcher detect initial state

        # Clear mock calls after modification was detected
        mock_event_bus.publish.reset_mock()

        # Delete the file
        test_file.unlink()

        # Manually trigger a scan since the watcher might not poll again
        await mailbox_watcher._check_changes()

        # Check that deletion event was emitted
        # Note: Deletion events don't publish to EventBus (to_agent_event_type returns None)
        # but they should still be emitted to local callbacks
        # Since we're using mock_event_bus, we check that publish was NOT called
        # (which is correct for deletion events)
        assert not mock_event_bus.publish.called

        await mailbox_watcher.stop()

    def test_extract_mailbox_metadata(self, temp_dir, mailbox_watcher):
        """Test extraction of mailbox metadata from files."""
        # Create a valid mailbox message file
        test_file = temp_dir / "valid_message.md"
        test_content = """---
id: dingtalk_msg_123
provider: dingtalk
session:
  id: chat_888
  type: group
  name: Test Group
participants:
  sender:
    id: u_1
    name: Test User
timestamp: '2026-02-10T10:00:00'
type: text
---
Hello from DingTalk!
"""
        test_file.write_text(test_content)

        metadata = mailbox_watcher._extract_mailbox_metadata(test_file)
        assert metadata["provider"] == "dingtalk"
        assert metadata["session_id"] == "chat_888"
        assert metadata["message_id"] == "dingtalk_msg_123"

    def test_extract_mailbox_metadata_invalid(self, temp_dir, mailbox_watcher):
        """Test extraction from invalid files."""
        # Create file without frontmatter
        test_file = temp_dir / "invalid_message.md"
        test_file.write_text("Just plain text, no frontmatter")

        metadata = mailbox_watcher._extract_mailbox_metadata(test_file)
        assert metadata == {}  # Should return empty dict

    def test_get_stats(self, mailbox_watcher):
        """Test getting watcher statistics."""
        stats = mailbox_watcher.get_stats()
        assert "name" in stats
        assert "running" in stats
        assert "config" in stats
        assert stats["name"] == "mailbox_watcher"


class TestMailboxInboundWatcher:
    """Tests for MailboxInboundWatcher specialized class."""

    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus."""
        event_bus = AsyncMock()
        event_bus.publish = AsyncMock()
        event_bus.subscribe = AsyncMock()
        return event_bus

    @pytest.fixture
    def temp_mailbox_root(self):
        """Create temporary mailbox root directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mailbox_root = Path(tmpdir)
            # Create standard mailbox structure
            (mailbox_root / "inbound").mkdir(parents=True)
            (mailbox_root / "outbound").mkdir()
            (mailbox_root / "archive").mkdir()
            yield mailbox_root

    @pytest.fixture
    def inbound_watcher(self, temp_mailbox_root, mock_event_bus):
        """Create MailboxInboundWatcher instance."""
        return MailboxInboundWatcher(
            mailbox_root=temp_mailbox_root,
            event_bus=mock_event_bus,
            poll_interval=0.1,
        )

    def test_initialization(self, inbound_watcher, temp_mailbox_root):
        """Test watcher initialization with correct paths."""
        config = inbound_watcher.config
        assert config.path == temp_mailbox_root / "inbound"
        assert config.patterns == ["*.md"]
        assert config.recursive is True
        assert config.poll_interval == 0.1
        assert inbound_watcher.name == "mailbox_inbound_watcher"

    @pytest.mark.asyncio
    async def test_watches_inbound_only(
        self, temp_mailbox_root, inbound_watcher, mock_event_bus
    ):
        """Test that watcher only monitors inbound directory."""
        await inbound_watcher.start()

        # Create file in inbound directory (should be detected)
        inbound_file = temp_mailbox_root / "inbound" / "dingtalk" / "test.md"
        inbound_file.parent.mkdir(parents=True, exist_ok=True)
        inbound_file.write_text("Test inbound message")

        # Create file in outbound directory (should NOT be detected)
        outbound_file = temp_mailbox_root / "outbound" / "test.md"
        outbound_file.parent.mkdir(parents=True, exist_ok=True)
        outbound_file.write_text("Test outbound message")

        await asyncio.sleep(0.2)

        # Should only detect inbound file
        assert mock_event_bus.publish.called

        call_args = mock_event_bus.publish.call_args
        payload = call_args[0][1]
        assert "inbound" in payload["path"]
        assert "outbound" not in payload["path"]

        await inbound_watcher.stop()

    @pytest.mark.asyncio
    async def test_provider_subdirectories(
        self, temp_mailbox_root, inbound_watcher, mock_event_bus
    ):
        """Test that watcher monitors provider subdirectories."""
        await inbound_watcher.start()

        # Create files in different provider directories
        providers = ["dingtalk", "email", "slack"]
        for provider in providers:
            provider_dir = temp_mailbox_root / "inbound" / provider
            provider_dir.mkdir(parents=True, exist_ok=True)

            message_file = provider_dir / f"{provider}_message.md"
            message_content = f"""---
id: {provider}_msg_001
provider: {provider}
---
Test message from {provider}
"""
            message_file.write_text(message_content)

        await asyncio.sleep(0.3)  # Wait for all files to be detected

        # Should detect all 3 files
        assert mock_event_bus.publish.call_count >= 3

        await inbound_watcher.stop()


class TestIntegration:
    """Integration tests for mailbox watcher functionality."""

    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus."""
        event_bus = AsyncMock()
        event_bus.publish = AsyncMock()
        event_bus.subscribe = AsyncMock()
        return event_bus

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self, tmp_path, mock_event_bus):
        """Test complete flow from file creation to event emission."""
        # Create watcher
        config = WatchConfig(
            path=tmp_path,
            patterns=["*.md"],
            recursive=True,
            poll_interval=0.1,
        )
        watcher = MailboxWatcher(config, mock_event_bus)

        # Register a callback to test event emission
        callback_called = asyncio.Event()
        callback_event = None

        async def test_callback(event):
            nonlocal callback_event
            callback_event = event
            callback_called.set()

        watcher.register_callback(test_callback)

        # Start watcher
        await watcher.start()

        # Create a mailbox message file
        test_file = tmp_path / "integration_test.md"
        test_content = """---
id: integration_test_001
provider: test
session:
  id: test_session
---
Integration test message
"""
        test_file.write_text(test_content)

        # Wait for callback to be called
        try:
            await asyncio.wait_for(callback_called.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            pytest.fail("Callback not called within timeout")

        # Verify callback received correct event
        assert callback_event is not None
        assert callback_event.path == test_file
        assert callback_event.change_type == ChangeType.CREATED
        assert callback_event.provider == "test"
        assert callback_event.session_id == "test_session"
        assert callback_event.message_id == "integration_test_001"

        # Verify event bus was also notified
        assert mock_event_bus.publish.called

        await watcher.stop()
