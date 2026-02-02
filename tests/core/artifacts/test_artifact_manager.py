"""
Unit tests for ArtifactManager and related classes.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from monoco.core.artifacts import (
    ArtifactManager,
    ArtifactMetadata,
    ArtifactSourceType,
    ArtifactStatus,
)
from monoco.core.artifacts.models import compute_content_hash, compute_file_hash


class TestArtifactMetadata:
    """Tests for ArtifactMetadata data model."""

    def test_basic_creation(self):
        """Test basic metadata creation."""
        metadata = ArtifactMetadata(
            artifact_id="test-123",
            content_hash="a" * 64,
            source_type=ArtifactSourceType.GENERATED,
        )
        assert metadata.artifact_id == "test-123"
        assert metadata.content_hash == "a" * 64
        assert metadata.source_type == ArtifactSourceType.GENERATED
        assert metadata.status == ArtifactStatus.ACTIVE

    def test_content_hash_validation(self):
        """Test content hash validation."""
        # Valid hash
        metadata = ArtifactMetadata(
            artifact_id="test",
            content_hash="a" * 64,
            source_type=ArtifactSourceType.GENERATED,
        )
        assert len(metadata.content_hash) == 64

        # Invalid hash - too short
        with pytest.raises(ValueError):
            ArtifactMetadata(
                artifact_id="test",
                content_hash="a" * 63,
                source_type=ArtifactSourceType.GENERATED,
            )

        # Invalid hash - not hex
        with pytest.raises(ValueError):
            ArtifactMetadata(
                artifact_id="test",
                content_hash="g" * 64,
                source_type=ArtifactSourceType.GENERATED,
            )

    def test_jsonl_serialization(self):
        """Test JSONL serialization and deserialization."""
        original = ArtifactMetadata(
            artifact_id="test-123",
            content_hash="a" * 64,
            source_type=ArtifactSourceType.UPLOADED,
            content_type="image/png",
            size_bytes=1024,
            tags=["test", "image"],
            metadata={"key": "value"},
        )

        jsonl_line = original.to_jsonl_line()
        assert jsonl_line.endswith("\n")

        # Parse back
        parsed = ArtifactMetadata.from_jsonl_line(jsonl_line)
        assert parsed.artifact_id == original.artifact_id
        assert parsed.content_hash == original.content_hash
        assert parsed.source_type == original.source_type
        assert parsed.tags == original.tags
        assert parsed.metadata == original.metadata

    def test_cas_path_components(self):
        """Test CAS path component generation."""
        metadata = ArtifactMetadata(
            artifact_id="test",
            content_hash="abc123def456" + "0" * 52,
            source_type=ArtifactSourceType.GENERATED,
        )
        p1, p2, filename = metadata.cas_path_components
        assert p1 == "ab"
        assert p2 == "c1"
        assert filename == metadata.content_hash

    def test_is_expired(self):
        """Test expiration checking."""
        # Not expired
        metadata = ArtifactMetadata(
            artifact_id="test",
            content_hash="a" * 64,
            source_type=ArtifactSourceType.GENERATED,
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
        assert not metadata.is_expired

        # Expired
        metadata.expires_at = datetime.utcnow() - timedelta(days=1)
        assert metadata.is_expired

        # No expiration
        metadata.expires_at = None
        assert not metadata.is_expired


class TestContentHash:
    """Tests for content hash computation."""

    def test_compute_content_hash(self):
        """Test hash computation from bytes."""
        content = b"hello world"
        hash1 = compute_content_hash(content)
        hash2 = compute_content_hash(content)

        assert len(hash1) == 64
        assert hash1 == hash2  # Deterministic

        # Different content = different hash
        different_content = b"hello world!"
        hash3 = compute_content_hash(different_content)
        assert hash1 != hash3

    def test_compute_file_hash(self, tmp_path):
        """Test hash computation from file."""
        test_file = tmp_path / "test.txt"
        content = b"test content for hashing"
        test_file.write_bytes(content)

        file_hash = compute_file_hash(test_file)
        content_hash = compute_content_hash(content)

        assert file_hash == content_hash


class TestArtifactManager:
    """Tests for ArtifactManager CRUD operations."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as project_dir:
            with tempfile.TemporaryDirectory() as global_dir:
                yield Path(project_dir), Path(global_dir)

    @pytest.fixture
    def manager(self, temp_dirs):
        """Create an ArtifactManager with temp directories."""
        project_dir, global_dir = temp_dirs
        return ArtifactManager(project_dir=project_dir, global_store=global_dir)

    def test_initialization(self, temp_dirs):
        """Test manager initialization creates directories."""
        project_dir, global_dir = temp_dirs
        manager = ArtifactManager(project_dir=project_dir, global_store=global_dir)

        assert manager.global_store.exists()
        assert manager.local_artifacts_dir.exists()
        assert manager.manifest_path.parent.exists()

    def test_store_and_get(self, manager):
        """Test storing and retrieving artifacts."""
        content = b"test artifact content"

        # Store
        metadata = manager.store(
            content=content,
            source_type=ArtifactSourceType.GENERATED,
            content_type="text/plain",
            tags=["test"],
        )

        assert metadata.artifact_id is not None
        assert metadata.content_hash == compute_content_hash(content)
        assert metadata.size_bytes == len(content)
        assert metadata.source_type == ArtifactSourceType.GENERATED

        # Get metadata
        retrieved = manager.get(metadata.artifact_id)
        assert retrieved is not None
        assert retrieved.artifact_id == metadata.artifact_id
        assert retrieved.content_hash == metadata.content_hash

        # Get content
        retrieved_content = manager.get_content(metadata.artifact_id)
        assert retrieved_content == content

    def test_store_file(self, manager, tmp_path):
        """Test storing a file."""
        test_file = tmp_path / "test.png"
        content = b"fake png content"
        test_file.write_bytes(content)

        metadata = manager.store_file(
            file_path=test_file,
            source_type=ArtifactSourceType.UPLOADED,
            tags=["image"],
        )

        assert metadata.original_filename == "test.png"
        assert metadata.content_type == "image/png"
        assert metadata.size_bytes == len(content)

    def test_cas_deduplication(self, manager):
        """Test that identical content is deduplicated in CAS."""
        content = b"duplicate content"

        meta1 = manager.store(content, source_type=ArtifactSourceType.GENERATED)
        meta2 = manager.store(content, source_type=ArtifactSourceType.UPLOADED)

        # Different artifact IDs
        assert meta1.artifact_id != meta2.artifact_id
        # Same content hash
        assert meta1.content_hash == meta2.content_hash

        # Only one file in CAS
        cas_path = manager._get_cas_path(meta1.content_hash)
        assert cas_path.exists()

    def test_list_artifacts(self, manager):
        """Test listing artifacts with filters."""
        # Create several artifacts
        meta1 = manager.store(
            b"content1", source_type=ArtifactSourceType.GENERATED, tags=["a", "b"]
        )
        meta2 = manager.store(
            b"content2", source_type=ArtifactSourceType.UPLOADED, tags=["b", "c"]
        )
        meta3 = manager.store(
            b"content3", source_type=ArtifactSourceType.IMPORTED, tags=["a"]
        )

        # List all
        all_artifacts = manager.list()
        assert len(all_artifacts) == 3

        # Filter by source type
        generated = manager.list(source_type=ArtifactSourceType.GENERATED)
        assert len(generated) == 1
        assert generated[0].artifact_id == meta1.artifact_id

        # Filter by tags
        tag_b = manager.list(tags=["b"])
        assert len(tag_b) == 2

        tag_a_b = manager.list(tags=["a", "b"])
        assert len(tag_a_b) == 1

    def test_list_with_expired(self, manager):
        """Test listing with expired artifacts."""
        # Active artifact
        meta1 = manager.store(b"active", source_type=ArtifactSourceType.GENERATED)

        # Expired artifact
        expired_time = datetime.utcnow() - timedelta(days=1)
        meta2 = manager.store(
            b"expired",
            source_type=ArtifactSourceType.GENERATED,
            expires_at=expired_time,
        )

        # Without include_expired
        active_only = manager.list()
        assert len(active_only) == 1
        assert active_only[0].artifact_id == meta1.artifact_id

        # With include_expired
        all_including = manager.list(include_expired=True)
        assert len(all_including) == 2

    def test_update_metadata(self, manager):
        """Test updating artifact metadata."""
        meta = manager.store(
            b"content",
            source_type=ArtifactSourceType.GENERATED,
            tags=["old"],
            metadata={"key": "value"},
        )

        # Update
        updated = manager.update(
            artifact_id=meta.artifact_id,
            tags=["new"],
            metadata={"extra": "data"},
            status=ArtifactStatus.ARCHIVED,
        )

        assert updated is not None
        assert updated.tags == ["new"]
        assert updated.metadata == {"key": "value", "extra": "data"}
        assert updated.status == ArtifactStatus.ARCHIVED

        # Verify persistence
        retrieved = manager.get(meta.artifact_id)
        assert retrieved.tags == ["new"]
        assert retrieved.status == ArtifactStatus.ARCHIVED

    def test_soft_delete(self, manager):
        """Test soft delete operation."""
        meta = manager.store(b"to delete", source_type=ArtifactSourceType.GENERATED)

        # Soft delete
        result = manager.delete(meta.artifact_id, permanent=False)
        assert result is True

        # Should not be retrievable
        assert manager.get(meta.artifact_id) is None

        # But still in manifest (marked as deleted)
        with open(manager.manifest_path, "r") as f:
            content = f.read()
            assert meta.artifact_id in content
            assert "deleted" in content

    def test_permanent_delete(self, manager):
        """Test permanent delete operation."""
        meta = manager.store(b"to delete", source_type=ArtifactSourceType.GENERATED)
        cas_path = manager._get_cas_path(meta.content_hash)

        # Permanent delete
        result = manager.delete(meta.artifact_id, permanent=True)
        assert result is True

        # Should not be retrievable
        assert manager.get(meta.artifact_id) is None

        # CAS file should be removed
        assert not cas_path.exists()

    def test_delete_nonexistent(self, manager):
        """Test deleting non-existent artifact."""
        result = manager.delete("nonexistent-id")
        assert result is False

    def test_cleanup_expired(self, manager):
        """Test cleanup of expired artifacts."""
        # Create expired artifact
        expired_time = datetime.utcnow() - timedelta(days=1)
        meta = manager.store(
            b"expired",
            source_type=ArtifactSourceType.GENERATED,
            expires_at=expired_time,
        )

        # Cleanup
        cleaned = manager.cleanup_expired()
        assert len(cleaned) == 1
        assert cleaned[0] == meta.artifact_id

        # Should be marked as expired
        retrieved = manager.get(meta.artifact_id)
        assert retrieved is None  # Expired not returned by default

        # But in list with include_expired
        all_expired = manager.list(include_expired=True)
        assert len(all_expired) == 1
        assert all_expired[0].status == ArtifactStatus.EXPIRED

    def test_get_stats(self, manager):
        """Test statistics collection."""
        # Empty stats
        stats = manager.get_stats()
        assert stats["total_artifacts"] == 0
        assert stats["active"] == 0

        # Add artifacts
        manager.store(b"a", source_type=ArtifactSourceType.GENERATED)
        manager.store(b"b", source_type=ArtifactSourceType.UPLOADED)

        stats = manager.get_stats()
        assert stats["total_artifacts"] == 2
        assert stats["active"] == 2
        assert stats["total_size_bytes"] == 2

    def test_manifest_persistence(self, temp_dirs):
        """Test that manifest persists across manager instances."""
        project_dir, global_dir = temp_dirs

        # First manager instance
        manager1 = ArtifactManager(project_dir=project_dir, global_store=global_dir)
        meta = manager1.store(b"persistent", source_type=ArtifactSourceType.GENERATED)

        # Second manager instance (simulates restart)
        manager2 = ArtifactManager(project_dir=project_dir, global_store=global_dir)
        retrieved = manager2.get(meta.artifact_id)

        assert retrieved is not None
        assert retrieved.artifact_id == meta.artifact_id

    def test_create_symlink(self, manager, tmp_path):
        """Test symlink creation."""
        content = b"symlink target"
        meta = manager.store(content, source_type=ArtifactSourceType.GENERATED)

        link_path = tmp_path / "link_to_artifact"
        result = manager.create_symlink(meta.artifact_id, link_path)

        assert result is True
        assert link_path.is_symlink()
        assert link_path.read_bytes() == content

    def test_create_symlink_nonexistent(self, manager, tmp_path):
        """Test symlink creation for non-existent artifact."""
        link_path = tmp_path / "broken_link"
        result = manager.create_symlink("nonexistent", link_path)
        assert result is False

    def test_content_type_detection(self, manager, tmp_path):
        """Test MIME type detection from file extension."""
        test_cases = [
            ("test.png", "image/png"),
            ("test.jpg", "image/jpeg"),
            ("test.json", "application/json"),
            ("test.md", "text/markdown"),
            ("test.txt", "text/plain"),
            ("test.unknown", "application/octet-stream"),
        ]

        for filename, expected_type in test_cases:
            test_file = tmp_path / filename
            test_file.write_bytes(b"test")
            meta = manager.store_file(test_file)
            assert meta.content_type == expected_type, f"Failed for {filename}"

    def test_concurrent_store(self, manager):
        """Test that concurrent stores work correctly."""
        import threading

        artifacts = []
        errors = []

        def store_artifact(i):
            try:
                meta = manager.store(
                    f"content{i}".encode(),
                    source_type=ArtifactSourceType.GENERATED,
                )
                artifacts.append(meta)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=store_artifact, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(artifacts) == 10
        assert len(manager.list()) == 10

    def test_get_content_path(self, manager):
        """Test getting filesystem path to content."""
        content = b"test content"
        meta = manager.store(content, source_type=ArtifactSourceType.GENERATED)

        path = manager.get_content_path(meta.artifact_id)
        assert path is not None
        assert path.exists()
        assert path.read_bytes() == content

        # Non-existent artifact
        assert manager.get_content_path("nonexistent") is None

    def test_manifest_atomicity(self, manager):
        """Test that manifest updates are atomic."""
        # Store multiple artifacts
        for i in range(5):
            manager.store(f"content{i}".encode(), source_type=ArtifactSourceType.GENERATED)

        # Verify manifest is valid JSONL
        with open(manager.manifest_path, "r") as f:
            lines = f.readlines()

        assert len(lines) == 5
        for line in lines:
            # Each line should be valid JSON
            data = json.loads(line)
            assert "artifact_id" in data
            assert "content_hash" in data
