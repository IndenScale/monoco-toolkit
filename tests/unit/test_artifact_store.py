"""
Unit tests for Artifact Store - Content-addressed file storage.
"""

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from monoco.features.artifact.store import ArtifactStore, ArtifactMetadata
from monoco.features.connector.protocol.schema import ArtifactType


class TestArtifactStore:
    """Tests for ArtifactStore class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def store(self, temp_dir):
        """Create an ArtifactStore instance."""
        return ArtifactStore(temp_dir)

    def test_initialization(self, temp_dir):
        """Test store initialization creates directory."""
        store = ArtifactStore(temp_dir)
        assert store.artifacts_dir.exists()
        assert store.artifacts_dir == temp_dir

    def test_compute_hash(self, store):
        """Test hash computation."""
        content = b"test content"
        expected_hash = hashlib.sha256(content).hexdigest()
        assert store._compute_hash(content) == expected_hash

    def test_short_hash(self, store):
        """Test short hash extraction."""
        full_hash = "a1b2c3d4e5f6789012345678"
        assert store._short_hash(full_hash) == "a1b2c3d4"

    def test_store_new_file(self, store):
        """Test storing a new file."""
        content = b"test file content"
        original_name = "test.txt"
        message_id = "msg_123"
        provider = "dingtalk"

        artifact, path = store.store(
            content=content,
            original_name=original_name,
            message_id=message_id,
            provider=provider,
        )

        # Check artifact properties
        assert artifact.id == hashlib.sha256(content).hexdigest()
        assert artifact.name == original_name
        assert artifact.type == ArtifactType.DOCUMENT
        assert artifact.size == len(content)
        assert artifact.path == f"{artifact.id[:8]}.txt"
        assert artifact.downloaded_at is not None

        # Check file was created
        assert path.exists()
        assert path.read_bytes() == content

    def test_store_deduplication(self, store):
        """Test that identical content is deduplicated."""
        content = b"duplicate content"
        original_name = "file1.txt"

        # Store same content twice
        artifact1, path1 = store.store(
            content=content,
            original_name=original_name,
            message_id="msg_1",
            provider="dingtalk",
        )

        artifact2, path2 = store.store(
            content=content,
            original_name="different_name.txt",
            message_id="msg_2",
            provider="lark",
        )

        # Same hash, same path
        assert artifact1.id == artifact2.id
        assert path1 == path2

        # File should only exist once
        assert path1.exists()

    def test_detect_type(self, store):
        """Test file type detection from extension."""
        assert store._detect_type("image.png") == ArtifactType.IMAGE
        assert store._detect_type("doc.pdf") == ArtifactType.DOCUMENT
        assert store._detect_type("sound.mp3") == ArtifactType.AUDIO
        assert store._detect_type("video.mp4") == ArtifactType.VIDEO
        assert store._detect_type("archive.zip") == ArtifactType.ARCHIVE
        assert store._detect_type("code.py") == ArtifactType.CODE
        assert store._detect_type("unknown.xyz") == ArtifactType.UNKNOWN

    def test_get_existing_artifact(self, store):
        """Test retrieving an existing artifact."""
        content = b"retrievable content"
        artifact, _ = store.store(
            content=content,
            original_name="test.txt",
            message_id="msg_123",
            provider="dingtalk",
        )

        # Get by full hash
        path = store.get(artifact.id)
        assert path is not None
        assert path.read_bytes() == content

        # Get by short hash
        path = store.get(artifact.id[:8])
        assert path is not None

    def test_get_nonexistent_artifact(self, store):
        """Test retrieving non-existent artifact."""
        assert store.get("nonexistent") is None

    def test_get_metadata(self, store):
        """Test retrieving artifact metadata."""
        content = b"metadata test"
        url = "https://example.com/file.txt"

        artifact, _ = store.store(
            content=content,
            original_name="test.txt",
            message_id="msg_123",
            provider="dingtalk",
            mime_type="text/plain",
            url=url,
        )

        metadata = store.get_metadata(artifact.id)
        assert metadata is not None
        assert metadata.hash == artifact.id
        assert metadata.name == "test.txt"
        assert metadata.provider == "dingtalk"
        assert metadata.mime_type == "text/plain"
        assert metadata.url == url

    def test_list_by_message(self, store):
        """Test listing artifacts by message ID."""
        message_id = "msg_abc"

        # Store two files for same message
        store.store(
            content=b"file1",
            original_name="file1.txt",
            message_id=message_id,
            provider="dingtalk",
        )
        store.store(
            content=b"file2",
            original_name="file2.png",
            message_id=message_id,
            provider="dingtalk",
        )

        # Store file for different message
        store.store(
            content=b"file3",
            original_name="file3.pdf",
            message_id="msg_xyz",
            provider="dingtalk",
        )

        artifacts = store.list_by_message(message_id)
        assert len(artifacts) == 2
        names = {a.name for a in artifacts}
        assert names == {"file1.txt", "file2.png"}

    def test_exists(self, store):
        """Test existence check."""
        content = b"check existence"
        artifact, _ = store.store(
            content=content,
            original_name="test.txt",
            message_id="msg_123",
            provider="dingtalk",
        )

        assert store.exists(artifact.id)
        assert store.exists(artifact.id[:8])
        assert not store.exists("nonexistent")

    def test_validate(self, store):
        """Test artifact validation."""
        content = b"valid content"
        artifact, _ = store.store(
            content=content,
            original_name="test.txt",
            message_id="msg_123",
            provider="dingtalk",
        )

        assert store.validate(artifact.id)
        assert not store.validate("nonexistent")

    def test_get_artifact_full_path(self, store):
        """Test getting full path from artifact path."""
        content = b"path test"
        artifact, _ = store.store(
            content=content,
            original_name="test.txt",
            message_id="msg_123",
            provider="dingtalk",
        )

        full_path = store.get_artifact_full_path(artifact.path)
        assert full_path is not None
        assert full_path.exists()
        assert full_path.read_bytes() == content


class TestArtifactMetadata:
    """Tests for ArtifactMetadata dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metadata = ArtifactMetadata(
            hash="abc123",
            short_hash="abc",
            name="test.txt",
            message_id="msg_1",
            provider="dingtalk",
            size=100,
        )

        data = metadata.to_dict()
        assert data["hash"] == "abc123"
        assert data["name"] == "test.txt"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "hash": "abc123",
            "short_hash": "abc",
            "name": "test.txt",
            "message_id": "msg_1",
            "provider": "dingtalk",
            "size": 100,
            "mime_type": "text/plain",
            "url": "https://example.com",
        }

        metadata = ArtifactMetadata.from_dict(data)
        assert metadata.hash == "abc123"
        assert metadata.name == "test.txt"
        assert metadata.mime_type == "text/plain"
