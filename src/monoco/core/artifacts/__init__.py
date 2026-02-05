"""
Monoco Artifact System - CAS Storage and Metadata Registry

Provides content-addressable storage for multi-modal assets with project-local
metadata tracking via manifest.jsonl.
"""

from .models import ArtifactMetadata, ArtifactSourceType, ArtifactStatus
from .manager import ArtifactManager

__all__ = [
    "ArtifactMetadata",
    "ArtifactSourceType",
    "ArtifactStatus",
    "ArtifactManager",
]
