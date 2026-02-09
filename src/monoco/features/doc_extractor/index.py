"""Lightweight index for blob metadata."""

import json
from datetime import datetime
from pathlib import Path
from typing import Self

import yaml

from .models import BlobRef


class BlobIndex:
    """Lightweight YAML index for blob metadata.
    
    This index is maintained for fast search and listing operations.
    It can be rebuilt from individual blob meta.json files if corrupted.
    """
    
    INDEX_PATH = Path.home() / ".monoco" / "blobs" / "index.yaml"
    
    def __init__(self):
        self._data: dict | None = None
    
    def _load(self) -> dict:
        """Load index from disk."""
        if self._data is not None:
            return self._data
        
        if not self.INDEX_PATH.exists():
            self._data = {"version": "1.0", "updated_at": None, "entries": []}
            return self._data
        
        try:
            with open(self.INDEX_PATH, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {"version": "1.0", "entries": []}
        except Exception:
            self._data = {"version": "1.0", "updated_at": None, "entries": []}
        
        return self._data
    
    def _save(self) -> None:
        """Save index to disk."""
        self.INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._data["updated_at"] = datetime.now().isoformat()
        with open(self.INDEX_PATH, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def add(self, blob: BlobRef) -> None:
        """Add or update index entry from blob metadata."""
        if not blob.meta_path.exists():
            return
        
        try:
            meta = json.loads(blob.meta_path.read_text())
        except Exception:
            return
        
        index = self._load()
        
        # Build entry
        entry = {
            "hash": blob.hash,
            "name": meta.get("original_name", "unknown"),
            "file_type": meta.get("file_type", "unknown"),
            "category": meta.get("category", "unknown"),
            "page_count": meta.get("page_count", 0),
            "created_at": meta.get("created_at", datetime.now().isoformat()),
        }
        
        # Add archive info if present
        if meta.get("source_archive"):
            entry["source_archive"] = {
                "hash": meta["source_archive"]["hash"],
                "name": meta["source_archive"]["name"],
            }
        
        # Remove existing entry with same hash
        index["entries"] = [e for e in index["entries"] if e["hash"] != blob.hash]
        
        # Add new entry (at beginning for recency)
        index["entries"].insert(0, entry)
        
        self._save()
    
    def remove(self, blob_hash: str) -> None:
        """Remove entry from index."""
        index = self._load()
        index["entries"] = [e for e in index["entries"] if e["hash"] != blob_hash]
        self._save()
    
    def search(self, query: str) -> list[BlobRef]:
        """Search by name, file type, or hash prefix.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching blob references
        """
        index = self._load()
        query_lower = query.lower()
        results = []
        
        for entry in index["entries"]:
            # Match by name
            if query_lower in entry.get("name", "").lower():
                results.append(BlobRef(hash=entry["hash"]))
                continue
            
            # Match by hash prefix
            if entry["hash"].startswith(query_lower):
                results.append(BlobRef(hash=entry["hash"]))
                continue
            
            # Match by file type
            if query_lower == entry.get("file_type", "").lower():
                results.append(BlobRef(hash=entry["hash"]))
                continue
            
            # Match by archive name
            if entry.get("source_archive") and query_lower in entry["source_archive"].get("name", "").lower():
                results.append(BlobRef(hash=entry["hash"]))
                continue
        
        return results
    
    def list_by_archive(self, archive_hash: str) -> list[BlobRef]:
        """List all blobs from a specific archive.
        
        Args:
            archive_hash: Hash of the archive file
            
        Returns:
            List of blob references from that archive
        """
        index = self._load()
        results = []
        
        for entry in index["entries"]:
            if entry.get("source_archive", {}).get("hash") == archive_hash:
                results.append(BlobRef(hash=entry["hash"]))
        
        return results
    
    def get_entry(self, blob_hash: str) -> dict | None:
        """Get index entry by hash."""
        index = self._load()
        for entry in index["entries"]:
            if entry["hash"] == blob_hash or entry["hash"].startswith(blob_hash):
                return entry
        return None
    
    def list_all(self) -> list[dict]:
        """List all index entries."""
        return self._load().get("entries", [])
    
    def rebuild(self) -> int:
        """Rebuild index from all blob directories.
        
        Returns:
            Number of entries rebuilt
        """
        from .extractor import DocExtractor
        
        blobs_dir = DocExtractor.BLOBS_DIR
        count = 0
        
        self._data = {"version": "1.0", "updated_at": None, "entries": []}
        
        for path in blobs_dir.iterdir():
            if not path.is_dir() or len(path.name) != 64:
                continue
            
            blob = BlobRef(hash=path.name)
            self.add(blob)
            count += 1
        
        return count
    
    def clear(self) -> None:
        """Clear the index."""
        self._data = {"version": "1.0", "updated_at": None, "entries": []}
        self._save()
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        index = self._load()
        entries = index.get("entries", [])
        
        categories = {}
        archives = set()
        
        for entry in entries:
            cat = entry.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
            if entry.get("source_archive"):
                archives.add(entry["source_archive"]["hash"])
        
        return {
            "total_blobs": len(entries),
            "categories": categories,
            "archive_count": len(archives),
        }
