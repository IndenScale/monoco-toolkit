import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

import logging

# Import AgentIntegration for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from monoco.core.integrations import AgentIntegration

logger = logging.getLogger("monoco.core.config")

class PathsConfig(BaseModel):
    """Configuration for directory paths."""
    root: str = Field(default=".", description="Project root directory")
    issues: str = Field(default="Issues", description="Directory for issues")
    spikes: str = Field(default=".references", description="Directory for spikes/research")
    specs: str = Field(default="SPECS", description="Directory for specifications")

class CoreConfig(BaseModel):
    """Core system configuration."""
    editor: str = Field(default_factory=lambda: os.getenv("EDITOR", "vim"), description="Preferred text editor")
    log_level: str = Field(default="INFO", description="Logging verbosity")
    author: Optional[str] = Field(default=None, description="Default author for new artifacts")

class ProjectConfig(BaseModel):
    """Project identity configuration."""
    name: str = Field(default="Monoco Project", description="Project name")
    key: str = Field(default="MON", description="Project key/prefix for IDs")
    spike_repos: Dict[str, str] = Field(default_factory=dict, description="Managed external research repositories (name -> url)")
    members: Dict[str, str] = Field(default_factory=dict, description="Workspace member projects (name -> relative_path)")

class I18nConfig(BaseModel):
    """Configuration for internationalization."""
    source_lang: str = Field(default="en", description="Source language code")
    target_langs: list[str] = Field(default_factory=lambda: ["zh"], description="Target language codes")

class UIConfig(BaseModel):
    """Configuration for UI customizations."""
    dictionary: Dict[str, str] = Field(default_factory=dict, description="Custom domain terminology mapping")

class TelemetryConfig(BaseModel):
    """Configuration for Telemetry."""
    enabled: Optional[bool] = Field(default=None, description="Whether telemetry is enabled")

class AgentConfig(BaseModel):
    """Configuration for Agent Environment Integration."""
    targets: Optional[list[str]] = Field(default=None, description="Specific target files to inject into (e.g. .cursorrules)")
    framework: Optional[str] = Field(default=None, description="Manually specified agent framework (cursor, windsurf, etc.)")
    includes: Optional[list[str]] = Field(default=None, description="List of specific features to include in injection")
    integrations: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Custom agent framework integrations (overrides defaults from monoco.core.integrations)"
    )

class MonocoConfig(BaseModel):
    """
    Main Configuration Schema.
    Hierarchy: Defaults < User Config (~/.monoco/config.yaml) < Project Config (./.monoco/config.yaml)
    """
    core: CoreConfig = Field(default_factory=CoreConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    i18n: I18nConfig = Field(default_factory=I18nConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)

    @staticmethod
    def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Recursive dict merge."""
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                MonocoConfig._deep_merge(base[k], v)
            else:
                base[k] = v
        return base

    @classmethod
    def load(cls, project_root: Optional[str] = None) -> "MonocoConfig":
        """
        Load configuration from multiple sources.
        """
        # 1. Start with empty dict (will use defaults via Pydantic)
        config_data = {}

        # 2. Define config paths
        home_path = Path.home() / ".monoco" / "config.yaml"
        
        # Determine project path
        cwd = Path(project_root) if project_root else Path.cwd()
        proj_path_hidden = cwd / ".monoco" / "config.yaml"
        
        # [Legacy] Check for monoco.yaml and warn
        proj_path_legacy = cwd / "monoco.yaml"
        if proj_path_legacy.exists():
            logger.warning(f"Legacy configuration found: {proj_path_legacy}. Please move it to .monoco/config.yaml")

        # 3. Load User Config
        if home_path.exists():
            try:
                with open(home_path, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        cls._deep_merge(config_data, user_config)
            except Exception as e:
                # We don't want to crash on config load fail, implementing simple warning equivalent
                pass

        # 4. Load Project Config (Only .monoco/config.yaml)
        if proj_path_hidden.exists():
            try:
                with open(proj_path_hidden, "r") as f:
                    proj_config = yaml.safe_load(f)
                    if proj_config:
                        cls._deep_merge(config_data, proj_config)
            except Exception:
                pass

        # 5. Instantiate Model
        return cls(**config_data)

# Global singleton
_settings = None

def get_config(project_root: Optional[str] = None) -> MonocoConfig:
    global _settings
    if _settings is None or project_root is not None:
        _settings = MonocoConfig.load(project_root)
    return _settings

class ConfigScope(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"

def get_config_path(scope: ConfigScope, project_root: Optional[str] = None) -> Path:
    """Get the path to the configuration file for a given scope."""
    if scope == ConfigScope.GLOBAL:
        return Path.home() / ".monoco" / "config.yaml"
    else:
        cwd = Path(project_root) if project_root else Path.cwd()
        return cwd / ".monoco" / "config.yaml"

def load_raw_config(scope: ConfigScope, project_root: Optional[str] = None) -> Dict[str, Any]:
    """Load raw configuration dictionary from a specific scope."""
    path = get_config_path(scope, project_root)
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to load config from {path}: {e}")
        return {}

def save_raw_config(scope: ConfigScope, data: Dict[str, Any], project_root: Optional[str] = None) -> None:
    """Save raw configuration dictionary to a specific scope."""
    path = get_config_path(scope, project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
