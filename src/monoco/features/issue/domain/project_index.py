import re
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel
from monoco.core.config import get_config


class IssueLocation(BaseModel):
    project_id: str
    file_path: str
    issue_id: str


class ProjectSymbolIndex:
    """
    Maintains a global index of all issues in the Monoco Project.
    Allows resolving Issue IDs (local or namespaced) to file locations.
    """

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.index: Dict[str, IssueLocation] = {}  # Map<FullID, Location>
        self.local_map: Dict[
            str, str
        ] = {}  # Map<LocalID, FullID> for current context project
        self._is_indexed = False

    def build_index(self, recursive: bool = True):
        """
        Scans the project and linked projects to build the index.
        """
        self.index.clear()

        # 1. Index local project
        project_name = "local"
        conf = get_config(str(self.root_path))
        if conf and conf.project and conf.project.name:
            project_name = conf.project.name.lower()

        self._index_project(self.root_path, project_name)

        # 2. Index linked projects
        if recursive:
            try:
                for linked_name, rel_path in conf.project.linked_projects.items():
                    linked_root = (self.root_path / rel_path).resolve()
                    if linked_root.exists():
                        self._index_project(linked_root, linked_name.lower())
            except Exception:
                pass

        self._is_indexed = True

    def _index_project(self, project_root: Path, project_name: str):
        issues_dir = project_root / "Issues"
        if not issues_dir.exists():
            return

        # Scan Epics, Features, Chores, Fixes
        for subdir in ["Epics", "Features", "Chores", "Fixes"]:
            d = issues_dir / subdir
            if d.exists():
                for f in d.rglob("*.md"):
                    # Filename format: {ID}-{slug}.md
                    # Regex: EPIC-0016-title.md -> EPIC-0016
                    match = re.match(r"^((?:EPIC|FEAT|CHORE|FIX)-\d{4})", f.name)
                    if match:
                        issue_id = match.group(1)
                        full_id = f"{project_name}::{issue_id}"
                        loc = IssueLocation(
                            project_id=project_name,
                            file_path=str(f.absolute()),
                            issue_id=issue_id,
                        )
                        self.index[full_id] = loc
                        self.index[issue_id] = loc  # Alias for local lookup

    def resolve(
        self, issue_id: str, context_project: Optional[str] = None
    ) -> Optional[IssueLocation]:
        """
        Resolves an issue ID to its location.
        Supports 'Project::ID' and 'ID'.
        """
        if not self._is_indexed:
            self.build_index()

        # Normalize lookup ID
        if "::" in issue_id:
            proj, lid = issue_id.split("::", 1)
            issue_id = f"{proj.lower()}::{lid.upper()}"
        else:
            issue_id = issue_id.upper()
            if context_project:
                context_project = context_project.lower()

        # 1. Try exact match
        if issue_id in self.index:
            return self.index[issue_id]

        # 2. Try contextual resolution if it's a local ID
        if "::" not in issue_id and context_project:
            full_id = f"{context_project}::{issue_id}"
            if full_id in self.index:
                return self.index[full_id]

        return None
