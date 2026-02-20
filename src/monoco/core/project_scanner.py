import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from monoco.core.config import get_config, MonocoConfig


class MonocoProject(BaseModel):
    """
    Representation of a single Monoco project.
    """

    id: str  # Unique ID within the project (usually the directory name)
    name: str
    path: Path
    config: MonocoConfig

    @property
    def issues_root(self) -> Path:
        issues_path = Path(self.config.paths.issues)
        if issues_path.is_absolute():
            return issues_path
        return (self.path / issues_path).resolve()

    model_config = ConfigDict(arbitrary_types_allowed=True)


def is_project_root(path: Path) -> bool:
    """
    Check if a directory serves as a Monoco project root.
    Criteria:
    - has .monoco/ directory (which should contain project.yaml)
    """
    if not path.is_dir():
        return False

    return (path / ".monoco").is_dir()


def load_project(path: Path) -> Optional[MonocoProject]:
    """Load a project from a path if it is a valid project root."""
    if not is_project_root(path):
        return None

    try:
        config = get_config(str(path))
        # If name is default, use directory name
        name = config.project.name
        if name == "Monoco Project":
            name = path.name

        return MonocoProject(id=path.name, name=name, path=path, config=config)
    except Exception:
        return None


def find_projects(project_root: Path) -> List[MonocoProject]:
    """
    Scan for projects in a project directory.
    Returns list of MonocoProject instances.
    """
    projects = []

    # 1. Check project root itself
    root_project = load_project(project_root)
    if root_project:
        projects.append(root_project)

    # 2. Recursive Scan
    for root, dirs, files in os.walk(project_root):
        # Skip hidden directories and node_modules
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and d != "node_modules" and d != "venv"
        ]

        for d in dirs:
            project_path = Path(root) / d
            # Avoid re-adding root if it was somehow added (unlikely here)
            if project_path == project_root:
                continue

            if is_project_root(project_path):
                p = load_project(project_path)
                if p:
                    projects.append(p)

    return projects


class ProjectScanner(BaseModel):
    """
    Project scanner for discovering Monoco projects within a directory.
    """

    root: Path
    projects: List[MonocoProject] = []

    @classmethod
    def discover(cls, root: Path) -> "ProjectScanner":
        projects = find_projects(root)
        return cls(root=root, projects=projects)

    def get_project(self, project_id: str) -> Optional[MonocoProject]:
        for p in self.projects:
            if p.id == project_id:
                return p
        return None

    model_config = ConfigDict(arbitrary_types_allowed=True)
