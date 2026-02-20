from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import json
import logging
from monoco.core.feature import MonocoFeature
from monoco.core.loader import FeatureLoader, FeatureRegistry as LoaderFeatureRegistry

logger = logging.getLogger(__name__)


@dataclass
class ProjectInventoryEntry:
    """Information about a Monoco project in the global inventory."""
    slug: str
    path: Path
    mailbox: Path
    config: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "path": str(self.path),
            "mailbox": str(self.mailbox),
            "config": self.config or {}
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProjectInventoryEntry":
        return cls(
            slug=d["slug"],
            path=Path(d["path"]),
            mailbox=Path(d["mailbox"]),
            config=d.get("config", {})
        )


class ProjectInventory:
    """
    Global project inventory management.
    Stored at ~/.monoco/inventory.json
    """
    FILE_PATH = Path.home() / ".monoco" / "inventory.json"

    def __init__(self):
        self._entries: Dict[str, ProjectInventoryEntry] = {}
        self.load()

    def register(self, slug: str, path: Path, config: Optional[Dict[str, Any]] = None) -> ProjectInventoryEntry:
        """Register a project path with a unique slug."""
        path = Path(path).resolve()
        mailbox = path / ".monoco" / "mailbox"

        entry = ProjectInventoryEntry(
            slug=slug,
            path=path,
            mailbox=mailbox,
            config=config or {}
        )
        self._entries[slug] = entry
        self.save()
        logger.info(f"Registered project '{slug}' -> {path}")
        return entry

    def get(self, slug: str) -> Optional[ProjectInventoryEntry]:
        """Get project entry by slug."""
        return self._entries.get(slug)

    def list(self) -> List[ProjectInventoryEntry]:
        """List all registered projects."""
        return list(self._entries.values())

    def remove(self, slug: str):
        """Remove a project registration."""
        if slug in self._entries:
            del self._entries[slug]
            self.save()
            logger.info(f"Removed project registration for '{slug}'")

    def save(self):
        """Persist inventory to disk."""
        try:
            self.FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {slug: entry.to_dict() for slug, entry in self._entries.items()}
            with open(self.FILE_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save project inventory: {e}")

    def load(self):
        """Load inventory from disk."""
        if not self.FILE_PATH.exists():
            return
        try:
            with open(self.FILE_PATH, "r") as f:
                data = json.load(f)
                self._entries = {slug: ProjectInventoryEntry.from_dict(d) for slug, d in data.items()}
            logger.debug(f"Loaded {len(self._entries)} projects from global inventory")
        except Exception as e:
            logger.error(f"Failed to load project inventory: {e}")


# Singleton instance
_inventory: Optional[ProjectInventory] = None


def get_inventory() -> ProjectInventory:
    """Get the global project inventory singleton."""
    global _inventory
    if _inventory is None:
        _inventory = ProjectInventory()
    return _inventory




class FeatureRegistry:
    """
    Feature registry that wraps the new unified FeatureLoader.
    
    This class provides backward compatibility while delegating to the
    new FeatureLoader for dynamic discovery and lifecycle management.
    """

    _loader: Optional[FeatureLoader] = None

    @classmethod
    def _get_loader(cls) -> FeatureLoader:
        """Get or create the default feature loader."""
        if cls._loader is None:
            cls._loader = FeatureLoader()
            # Discover and load all features
            cls._loader.discover()
            cls._loader.load_all()
        return cls._loader

    @classmethod
    def register(cls, feature: MonocoFeature):
        """Register a feature instance."""
        loader = cls._get_loader()
        loader.registry.register(feature)  # type: ignore

    @classmethod
    def get_features(cls) -> List[MonocoFeature]:
        """Get all registered features."""
        loader = cls._get_loader()
        return loader.registry.get_all()  # type: ignore

    @classmethod
    def get_feature(cls, name: str) -> Optional[MonocoFeature]:
        """Get a specific feature by name."""
        loader = cls._get_loader()
        return loader.registry.get(name)  # type: ignore

    @classmethod
    def load_defaults(cls):
        """
        Load default core features using the unified FeatureLoader.
        
        This method discovers and loads all features from monoco/features/
        automatically, replacing the manual registration approach.
        """
        loader = cls._get_loader()
        # Features are already discovered and loaded in _get_loader
        # This method is kept for backward compatibility
