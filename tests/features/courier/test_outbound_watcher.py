"""
Tests for OutboundWatcher - outbound message polling and detection.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml

from monoco.features.courier.outbound_watcher import (
    OutboundWatcher,
    OutboundMessageEntry,
)
from monoco.features.connector.protocol.schema import Provider


@pytest.fixture
def temp_mailbox():
    """Create a temporary mailbox directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mailbox = Path(tmpdir) / "mailbox"
        outbound = mailbox / "outbound"
        outbound.mkdir(parents=True)
        
        # Create provider directories
        for provider in OutboundWatcher.SUPPORTED_PROVIDERS:
            (outbound / provider.value).mkdir(exist_ok=True)
        
        yield mailbox


@pytest.fixture
def watcher(temp_mailbox):
    """Create an OutboundWatcher instance."""
    outbound_path = temp_mailbox / "outbound"
    watcher = OutboundWatcher(outbound_path=outbound_path, poll_interval=1.0)
    watcher.initialize()
    return watcher


def create_test_message(
    path: Path,
    msg_id: str,
    provider: str = "dingtalk",
    status: str = "pending",
    retry_count: int = 0,
    next_retry_at: datetime = None,
    content: str = "Test message content",
):
    """Helper to create a test message file."""
    frontmatter = {
        "id": msg_id,
        "to": "test_user",
        "provider": provider,
        "content_type": "text",
        "status": status,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "retry_count": retry_count,
    }
    
    if next_retry_at:
        frontmatter["next_retry_at"] = next_retry_at.isoformat() + "Z"
    
    content_yaml = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    full_content = f"---\n{content_yaml}---\n{content}\n"
    
    path.write_text(full_content, encoding="utf-8")
    return path


class TestOutboundWatcher:
    """Tests for OutboundWatcher class."""

    def test_initialization(self, temp_mailbox):
        """Test watcher initialization."""
        outbound_path = temp_mailbox / "outbound"
        watcher = OutboundWatcher(outbound_path=outbound_path)
        watcher.initialize()
        
        # Check that provider directories exist
        for provider in OutboundWatcher.SUPPORTED_PROVIDERS:
            assert (outbound_path / provider.value).exists()

    def test_scan_empty_directory(self, watcher):
        """Test scanning an empty directory."""
        pending = watcher.scan()
        assert pending == []

    def test_scan_pending_message(self, watcher, temp_mailbox):
        """Test scanning finds pending messages."""
        provider_dir = temp_mailbox / "outbound" / "dingtalk"
        create_test_message(
            provider_dir / "test_msg.md",
            msg_id="out_dingtalk_001",
            status="pending",
        )
        
        pending = watcher.scan()
        
        assert len(pending) == 1
        assert pending[0].id == "out_dingtalk_001"
        assert pending[0].provider == Provider.DINGTALK
        assert pending[0].status == "pending"

    def test_scan_skips_sent_messages(self, watcher, temp_mailbox):
        """Test that sent messages are skipped."""
        provider_dir = temp_mailbox / "outbound" / "dingtalk"
        
        # Create sent message
        create_test_message(
            provider_dir / "sent_msg.md",
            msg_id="sent_msg",
            status="sent",
        )
        
        # Create pending message
        create_test_message(
            provider_dir / "pending_msg.md",
            msg_id="pending_msg",
            status="pending",
        )
        
        pending = watcher.scan()
        
        assert len(pending) == 1
        assert pending[0].id == "pending_msg"

    def test_scan_skips_sending_messages(self, watcher, temp_mailbox):
        """Test that sending messages are skipped."""
        provider_dir = temp_mailbox / "outbound" / "dingtalk"
        
        create_test_message(
            provider_dir / "sending_msg.md",
            msg_id="sending_msg",
            status="sending",
        )
        
        pending = watcher.scan()
        assert len(pending) == 0

    def test_scan_skips_future_retry(self, watcher, temp_mailbox):
        """Test that messages with future retry are skipped."""
        provider_dir = temp_mailbox / "outbound" / "dingtalk"
        
        future_time = datetime.utcnow() + timedelta(hours=1)
        create_test_message(
            provider_dir / "retry_later.md",
            msg_id="retry_later",
            status="pending",
            retry_count=1,
            next_retry_at=future_time,
        )
        
        pending = watcher.scan()
        assert len(pending) == 0

    def test_scan_includes_past_retry(self, watcher, temp_mailbox):
        """Test that messages with past retry are included."""
        provider_dir = temp_mailbox / "outbound" / "dingtalk"
        
        past_time = datetime.utcnow() - timedelta(hours=1)
        create_test_message(
            provider_dir / "retry_now.md",
            msg_id="retry_now",
            status="pending",
            retry_count=1,
            next_retry_at=past_time,
        )
        
        pending = watcher.scan()
        assert len(pending) == 1
        assert pending[0].id == "retry_now"

    def test_scan_skips_max_retries(self, watcher, temp_mailbox):
        """Test that messages exceeding max retries are skipped."""
        from monoco.features.connector.protocol.constants import MAX_RETRY_ATTEMPTS
        
        provider_dir = temp_mailbox / "outbound" / "dingtalk"
        
        create_test_message(
            provider_dir / "max_retry.md",
            msg_id="max_retry",
            status="pending",
            retry_count=MAX_RETRY_ATTEMPTS,
        )
        
        pending = watcher.scan()
        assert len(pending) == 0

    def test_mark_processing(self, watcher, temp_mailbox):
        """Test marking messages as processing."""
        provider_dir = temp_mailbox / "outbound" / "dingtalk"
        create_test_message(
            provider_dir / "msg.md",
            msg_id="processing_msg",
            status="pending",
        )
        
        # First scan finds it
        pending = watcher.scan()
        assert len(pending) == 1
        
        # Mark as processing
        watcher.mark_processing("processing_msg")
        
        # Second scan should skip it
        pending = watcher.scan()
        assert len(pending) == 0
        
        # Mark as done
        watcher.mark_done("processing_msg")
        
        # Third scan finds it again
        pending = watcher.scan()
        assert len(pending) == 1

    def test_multiple_providers(self, watcher, temp_mailbox):
        """Test scanning multiple provider directories."""
        # Create messages in different provider dirs
        for provider in [Provider.DINGTALK, Provider.LARK, Provider.SLACK]:
            provider_dir = temp_mailbox / "outbound" / provider.value
            create_test_message(
                provider_dir / f"{provider.value}_msg.md",
                msg_id=f"out_{provider.value}_001",
                provider=provider.value,
                status="pending",
            )
        
        pending = watcher.scan()
        
        assert len(pending) == 3
        providers = {p.provider for p in pending}
        assert Provider.DINGTALK in providers
        assert Provider.LARK in providers
        assert Provider.SLACK in providers

    def test_get_stats(self, watcher, temp_mailbox):
        """Test getting watcher statistics."""
        # Add some messages
        provider_dir = temp_mailbox / "outbound" / "dingtalk"
        create_test_message(provider_dir / "msg1.md", msg_id="msg1", status="pending")
        
        stats = watcher.get_stats()
        
        assert "outbound_path" in stats
        assert "poll_interval" in stats
        assert "provider_counts" in stats
        assert stats["provider_counts"]["dingtalk"] == 1


class TestOutboundMessageEntry:
    """Tests for OutboundMessageEntry dataclass."""

    def test_entry_creation(self):
        """Test creating an entry."""
        entry = OutboundMessageEntry(
            id="test_id",
            provider=Provider.DINGTALK,
            to="user123",
            content_type="text",
            status="pending",
            file_path=Path("/tmp/test.md"),
        )
        
        assert entry.id == "test_id"
        assert entry.provider == Provider.DINGTALK
        assert entry.retry_count == 0
