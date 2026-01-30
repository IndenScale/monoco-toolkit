import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Awaitable, List
from enum import Enum
from pydantic import BaseModel, Field

import logging
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


logger = logging.getLogger("monoco.core.config")


class PathsConfig(BaseModel):
    """Configuration for directory paths."""

    root: str = Field(default=".", description="Project root directory")
    issues: str = Field(default="Issues", description="Directory for issues")
    spikes: str = Field(
        default=".references", description="Directory for spikes/research"
    )


class CoreConfig(BaseModel):
    """Core system configuration."""

    log_level: str = Field(default="INFO", description="Logging verbosity")
    author: Optional[str] = Field(
        default=None, description="Default author for new artifacts"
    )


class ProjectConfig(BaseModel):
    """Project identity configuration."""

    name: str = Field(default="Monoco Project", description="Project name")
    key: str = Field(default="MON", description="Project key/prefix for IDs")
    spike_repos: Dict[str, str] = Field(
        default_factory=dict,
        description="Managed external research repositories (name -> url)",
    )
    members: Dict[str, str] = Field(
        default_factory=dict,
        description="Workspace member projects (name -> relative_path)",
    )


class I18nConfig(BaseModel):
    """Configuration for internationalization."""

    source_lang: str = Field(default="en", description="Source language code")
    target_langs: list[str] = Field(
        default_factory=lambda: ["zh"], description="Target language codes"
    )


class UIConfig(BaseModel):
    """Configuration for UI customizations."""

    dictionary: Dict[str, str] = Field(
        default_factory=dict, description="Custom domain terminology mapping"
    )


class TelemetryConfig(BaseModel):
    """Configuration for Telemetry."""

    enabled: Optional[bool] = Field(
        default=None, description="Whether telemetry is enabled"
    )


class IssueTypeConfig(BaseModel):
    name: str
    label: str
    prefix: str
    folder: str
    description: Optional[str] = None


class TransitionConfig(BaseModel):
    name: str
    label: str
    icon: Optional[str] = None
    from_status: Optional[str] = None
    from_stage: Optional[str] = None
    to_status: str
    to_stage: Optional[str] = None
    required_solution: Optional[str] = None
    description: str = ""
    command_template: Optional[str] = None


class CriticalityRuleConfig(BaseModel):
    """Configuration for auto-escalation rules."""

    name: str
    description: str = ""
    path_patterns: List[str] = Field(default_factory=list)
    tag_patterns: List[str] = Field(default_factory=list)
    target_level: str = "medium"  # low, medium, high, critical


class CriticalityConfig(BaseModel):
    """Configuration for issue criticality system."""

    enabled: bool = Field(default=True)
    # Type to criticality default mapping
    type_defaults: Dict[str, str] = Field(
        default_factory=lambda: {
            "epic": "high",
            "feature": "medium",
            "chore": "low",
            "fix": "high",
        }
    )
    # Auto-escalation rules
    auto_rules: List[CriticalityRuleConfig] = Field(default_factory=list)

    def merge(self, other: "CriticalityConfig") -> "CriticalityConfig":
        if not other:
            return self
        if other.enabled is not None:
            self.enabled = other.enabled
        if other.type_defaults:
            self.type_defaults.update(other.type_defaults)
        if other.auto_rules:
            # Merge by name
            existing = {r.name: r for r in self.auto_rules}
            for rule in other.auto_rules:
                existing[rule.name] = rule
            self.auto_rules = list(existing.values())
        return self


class IssueSchemaConfig(BaseModel):
    types: List[IssueTypeConfig] = Field(default_factory=list)
    statuses: List[str] = Field(default_factory=list)
    stages: List[str] = Field(default_factory=list)
    solutions: List[str] = Field(default_factory=list)
    workflows: List[TransitionConfig] = Field(default_factory=list)
    criticality: CriticalityConfig = Field(default_factory=CriticalityConfig)

    def merge(self, other: "IssueSchemaConfig") -> "IssueSchemaConfig":
        if not other:
            return self

        # Types: merge by name
        if other.types:
            type_map = {t.name: t for t in self.types}
            for ot in other.types:
                type_map[ot.name] = ot
            self.types = list(type_map.values())

        # Statuses: replace if provided
        if other.statuses:
            self.statuses = other.statuses

        # Stages: replace if provided
        if other.stages:
            self.stages = other.stages

        # Solutions: replace if provided
        if other.solutions:
            self.solutions = other.solutions

        # Workflows (Transitions): merge by name
        if other.workflows:
            wf_map = {w.name: w for w in self.workflows}
            for ow in other.workflows:
                wf_map[ow.name] = ow
            self.workflows = list(wf_map.values())

        # Criticality config
        if other.criticality:
            self.criticality = self.criticality.merge(other.criticality)

        return self


class DomainItem(BaseModel):
    name: str = Field(..., description="Canonical domain name (e.g. backend.auth)")
    description: Optional[str] = Field(None, description="Description of the domain")
    aliases: List[str] = Field(default_factory=list, description="List of aliases")


class DomainConfig(BaseModel):
    items: List[DomainItem] = Field(
        default_factory=list, description="List of defined domains"
    )
    strict: bool = Field(
        default=False, description="If True, only allow defined domains"
    )

    def merge(self, other: "DomainConfig") -> "DomainConfig":
        if not other:
            return self

        # Merge items by name
        if other.items:
            item_map = {item.name: item for item in self.items}
            for item in other.items:
                # Overwrite or merge aliases? Let's overwrite for simplicity/consistency
                item_map[item.name] = item
            self.items = list(item_map.values())

        # Strict mode: logic? maybe strict overrides?
        # Let's say if ANY config asks for strict, it is strict? Or last one wins (project)?
        # Default merge is usually override.
        self.strict = other.strict

        return self


class StateMachineConfig(BaseModel):
    transitions: List[TransitionConfig]


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
    hooks: Dict[str, str] = Field(
        default_factory=dict,
        description="Git hooks configuration (hook_name -> command)",
    )
    session_hooks: Dict[str, Any] = Field(
        default_factory=dict,
        description="Session lifecycle hooks configuration (hook_name -> config)",
    )

    issue: IssueSchemaConfig = Field(default_factory=IssueSchemaConfig)
    domains: DomainConfig = Field(default_factory=DomainConfig)

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
    def load(
        cls, project_root: Optional[str] = None, require_project: bool = False
    ) -> "MonocoConfig":
        """
        Load configuration from multiple sources.

        Args:
            project_root: Explicit root path. If None, uses CWD.
            require_project: If True, raises error if .monoco directory is missing.
        """
        # 1. Start with empty dict (will use defaults via Pydantic)
        config_data = {}

        # 2. Define config paths
        home_path = Path.home() / ".monoco" / "config.yaml"

        # Determine project path
        cwd = Path(project_root) if project_root else Path.cwd()
        # FIX-0009: strict separation of workspace and project config
        workspace_config_path = cwd / ".monoco" / "workspace.yaml"
        project_config_path = cwd / ".monoco" / "project.yaml"

        # Strict Workspace Check
        if require_project and not (cwd / ".monoco").exists():
            raise FileNotFoundError(
                f"Monoco workspace not found in {cwd}. (No .monoco directory)"
            )

        # 3. Load User Config
        if home_path.exists():
            try:
                with open(home_path, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        cls._deep_merge(config_data, user_config)
            except Exception:
                # We don't want to crash on config load fail, implementing simple warning equivalent
                pass

        # 4. Load Project/Workspace Config

        # 4a. Load workspace.yaml (Global Environment)
        if workspace_config_path.exists():
            try:
                with open(workspace_config_path, "r") as f:
                    ws_config = yaml.safe_load(f)
                    if ws_config:
                        # workspace.yaml contains core, paths, i18n, ui, telemetry, agent
                        cls._deep_merge(config_data, ws_config)
            except Exception:
                pass

        # 4b. Load project.yaml (Identity)
        if project_config_path.exists():
            try:
                with open(project_config_path, "r") as f:
                    pj_config = yaml.safe_load(f)
                    if pj_config:
                        # project.yaml contains 'project' fields directly? or under 'project' key?
                        # Design decision: project.yaml should be clean, e.g. "name: foo".
                        # But to simplify merging, let's check if it has a 'project' key or is flat.
                        if "project" in pj_config:
                            cls._deep_merge(config_data, pj_config)
                        else:
                            # Assume flat structure mapping to 'project' section
                            if "project" not in config_data:
                                config_data["project"] = {}
                            cls._deep_merge(config_data["project"], pj_config)
            except Exception:
                pass

        # 5. Instantiate Model
        return cls(**config_data)


# Global singleton
_settings = None


def get_config(
    project_root: Optional[str] = None, require_project: bool = False
) -> MonocoConfig:
    global _settings
    # If explicit root provided, always reload.
    # If require_project is True, we must reload to ensure validation happens (in case a previous loose load occurred).
    if _settings is None or project_root is not None or require_project:
        _settings = MonocoConfig.load(project_root, require_project=require_project)
    return _settings


class ConfigScope(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"
    WORKSPACE = "workspace"


def get_config_path(scope: ConfigScope, project_root: Optional[str] = None) -> Path:
    """Get the path to the configuration file for a given scope."""
    if scope == ConfigScope.GLOBAL:
        return Path.home() / ".monoco" / "config.yaml"
    elif scope == ConfigScope.WORKSPACE:
        cwd = Path(project_root) if project_root else Path.cwd()
        return cwd / ".monoco" / "workspace.yaml"
    else:
        # ConfigScope.PROJECT
        cwd = Path(project_root) if project_root else Path.cwd()
        return cwd / ".monoco" / "project.yaml"


def find_monoco_root(start_path: Optional[Path] = None) -> Path:
    """
    Find the Monoco Workspace root.
    Strictly restricted to checking the current directory (or its parent if CWD is .monoco).
    Recursive upward lookup is disabled per FIX-0009.
    """
    current = (start_path or Path.cwd()).resolve()

    # Check if we are inside a .monoco folder
    if current.name == ".monoco":
        return current.parent

    # Check if current directory has .monoco
    if (current / ".monoco").exists():
        return current

    return current


def load_raw_config(
    scope: ConfigScope, project_root: Optional[str] = None
) -> Dict[str, Any]:
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


def save_raw_config(
    scope: ConfigScope, data: Dict[str, Any], project_root: Optional[str] = None
) -> None:
    """Save raw configuration dictionary to a specific scope."""
    path = get_config_path(scope, project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


class ConfigEventHandler(FileSystemEventHandler):
    def __init__(
        self, loop, on_change: Callable[[], Awaitable[None]], config_path: Path
    ):
        self.loop = loop
        self.on_change = on_change
        self.config_path = config_path

    def on_modified(self, event):
        if event.src_path == str(self.config_path):
            asyncio.run_coroutine_threadsafe(self.on_change(), self.loop)


class ConfigMonitor:
    """
    Monitors a configuration file for changes.
    """

    def __init__(self, config_path: Path, on_change: Callable[[], Awaitable[None]]):
        self.config_path = config_path
        self.on_change = on_change
        self.observer = Observer()

    async def start(self):
        loop = asyncio.get_running_loop()
        event_handler = ConfigEventHandler(loop, self.on_change, self.config_path)

        if not self.config_path.exists():
            # Ensure parent exists at least
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # We watch the parent directory for the specific file
        self.observer.schedule(
            event_handler, str(self.config_path.parent), recursive=False
        )
        self.observer.start()
        logger.info(f"Config Monitor started for {self.config_path}")

    def stop(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        logger.info(f"Config Monitor stopped for {self.config_path}")
