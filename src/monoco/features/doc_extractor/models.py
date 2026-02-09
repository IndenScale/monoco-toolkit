"""Data models for doc-extractor."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Self


@dataclass(frozen=True)
class BlobRef:
    """Reference to an extracted document blob."""
    
    hash: str
    """SHA256 hash of the original file (hex digest)."""
    
    cached: bool = False
    """Whether this blob was read from cache."""
    
    @property
    def path(self) -> Path:
        """Get the blob directory path."""
        from .extractor import DocExtractor
        return DocExtractor.BLOBS_DIR / self.hash
    
    @property
    def source_path(self) -> Path:
        """Get the source file path."""
        return self.path / "source"
    
    @property
    def pdf_path(self) -> Path:
        """Get the normalized PDF path."""
        return self.path / "source.pdf"
    
    @property
    def pages_dir(self) -> Path:
        """Get the pages directory path."""
        return self.path / "pages"
    
    @property
    def meta_path(self) -> Path:
        """Get the metadata file path."""
        return self.path / "meta.json"
    
    def exists(self) -> bool:
        """Check if the blob exists."""
        return self.path.exists()


@dataclass
class ExtractionResult:
    """Result of document extraction."""
    
    blob: BlobRef
    """Reference to the extracted blob."""
    
    page_count: int = 0
    """Number of pages rendered."""
    
    page_paths: list[Path] = field(default_factory=list)
    """Paths to rendered WebP pages."""
    
    @property
    def is_cached(self) -> bool:
        """Whether this result was from cache."""
        return self.blob.cached


@dataclass
class ExtractConfig:
    """Configuration for document extraction."""
    
    dpi: int = 150
    """DPI for PDF rendering (72-300)."""
    
    quality: int = 85
    """WebP quality (1-100)."""
    
    pages: list[int] | None = None
    """Specific pages to render (0-indexed). None for all."""
    
    def __post_init__(self):
        """Validate configuration."""
        if not 72 <= self.dpi <= 300:
            raise ValueError(f"DPI must be between 72 and 300, got {self.dpi}")
        if not 1 <= self.quality <= 100:
            raise ValueError(f"Quality must be between 1 and 100, got {self.quality}")
