"""
Artifact data models for Monoco Artifact System.

Defines the metadata structure, enums, and data classes for artifact management.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ArtifactSourceType(str, Enum):
    """Source type of the artifact."""

    GENERATED = "generated"  # AI-generated content
    UPLOADED = "uploaded"  # User-uploaded file
    IMPORTED = "imported"  # Imported from external source
    DERIVED = "derived"  # Derived from another artifact


class ArtifactStatus(str, Enum):
    """Lifecycle status of the artifact."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    DELETED = "deleted"


class ArtifactMetadata(BaseModel):
    """
    Metadata record for an artifact in the manifest.

    Each artifact is uniquely identified by its content hash (SHA256).
    The manifest.jsonl contains one JSON line per artifact metadata.
    """

    artifact_id: str = Field(
        description="Unique identifier (ULID or UUID) for the artifact instance"
    )
    content_hash: str = Field(
        description="SHA256 hash of the artifact content (CAS address)"
    )
    source_type: ArtifactSourceType = Field(description="How the artifact was created")
    status: ArtifactStatus = Field(
        default=ArtifactStatus.ACTIVE, description="Current lifecycle status"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp (UTC)"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp (UTC)"
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="Optional expiration timestamp"
    )
    content_type: str = Field(
        default="application/octet-stream", description="MIME type of the content"
    )
    size_bytes: int = Field(default=0, description="Size of the artifact in bytes")
    original_filename: Optional[str] = Field(
        default=None, description="Original filename if uploaded"
    )
    source_url: Optional[str] = Field(
        default=None, description="Source URL if imported from external"
    )
    parent_artifact_id: Optional[str] = Field(
        default=None, description="Parent artifact ID if this is derived"
    )
    tags: list[str] = Field(default_factory=list, description="User-defined tags")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata key-value pairs"
    )

    @field_validator("content_hash")
    @classmethod
    def validate_content_hash(cls, v: str) -> str:
        """Validate that content_hash is a valid SHA256 hex string."""
        if len(v) != 64:
            raise ValueError("content_hash must be a 64-character SHA256 hex string")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("content_hash must be a valid hex string")
        return v

    def to_jsonl_line(self) -> str:
        """Serialize to a single JSON line for manifest.jsonl."""
        return json.dumps(self.model_dump(mode="json"), ensure_ascii=False) + "\n"

    @classmethod
    def from_jsonl_line(cls, line: str) -> ArtifactMetadata:
        """Deserialize from a JSON line."""
        data = json.loads(line.strip())
        return cls.model_validate(data)

    @property
    def is_expired(self) -> bool:
        """Check if the artifact has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def cas_path_components(self) -> tuple[str, str, str]:
        """
        Generate CAS storage path components from content_hash.

        Returns (prefix1, prefix2, filename) for tiered directory structure.
        Example: hash='abc123...' -> ('ab', 'c1', 'abc123...')
        """
        if len(self.content_hash) < 4:
            raise ValueError("content_hash too short for path generation")
        return (
            self.content_hash[:2],
            self.content_hash[2:4],
            self.content_hash,
        )

    @property
    def cas_relative_path(self) -> str:
        """Get the relative CAS path for this artifact."""
        p1, p2, filename = self.cas_path_components
        return f"{p1}/{p2}/{filename}"


def compute_content_hash(content: bytes) -> str:
    """
    Compute SHA256 hash of content for CAS addressing.

    Args:
        content: Raw bytes of the artifact content

    Returns:
        64-character lowercase hex string of the SHA256 hash
    """
    return hashlib.sha256(content).hexdigest()


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file for CAS addressing.

    Args:
        file_path: Path to the file to hash

    Returns:
        64-character lowercase hex string of the SHA256 hash
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
