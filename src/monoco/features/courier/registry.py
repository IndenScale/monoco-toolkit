import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict

from .constants import COURIER_REGISTRY_FILE

logger = logging.getLogger(__name__)

@dataclass
class ProjectInfo:
    """Information about a Monoco project."""
    project_id: str
    root_path: Path
    mailbox_path: Path
    config: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["root_path"] = str(self.root_path)
        d["mailbox_path"] = str(self.mailbox_path)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProjectInfo":
        return cls(
            project_id=d["project_id"],
            root_path=Path(d["root_path"]),
            mailbox_path=Path(d["mailbox_path"]),
            config=d["config"]
        )

class ProjectRegistry:
    """
    Registry for Monoco projects handled by Courier.
    """
    
    def __init__(self, persistence_file: Optional[Path] = None):
        # Slug -> ProjectInfo
        self._mappings: Dict[str, ProjectInfo] = {}
        self.persistence_file = persistence_file or COURIER_REGISTRY_FILE
        self.load()

    def register(self, slug: str, root_path: Path, config: Optional[Dict[str, Any]] = None) -> ProjectInfo:
        """Register a project with a slug."""
        root_path = Path(root_path).resolve()
        mailbox_path = root_path / ".monoco" / "mailbox"
        
        # Load secret from .env if available
        secret = None
        env_path = root_path / ".env"
        if env_path.exists():
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        if line.startswith("DINGTALK_SECRET="):
                            secret = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
            except Exception as e:
                logger.warning(f"Failed to read .env for secret: {e}")
        
        if not config:
            config = {}
        if secret:
            config["dingtalk_secret"] = secret

        info = ProjectInfo(
            project_id=slug,
            root_path=root_path,
            mailbox_path=mailbox_path,
            config=config
        )
        
        self._mappings[slug] = info
        logger.info(f"Registered project slug '{slug}' -> {root_path} (Secret: {'found' if secret else 'not found'})")
        self.save()
        return info

    def get_project(self, slug: str) -> Optional[ProjectInfo]:
        """Get project info by slug."""
        return self._mappings.get(slug)

    def list_slugs(self) -> List[str]:
        """List all registered slugs."""
        return list(self._mappings.keys())

    def save(self):
        """Save registry to persistent storage."""
        try:
            self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
            data = {slug: info.to_dict() for slug, info in self._mappings.items()}
            with open(self.persistence_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved registry to {self.persistence_file}")
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def load(self):
        """Load registry from persistent storage."""
        if not self.persistence_file.exists():
            return
        
        try:
            with open(self.persistence_file, "r") as f:
                data = json.load(f)
                for slug, info_dict in data.items():
                    self._mappings[slug] = ProjectInfo.from_dict(info_dict)
            logger.info(f"Loaded {len(self._mappings)} project mappings from {self.persistence_file}")
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")

    def clear(self):
        """Clear the registry."""
        self._mappings.clear()
        self.save()
