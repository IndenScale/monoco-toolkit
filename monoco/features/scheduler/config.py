from typing import Dict, Optional
import yaml
from pathlib import Path
from .models import RoleTemplate, SchedulerConfig
from .defaults import DEFAULT_ROLES


class RoleLoader:
    """
    Tiered configuration loader for Agent Roles.
    Level 1: Builtin Fallback
    Level 2: Global (~/.monoco/roles.yaml)
    Level 3: Project (./.monoco/roles.yaml)
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root
        self.user_home = Path.home()
        self.roles: Dict[str, RoleTemplate] = {}
        self.sources: Dict[str, str] = {}  # role_name -> source description

    def load_all(self) -> Dict[str, RoleTemplate]:
        # Level 1: Defaults
        for role in DEFAULT_ROLES:
            self.roles[role.name] = role
            self.sources[role.name] = "builtin"

        # Level 2: Global
        global_path = self.user_home / ".monoco" / "roles.yaml"
        self._load_from_path(global_path, "global")

        # Level 3: Project
        if self.project_root:
            project_path = self.project_root / ".monoco" / "roles.yaml"
            self._load_from_path(project_path, "project")

        return self.roles

    def _load_from_path(self, path: Path, source_label: str):
        if not path.exists():
            return

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}

            if "roles" in data:
                # Validate using SchedulerConfig
                config = SchedulerConfig(roles=data["roles"])
                for role in config.roles:
                    # Level 3 > Level 2 > Level 1 (名字相同的 Role 进行覆盖/Merge)
                    # Currently we do total replacement for same-named roles
                    self.roles[role.name] = role
                    self.sources[role.name] = str(path)
        except Exception as e:
            # We don't want to crash the whole tool if a config is malformed,
            # but we should probably warn.
            import sys

            print(f"Warning: Failed to load roles from {path}: {e}", file=sys.stderr)


def load_scheduler_config(project_root: Path) -> Dict[str, RoleTemplate]:
    """
    Legacy compatibility wrapper for functional access.
    """
    loader = RoleLoader(project_root)
    return loader.load_all()
