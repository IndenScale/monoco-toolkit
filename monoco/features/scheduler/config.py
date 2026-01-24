import yaml
from pathlib import Path
from typing import Dict
from .models import RoleTemplate, SchedulerConfig
from .defaults import DEFAULT_ROLES


def load_scheduler_config(project_root: Path) -> Dict[str, RoleTemplate]:
    """
    Load scheduler configuration from .monoco/scheduler.yaml
    Merges with default roles.
    """
    roles = {role.name: role for role in DEFAULT_ROLES}

    config_path = project_root / ".monoco" / "scheduler.yaml"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}

            # Use Pydantic to validate the whole config if possible, or just the roles list
            # Depending on file structure. Assuming the file has a 'roles' key.
            if "roles" in data:
                # We can validate using SchedulerConfig
                config = SchedulerConfig(roles=data["roles"])
                for role in config.roles:
                    roles[role.name] = role
        except Exception as e:
            # For now, just log or print. Ideally use a logger.
            print(f"Warning: Failed to load scheduler config: {e}")

    return roles
