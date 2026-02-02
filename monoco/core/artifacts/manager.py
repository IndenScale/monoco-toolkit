"""
ArtifactManager - Core management class for Monoco Artifact System.

Implements CRUD operations, CAS (Content-Addressable Storage) management,
and manifest.jsonl registry operations.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .models import (
    ArtifactMetadata,
    ArtifactSourceType,
    ArtifactStatus,
    compute_content_hash,
    compute_file_hash,
)


class ArtifactManager:
    """
    Manages artifacts with CAS storage and manifest-based metadata registry.

    Implements a hybrid storage architecture:
    - Global storage pool: ~/.monoco/artifacts/ (physical storage)
    - Project-local registry: ./.monoco/artifacts/manifest.jsonl

    CAS (Content-Addressable Storage):
    - Files are stored by their SHA256 hash
    - Path structure: {global_store}/{hash[:2]}/{hash[2:4]}/{hash}
    - Automatic deduplication via hash-based addressing
    """

    def __init__(
        self,
        project_dir: Path,
        global_store: Optional[Path] = None,
    ):
        """
        Initialize ArtifactManager.

        Args:
            project_dir: Root directory of the project (for local manifest)
            global_store: Path to global artifact store (default: ~/.monoco/artifacts)
        """
        self.project_dir = Path(project_dir).resolve()
        self.global_store = (
            Path(global_store).expanduser().resolve()
            if global_store
            else Path.home() / ".monoco" / "artifacts"
        )

        # Project-local artifact directory
        self.local_artifacts_dir = self.project_dir / ".monoco" / "artifacts"
        self.manifest_path = self.local_artifacts_dir / "manifest.jsonl"

        # In-memory cache of metadata (artifact_id -> metadata)
        self._metadata_cache: dict[str, ArtifactMetadata] = {}
        self._lock = threading.RLock()

        # Ensure directories exist
        self._ensure_directories()

        # Load existing manifest
        self._load_manifest()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.global_store.mkdir(parents=True, exist_ok=True)
        self.local_artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _load_manifest(self) -> None:
        """Load manifest.jsonl into memory cache."""
        if not self.manifest_path.exists():
            return

        with self._lock:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        metadata = ArtifactMetadata.from_jsonl_line(line)
                        self._metadata_cache[metadata.artifact_id] = metadata
                    except (json.JSONDecodeError, ValueError):
                        # Skip corrupted lines, could log warning
                        continue

    def _atomic_append_manifest(self, metadata: ArtifactMetadata) -> None:
        """Atomically append a metadata entry to manifest.jsonl."""
        with self._lock:
            # Write to temp file first, then rename for atomicity
            fd, temp_path = tempfile.mkstemp(
                dir=self.local_artifacts_dir, suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(metadata.to_jsonl_line())

                # Append temp content to manifest atomically
                with open(temp_path, "r", encoding="utf-8") as src:
                    with open(self.manifest_path, "a", encoding="utf-8") as dst:
                        dst.write(src.read())
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def _rewrite_manifest(self) -> None:
        """Rewrite entire manifest from cache (for deletes/updates)."""
        with self._lock:
            fd, temp_path = tempfile.mkstemp(
                dir=self.local_artifacts_dir, suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    for metadata in self._metadata_cache.values():
                        # Keep all records including DELETED for audit trail
                        f.write(metadata.to_jsonl_line())

                # Atomic rename
                os.replace(temp_path, self.manifest_path)
            except Exception:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise

    def _get_cas_path(self, content_hash: str) -> Path:
        """Get the CAS storage path for a content hash."""
        prefix1 = content_hash[:2]
        prefix2 = content_hash[2:4]
        return self.global_store / prefix1 / prefix2 / content_hash

    def _store_in_cas(self, content: bytes, content_hash: str) -> Path:
        """
        Store content in CAS. If content already exists, skip writing.

        Returns:
            Path to the stored file in CAS
        """
        cas_path = self._get_cas_path(content_hash)

        if cas_path.exists():
            # Content already stored (deduplication)
            return cas_path

        # Ensure parent directories exist
        cas_path.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically using temp file
        fd, temp_path = tempfile.mkstemp(dir=cas_path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(content)
            os.replace(temp_path, cas_path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

        return cas_path

    def store(
        self,
        content: bytes,
        source_type: ArtifactSourceType = ArtifactSourceType.GENERATED,
        content_type: str = "application/octet-stream",
        original_filename: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        source_url: Optional[str] = None,
        parent_artifact_id: Optional[str] = None,
    ) -> ArtifactMetadata:
        """
        Store a new artifact with CAS deduplication.

        Args:
            content: Raw bytes of the artifact content
            source_type: How the artifact was created
            content_type: MIME type of the content
            original_filename: Original filename if uploaded
            expires_at: Optional expiration timestamp
            tags: User-defined tags
            metadata: Additional metadata key-value pairs
            source_url: Source URL if imported
            parent_artifact_id: Parent artifact ID if derived

        Returns:
            ArtifactMetadata for the stored artifact
        """
        # Compute content hash for CAS
        content_hash = compute_content_hash(content)

        # Store in CAS (deduplication happens automatically)
        cas_path = self._store_in_cas(content, content_hash)

        # Create metadata
        artifact_meta = ArtifactMetadata(
            artifact_id=str(uuid.uuid4()),
            content_hash=content_hash,
            source_type=source_type,
            status=ArtifactStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=expires_at,
            content_type=content_type,
            size_bytes=len(content),
            original_filename=original_filename,
            source_url=source_url,
            parent_artifact_id=parent_artifact_id,
            tags=tags or [],
            metadata=metadata or {},
        )

        # Update cache and manifest
        with self._lock:
            self._metadata_cache[artifact_meta.artifact_id] = artifact_meta
            self._atomic_append_manifest(artifact_meta)

        return artifact_meta

    def store_file(
        self,
        file_path: Path,
        source_type: ArtifactSourceType = ArtifactSourceType.UPLOADED,
        content_type: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ArtifactMetadata:
        """
        Store a file as an artifact.

        Args:
            file_path: Path to the file to store
            source_type: How the artifact was created
            content_type: MIME type (auto-detected if not provided)
            expires_at: Optional expiration timestamp
            tags: User-defined tags
            metadata: Additional metadata

        Returns:
            ArtifactMetadata for the stored artifact
        """
        file_path = Path(file_path)
        content = file_path.read_bytes()

        if content_type is None:
            content_type = self._detect_content_type(file_path)

        return self.store(
            content=content,
            source_type=source_type,
            content_type=content_type,
            original_filename=file_path.name,
            expires_at=expires_at,
            tags=tags,
            metadata=metadata,
        )

    def _detect_content_type(self, file_path: Path) -> str:
        """Detect MIME type from file extension."""
        suffix = file_path.suffix.lower()
        mime_types = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".jsonl": "application/jsonlines",
            ".yaml": "application/yaml",
            ".yml": "application/yaml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".pdf": "application/pdf",
            ".html": "text/html",
            ".htm": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".py": "text/x-python",
            ".zip": "application/zip",
        }
        return mime_types.get(suffix, "application/octet-stream")

    def get(self, artifact_id: str) -> Optional[ArtifactMetadata]:
        """
        Get artifact metadata by ID.

        Args:
            artifact_id: The unique artifact identifier

        Returns:
            ArtifactMetadata if found and active, None otherwise
            (returns None for DELETED or EXPIRED artifacts)
        """
        with self._lock:
            metadata = self._metadata_cache.get(artifact_id)
            if metadata is None:
                return None
            if metadata.status in (ArtifactStatus.DELETED, ArtifactStatus.EXPIRED):
                return None
            return metadata

    def get_content(self, artifact_id: str) -> Optional[bytes]:
        """
        Get artifact content by ID.

        Args:
            artifact_id: The unique artifact identifier

        Returns:
            Content bytes if found, None otherwise
        """
        metadata = self.get(artifact_id)
        if metadata is None:
            return None

        cas_path = self._get_cas_path(metadata.content_hash)
        if not cas_path.exists():
            return None

        return cas_path.read_bytes()

    def get_content_path(self, artifact_id: str) -> Optional[Path]:
        """
        Get the filesystem path to artifact content (read-only access).

        Args:
            artifact_id: The unique artifact identifier

        Returns:
            Path to content if exists, None otherwise
        """
        metadata = self.get(artifact_id)
        if metadata is None:
            return None

        cas_path = self._get_cas_path(metadata.content_hash)
        if cas_path.exists():
            return cas_path
        return None

    def list(
        self,
        status: Optional[ArtifactStatus] = None,
        source_type: Optional[ArtifactSourceType] = None,
        tags: Optional[list[str]] = None,
        include_expired: bool = False,
    ) -> list[ArtifactMetadata]:
        """
        List artifacts with optional filtering.

        Args:
            status: Filter by status
            source_type: Filter by source type
            tags: Filter by tags (must have all specified tags)
            include_expired: Include expired artifacts

        Returns:
            List of matching ArtifactMetadata
        """
        with self._lock:
            results = []
            for metadata in self._metadata_cache.values():
                # Skip deleted
                if metadata.status == ArtifactStatus.DELETED:
                    continue

                # Apply filters
                if status is not None and metadata.status != status:
                    continue
                if source_type is not None and metadata.source_type != source_type:
                    continue
                if tags is not None and not all(tag in metadata.tags for tag in tags):
                    continue
                if not include_expired and metadata.is_expired:
                    continue

                results.append(metadata)

            return sorted(results, key=lambda m: m.created_at, reverse=True)

    def update(
        self,
        artifact_id: str,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
        status: Optional[ArtifactStatus] = None,
    ) -> Optional[ArtifactMetadata]:
        """
        Update artifact metadata (not content - content is immutable in CAS).

        Args:
            artifact_id: The artifact to update
            tags: New tags (replaces existing)
            metadata: Additional metadata to merge
            expires_at: New expiration timestamp
            status: New status

        Returns:
            Updated ArtifactMetadata if found, None otherwise
        """
        with self._lock:
            existing = self._metadata_cache.get(artifact_id)
            if existing is None or existing.status == ArtifactStatus.DELETED:
                return None

            # Update fields
            if tags is not None:
                existing.tags = tags
            if metadata is not None:
                existing.metadata.update(metadata)
            if expires_at is not None:
                existing.expires_at = expires_at
            if status is not None:
                existing.status = status

            existing.updated_at = datetime.utcnow()

            # Rewrite manifest
            self._rewrite_manifest()

            return existing

    def delete(self, artifact_id: str, permanent: bool = False) -> bool:
        """
        Delete (or mark as deleted) an artifact.

        Args:
            artifact_id: The artifact to delete
            permanent: If True, permanently remove from CAS and manifest

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            metadata = self._metadata_cache.get(artifact_id)
            if metadata is None or metadata.status == ArtifactStatus.DELETED:
                return False

            if permanent:
                # Remove from cache and rewrite manifest
                del self._metadata_cache[artifact_id]
                self._rewrite_manifest()

                # Remove from CAS (only if no other artifacts reference this hash)
                self._cleanup_cas_if_orphaned(metadata.content_hash)
            else:
                # Soft delete
                metadata.status = ArtifactStatus.DELETED
                metadata.updated_at = datetime.utcnow()
                self._rewrite_manifest()

            return True

    def _cleanup_cas_if_orphaned(self, content_hash: str) -> None:
        """Remove content from CAS if no other artifacts reference it."""
        # Check if any other artifact uses this hash
        for meta in self._metadata_cache.values():
            if meta.content_hash == content_hash and meta.status != ArtifactStatus.DELETED:
                return  # Still referenced

        # Safe to delete from CAS
        cas_path = self._get_cas_path(content_hash)
        if cas_path.exists():
            cas_path.unlink()

            # Cleanup empty directories
            try:
                cas_path.parent.rmdir()  # Remove hash[2:4] dir if empty
                cas_path.parent.parent.rmdir()  # Remove hash[:2] dir if empty
            except OSError:
                pass  # Directory not empty

    def cleanup_expired(self) -> list[str]:
        """
        Remove all expired artifacts (soft delete).

        Returns:
            List of artifact IDs that were cleaned up
        """
        cleaned = []
        with self._lock:
            for metadata in self._metadata_cache.values():
                if metadata.is_expired and metadata.status == ArtifactStatus.ACTIVE:
                    metadata.status = ArtifactStatus.EXPIRED
                    metadata.updated_at = datetime.utcnow()
                    cleaned.append(metadata.artifact_id)

            if cleaned:
                self._rewrite_manifest()

        return cleaned

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the artifact store.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total = len(self._metadata_cache)
            active = sum(
                1
                for m in self._metadata_cache.values()
                if m.status == ArtifactStatus.ACTIVE
            )
            expired = sum(
                1
                for m in self._metadata_cache.values()
                if m.status == ArtifactStatus.EXPIRED
            )
            archived = sum(
                1
                for m in self._metadata_cache.values()
                if m.status == ArtifactStatus.ARCHIVED
            )
            total_size = sum(
                m.size_bytes
                for m in self._metadata_cache.values()
                if m.status != ArtifactStatus.DELETED
            )

        return {
            "total_artifacts": total,
            "active": active,
            "expired": expired,
            "archived": archived,
            "total_size_bytes": total_size,
            "global_store_path": str(self.global_store),
            "manifest_path": str(self.manifest_path),
        }

    def create_symlink(self, artifact_id: str, link_path: Path) -> bool:
        """
        Create a symlink from link_path to the artifact content.

        Args:
            artifact_id: The artifact to link to
            link_path: Where to create the symlink

        Returns:
            True if successful, False otherwise
        """
        content_path = self.get_content_path(artifact_id)
        if content_path is None:
            return False

        link_path = Path(link_path)
        link_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing link if present
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()

        # Create relative symlink for portability
        try:
            rel_target = os.path.relpath(content_path, link_path.parent)
            link_path.symlink_to(rel_target)
            return True
        except OSError:
            return False
