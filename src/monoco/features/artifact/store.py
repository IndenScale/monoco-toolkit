"""
Artifact Store - Content-addressed file storage.

Files are stored in a flat structure with content-derived hashes as filenames.
Metadata is tracked in a JSONL manifest for lookups.

Structure:
    ~/.monoco/artifacts/
    ├── a1b2c3d4.png          # hash[:8] + ext
    ├── e5f6g7h8.pdf
    └── manifest.jsonl        # metadata index

Example manifest entry:
    {"hash": "a1b2c3d4...", "short_hash": "a1b2c3d4", "name": "doc.pdf",
     "message_id": "dingtalk_abc", "provider": "dingtalk", "size": 1024,
     "mime_type": "application/pdf", "downloaded_at": "2026-02-10T09:30:00Z"}
"""

import hashlib
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from monoco.features.connector.protocol.schema import Artifact, ArtifactType

logger = logging.getLogger(__name__)


@dataclass
class ArtifactMetadata:
    """Metadata for a stored artifact."""
    hash: str                      # Full SHA256 hash
    short_hash: str                # First 8 characters
    name: str                      # Original filename
    message_id: str                # Associated message ID
    provider: str                  # Source provider
    size: int                      # File size in bytes
    mime_type: Optional[str] = None
    downloaded_at: Optional[str] = None
    url: Optional[str] = None      # Original download URL

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ArtifactMetadata":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ArtifactStore:
    """
    Content-addressed artifact storage.

    All files are stored flat with hash-based names.
    Duplicate content is automatically deduplicated.
    """

    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir
        self.manifest_path = artifacts_dir / "manifest.jsonl"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure artifacts directory exists."""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, content: bytes) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content).hexdigest()

    def _short_hash(self, full_hash: str) -> str:
        """Get short hash (first 8 chars)."""
        return full_hash[:8]

    def _get_storage_path(self, short_hash: str, original_name: str) -> Path:
        """Generate storage path with preserved extension."""
        ext = Path(original_name).suffix
        return self.artifacts_dir / f"{short_hash}{ext}"

    def _read_manifest(self) -> List[ArtifactMetadata]:
        """Read all entries from manifest."""
        if not self.manifest_path.exists():
            return []

        entries = []
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            entries.append(ArtifactMetadata.from_dict(data))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Failed to read manifest: {e}")

        return entries

    def _append_manifest(self, metadata: ArtifactMetadata) -> None:
        """Append entry to manifest."""
        with open(self.manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(metadata.to_dict(), ensure_ascii=False) + "\n")

    def store(
        self,
        content: bytes,
        original_name: str,
        message_id: str,
        provider: str,
        mime_type: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Tuple[Artifact, Path]:
        """
        Store content and return Artifact with path.

        Args:
            content: File content bytes
            original_name: Original filename
            message_id: Associated message ID
            provider: Source provider (dingtalk, lark, etc.)
            mime_type: Optional MIME type
            url: Optional original download URL

        Returns:
            Tuple of (Artifact, storage_path)

        Raises:
            IOError: If storage fails
        """
        # Compute hash
        full_hash = self._compute_hash(content)
        short_hash = self._short_hash(full_hash)

        # Determine artifact type from extension
        artifact_type = self._detect_type(original_name)

        # Build storage path
        storage_path = self._get_storage_path(short_hash, original_name)

        # Check if already exists (deduplication)
        if storage_path.exists():
            logger.debug(f"Artifact {short_hash} already exists, reusing")
        else:
            # Atomic write
            temp_path = storage_path.with_suffix(storage_path.suffix + ".tmp")
            try:
                temp_path.write_bytes(content)
                temp_path.rename(storage_path)
                logger.debug(f"Stored artifact {short_hash} ({len(content)} bytes)")
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise IOError(f"Failed to store artifact: {e}") from e

        # Record metadata
        metadata = ArtifactMetadata(
            hash=full_hash,
            short_hash=short_hash,
            name=original_name,
            message_id=message_id,
            provider=provider,
            size=len(content),
            mime_type=mime_type,
            downloaded_at=datetime.now(timezone.utc).isoformat(),
            url=url,
        )
        self._append_manifest(metadata)

        # Build Artifact object
        artifact = Artifact(
            id=full_hash,
            name=original_name,
            type=artifact_type,
            mime_type=mime_type,
            size=len(content),
            path=storage_path.name,  # Just the filename (flat structure)
            url=url,
            downloaded_at=datetime.now(timezone.utc),
        )

        return artifact, storage_path

    def get(self, artifact_id: str) -> Optional[Path]:
        """
        Get storage path for an artifact by ID (hash).

        Args:
            artifact_id: Full or short hash

        Returns:
            Path to file if exists, None otherwise
        """
        # Search manifest for matching hash
        entries = self._read_manifest()
        for entry in entries:
            if entry.hash.startswith(artifact_id) or entry.short_hash == artifact_id:
                path = self._get_storage_path(entry.short_hash, entry.name)
                if path.exists():
                    return path
        return None

    def get_metadata(self, artifact_id: str) -> Optional[ArtifactMetadata]:
        """Get metadata for an artifact by ID."""
        entries = self._read_manifest()
        for entry in entries:
            if entry.hash.startswith(artifact_id) or entry.short_hash == artifact_id:
                return entry
        return None

    def list_by_message(self, message_id: str) -> List[ArtifactMetadata]:
        """List all artifacts associated with a message."""
        entries = self._read_manifest()
        return [e for e in entries if e.message_id == message_id]

    def exists(self, content_hash: str) -> bool:
        """Check if content already exists (by hash)."""
        entries = self._read_manifest()
        return any(e.hash == content_hash or e.short_hash == content_hash for e in entries)

    def delete(self, artifact_id: str) -> bool:
        """
        Delete an artifact. Returns True if found and deleted.

        Note: File is only deleted if no other messages reference it.
        """
        metadata = self.get_metadata(artifact_id)
        if not metadata:
            return False

        path = self._get_storage_path(metadata.short_hash, metadata.name)

        # Check if other messages use this file
        entries = self._read_manifest()
        other_refs = [e for e in entries
                      if e.short_hash == metadata.short_hash
                      and e.message_id != metadata.message_id]

        if not other_refs and path.exists():
            path.unlink()
            logger.debug(f"Deleted artifact file {path.name}")

        # Note: Manifest entry is not removed (append-only log)
        return True

    def _detect_type(self, filename: str) -> ArtifactType:
        """Detect artifact type from filename extension."""
        ext = Path(filename).suffix.lower()

        image_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
        doc_exts = {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt"}
        audio_exts = {".mp3", ".wav", ".ogg", ".aac", ".flac", ".m4a"}
        video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
        archive_exts = {".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"}
        code_exts = {".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rs", ".rb"}

        if ext in image_exts:
            return ArtifactType.IMAGE
        elif ext in doc_exts:
            return ArtifactType.DOCUMENT
        elif ext in audio_exts:
            return ArtifactType.AUDIO
        elif ext in video_exts:
            return ArtifactType.VIDEO
        elif ext in archive_exts:
            return ArtifactType.ARCHIVE
        elif ext in code_exts:
            return ArtifactType.CODE
        else:
            return ArtifactType.UNKNOWN

    def get_artifact_full_path(self, artifact_path: str) -> Optional[Path]:
        """
        Get full path from artifact's path field.

        Args:
            artifact_path: The path field from Artifact (e.g., "a1b2c3d4.png")

        Returns:
            Full Path if exists, None otherwise
        """
        full_path = self.artifacts_dir / artifact_path
        if full_path.exists():
            return full_path
        return None

    def validate(self, artifact_id: str) -> bool:
        """
        Validate that artifact exists and hash matches content.

        Returns:
            True if valid, False otherwise
        """
        metadata = self.get_metadata(artifact_id)
        if not metadata:
            return False

        path = self._get_storage_path(metadata.short_hash, metadata.name)
        if not path.exists():
            return False

        # Verify hash
        content = path.read_bytes()
        actual_hash = self._compute_hash(content)

        return actual_hash == metadata.hash
