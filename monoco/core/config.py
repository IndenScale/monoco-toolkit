import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

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

class I18nConfig(BaseModel):
    """Configuration for internationalization."""
    source_lang: str = Field(default="en", description="Source language code")
    target_langs: list[str] = Field(default_factory=lambda: ["zh"], description="Target language codes")

class UIConfig(BaseModel):
    """Configuration for UI customizations."""
    dictionary: Dict[str, str] = Field(default_factory=dict, description="Custom domain terminology mapping")

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
        proj_path_root = cwd / "monoco.yaml"

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

        # 4. Load Project Config (prefer .monoco/config.yaml, fallback to monoco.yaml)
        target_proj_conf = proj_path_hidden if proj_path_hidden.exists() else (
            proj_path_root if proj_path_root.exists() else None
        )

        if target_proj_conf:
            try:
                with open(target_proj_conf, "r") as f:
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
