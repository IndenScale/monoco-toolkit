from typing import Dict, Optional
import yaml
from pathlib import Path
from .models import RoleTemplate, AgentRoleConfig as AgentConfig
from .defaults import DEFAULT_ROLES


class RoleLoader:
    """
    Tiered configuration loader for Agent Roles.
    Level 1: Builtin Resources (monoco/features/agent/resources/roles/*.yaml)
    Level 2: Global (~/.monoco/roles/*.yaml)
    Level 3: Project (./.monoco/roles/*.yaml)
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root
        self.user_home = Path.home()
        self.roles: Dict[str, RoleTemplate] = {}
        self.sources: Dict[str, str] = {}  # role_name -> source description

    def load_all(self) -> Dict[str, RoleTemplate]:
        # Level 1: Defaults (Hardcoded)
        for role in DEFAULT_ROLES:
            if role.name not in self.roles:
                self.roles[role.name] = role
                self.sources[role.name] = "builtin (default)"

        # Level 2: Global
        global_monoco = self.user_home / ".monoco"
        self._load_from_file(global_monoco / "roles.yaml", "global")
        self._load_from_dir(global_monoco / "roles", "global")

        # Level 3: Project
        if self.project_root:
            project_monoco = self.project_root / ".monoco"
            self._load_from_file(project_monoco / "roles.yaml", "project")
            self._load_from_dir(project_monoco / "roles", "project")

        return self.roles

    def _load_from_dir(self, directory: Path, source_label: str):
        if not directory.exists() or not directory.is_dir():
            return
        
        for file in directory.glob("*.yaml"):
            self._load_from_file(file, source_label)

    def _load_from_file(self, path: Path, source_label: str):
        if not path.exists():
            return

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}

            # Case A: Config object with "roles" list
            if "roles" in data and isinstance(data["roles"], list):
                config = AgentConfig(roles=data["roles"])
                for role in config.roles:
                    self._upsert_role(role, str(path))
            
            # Case B: Single Role object
            elif "name" in data and "system_prompt" in data:
                role = RoleTemplate(**data)
                self._upsert_role(role, str(path))
                
        except Exception as e:
            import sys
            print(f"Warning: Failed to load roles from {path}: {e}", file=sys.stderr)

    def _upsert_role(self, role: RoleTemplate, source: str):
        self.roles[role.name] = role
        self.sources[role.name] = source


def load_scheduler_config(project_root: Path) -> Dict[str, RoleTemplate]:
    """
    Legacy compatibility wrapper for functional access.
    """
    loader = RoleLoader(project_root)
    return loader.load_all()


def load_agent_config(project_root: Path) -> Dict[str, RoleTemplate]:
    """
    Load agent configuration from tiered sources.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        Dictionary mapping role names to RoleTemplate objects
    """
    loader = RoleLoader(project_root)
    return loader.load_all()
