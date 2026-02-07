"""
Tests for OutboundProcessor - post-send processing and message lifecycle.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml

from monoco.features.courier.outbound_processor import OutboundProcessor
from monoco.features.courier.outbound_watcher import OutboundMessageEntry
from monoco.features.courier.adapters.base import SendResult
from monoco.features.connector.protocol.schema import Provider


@pytest.fixture
def temp_mailbox():
    """Create a temporary mailbox directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mailbox = Path(tmpdir) / "mailbox"
        paths = {
            "outbound": mailbox / "outbound",
            "archive": mailbox / "archive",
            "deadletter": mailbox / ".deadletter",
        }
        for p in paths.values():
            p.mkdir(parents=True)
        yield paths


@pytest.fixture
def processor(temp_mailbox):
    """Create an OutboundProcessor instance."""
    proc = OutboundProcessor(
        outbound_path=temp_mailbox["outbound"],
        archive_path=temp_mailbox["archive"],
        deadletter_path=temp_mailbox["deadletter"],
    )
    proc.initialize()
    return proc


def create_test_entry(
    outbound_path: Path,
    msg_id: str,
    provider: Provider = Provider.DINGTALK,
    status: str = "pending",
    retry_count: int = 0,
    content: str = "Test content",
) -> OutboundMessageEntry:
    """Helper to create a test message entry."""
    provider_dir = outbound_path / provider.value
    provider_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = provider_dir / f"{msg_id}.md"
    
    frontmatter = {
        "id": msg_id,
        "to": "test_user",
        "provider": provider.value,
        "content_type": "text",
        "status": status,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "retry_count": retry_count,
    }
    
    content_yaml = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    full_content = f"---\n{content_yaml}---\n{content}\n"
    file_path.write_text(full_content, encoding="utf-8")
    
    return OutboundMessageEntry(
        id=msg_id,
        provider=provider,
        to="test_user",
        content_type="text",
        status=status,
        file_path=file_path,
        retry_count=retry_count,
        frontmatter=frontmatter,
    )


class TestOutboundProcessor:
    """Tests for OutboundProcessor class."""

    def test_initialization(self, temp_mailbox):
        """Test processor initialization."""
        processor = OutboundProcessor(
            outbound_path=temp_mailbox["outbound"],
            archive_path=temp_mailbox["archive"],
            deadletter_path=temp_mailbox["deadletter"],
        )
        processor.initialize()
        
        assert temp_mailbox["archive"].exists()
        assert temp_mailbox["deadletter"].exists()

    def test_process_success(self, processor, temp_mailbox):
        """Test processing a successful send."""
        entry = create_test_entry(temp_mailbox["outbound"], "success_msg")
        result = SendResult(success=True, provider_message_id="dt_123")
        
        success = processor.process_success(entry, result)
        
        assert success is True
        # Message should be moved to archive
        assert not entry.file_path.exists()
        archive_file = temp_mailbox["archive"] / "dingtalk" / "success_msg.md"
        assert archive_file.exists()
        
        # Check frontmatter updated
        content = archive_file.read_text(encoding="utf-8")
        assert "status: sent" in content
        assert "sent_at:" in content
        assert "provider_message_id: dt_123" in content

    def test_process_failure_retry_scheduled(self, processor, temp_mailbox):
        """Test processing a failure with retry scheduled."""
        entry = create_test_entry(temp_mailbox["outbound"], "retry_msg", retry_count=0)
        result = SendResult(success=False, error="Network error")
        
        will_retry = processor.process_failure(entry, result)
        
        assert will_retry is True
        # Message should still be in outbound
        assert entry.file_path.exists()
        
        # Check frontmatter updated
        content = entry.file_path.read_text(encoding="utf-8")
        assert "retry_count: 1" in content
        assert "next_retry_at:" in content
        assert "error_message: Network error" in content

    def test_process_failure_to_deadletter(self, processor, temp_mailbox):
        """Test processing a failure that moves to deadletter."""
        from monoco.features.connector.protocol.constants import MAX_RETRY_ATTEMPTS
        
        entry = create_test_entry(
            temp_mailbox["outbound"],
            "dead_msg",
            retry_count=MAX_RETRY_ATTEMPTS - 1,
        )
        result = SendResult(success=False, error="Permanent failure")
        
        will_retry = processor.process_failure(entry, result)
        
        assert will_retry is False
        # Message should be moved to deadletter
        assert not entry.file_path.exists()
        deadletter_file = temp_mailbox["deadletter"] / "dingtalk" / "dead_msg.md"
        assert deadletter_file.exists()
        
        # Check frontmatter updated
        content = deadletter_file.read_text(encoding="utf-8")
        assert "status: failed" in content
        assert "failed_at:" in content

    def test_calculate_next_retry(self, processor):
        """Test retry delay calculation."""
        base_delay = 1000  # 1 second in ms
        
        # First retry
        next_retry_0 = processor._calculate_next_retry(0)
        delay_0 = (next_retry_0 - datetime.utcnow()).total_seconds()
        assert 0.9 < delay_0 < 1.2  # ~1 second
        
        # Second retry (2x delay)
        next_retry_1 = processor._calculate_next_retry(1)
        delay_1 = (next_retry_1 - datetime.utcnow()).total_seconds()
        assert 1.9 < delay_1 < 2.2  # ~2 seconds
        
        # Third retry (4x delay)
        next_retry_2 = processor._calculate_next_retry(2)
        delay_2 = (next_retry_2 - datetime.utcnow()).total_seconds()
        assert 3.9 < delay_2 < 4.2  # ~4 seconds

    def test_archive_handles_collision(self, processor, temp_mailbox):
        """Test archive handles filename collision."""
        # Create first message and archive it
        entry1 = create_test_entry(temp_mailbox["outbound"], "collision_msg")
        result = SendResult(success=True)
        processor.process_success(entry1, result)
        
        # Create second message with same name (simulating new message with same ID)
        entry2 = create_test_entry(temp_mailbox["outbound"], "collision_msg")
        processor.process_success(entry2, result)
        
        # Both should exist with different names
        archive_dir = temp_mailbox["archive"] / "dingtalk"
        files = list(archive_dir.glob("collision_msg*.md"))
        assert len(files) == 2

    def test_get_stats(self, processor, temp_mailbox):
        """Test getting processor statistics."""
        # Create some archived messages
        for i in range(3):
            entry = create_test_entry(temp_mailbox["outbound"], f"archived_{i}")
            processor.process_success(entry, SendResult(success=True))
        
        # Create some deadletter messages
        from monoco.features.connector.protocol.constants import MAX_RETRY_ATTEMPTS
        for i in range(2):
            entry = create_test_entry(
                temp_mailbox["outbound"],
                f"dead_{i}",
                retry_count=MAX_RETRY_ATTEMPTS,
            )
            processor.process_failure(entry, SendResult(success=False, error="fail"))
        
        stats = processor.get_stats()
        
        assert stats["archived_count"] == 3
        assert stats["deadletter_count"] == 2
