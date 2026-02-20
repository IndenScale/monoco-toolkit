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
    trunk_branch: str = Field(
        default="main",
        description="Trunk branch name for TBD workflow (default: main, fallback: master)"
    )
    spike_repos: Dict[str, str] = Field(
        default_factory=dict,
        description="Managed external research repositories (name -> url)",
    )
    linked_projects: Dict[str, str] = Field(
        default_factory=dict,
        description="Linked projects for cross-project issue resolution (name -> relative_path)",
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


class HooksConfig(BaseModel):
    """Configuration for git hooks management."""

    enabled: bool = Field(default=True, description="Whether hooks system is enabled")
    features: Dict[str, bool] = Field(
        default_factory=dict,
        description="Per-feature hook enable/disable (feature_name -> enabled)"
    )
    hooks: Dict[str, bool] = Field(
        default_factory=lambda: {
            "pre-commit": True,
            "pre-push": False,
            "post-checkout": False,
        },
        description="Per-hook-type enable/disable (hook_type -> enabled)"
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
    post_actions: List[str] = Field(default_factory=list)


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


class AgentConcurrencyConfig(BaseModel):
    """Configuration for agent concurrency limits (semaphore-based)."""
    global_max: int = Field(default=3, description="Global maximum concurrent agents across all roles")
    engineer: int = Field(default=1, description="Maximum concurrent Engineer agents")
    architect: int = Field(default=1, description="Maximum concurrent Architect agents")
    reviewer: int = Field(default=1, description="Maximum concurrent Reviewer agents")
    # Note: Planner role removed in FEAT-0155 (was never used)
    # Cool-down configuration
    failure_cooldown_seconds: int = Field(default=60, description="Cooldown period after a failure before retrying")


class AgentConfig(BaseModel):
    """Configuration for AI Agents."""
    timeout_seconds: int = Field(default=900, description="Global timeout for agent sessions")
    concurrency: AgentConcurrencyConfig = Field(default_factory=AgentConcurrencyConfig)


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
    Hierarchy: Defaults < User Config (~/.monoco/config.yaml)
    """

    core: CoreConfig = Field(default_factory=CoreConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    i18n: I18nConfig = Field(default_factory=I18nConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    hooks: HooksConfig = Field(default_factory=HooksConfig)
    session_hooks: Dict[str, Any] = Field(
        default_factory=dict,
        description="Session lifecycle hooks configuration (hook_name -> config)",
    )

    issue: IssueSchemaConfig = Field(default_factory=IssueSchemaConfig)
    domains: DomainConfig = Field(default_factory=DomainConfig)
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
    def load(
        cls, project_root: Optional[str] = None, require_project: bool = False
    ) -> "MonocoConfig":
        """
        Load configuration from ~/.monoco/config.yaml.

        Args:
            project_root: Deprecated, kept for API compatibility.
            require_project: Deprecated, kept for API compatibility.
        """
        # Start with empty dict (will use defaults via Pydantic)
        config_data = {}

        # Load User Config from ~/.monoco/config.yaml
        home_path = Path.home() / ".monoco" / "config.yaml"
        if home_path.exists():
            try:
                with open(home_path, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        cls._deep_merge(config_data, user_config)
            except Exception:
                # We don't want to crash on config load fail, implementing simple warning equivalent
                pass

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
    """Configuration scope - only GLOBAL is supported."""

    GLOBAL = "global"


def get_config_path(scope: ConfigScope = ConfigScope.GLOBAL) -> Path:
    """Get the path to the configuration file.

    Args:
        scope: Deprecated parameter, kept for API compatibility.

    Returns:
        Path to ~/.monoco/config.yaml
    """
    return Path.home() / ".monoco" / "config.yaml"


def load_raw_config() -> Dict[str, Any]:
    """Load raw configuration dictionary from ~/.monoco/config.yaml."""
    path = get_config_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to load config from {path}: {e}")
        return {}


def save_raw_config(data: Dict[str, Any]) -> None:
    """Save raw configuration dictionary to ~/.monoco/config.yaml."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def find_monoco_root(start_path: Optional[Path] = None) -> Path:
    """
    Find the Monoco Project root.
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
        self._started = False

    async def start(self):
        if self._started:
            logger.warning(f"Config Monitor already started for {self.config_path}")
            return

        loop = asyncio.get_running_loop()
        event_handler = ConfigEventHandler(loop, self.on_change, self.config_path)

        if not self.config_path.exists():
            # Ensure parent exists at least
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Watch the specific file, not the parent directory
        # This avoids "already scheduled" errors when multiple files are in the same directory
        try:
            self.observer.schedule(
                event_handler, str(self.config_path), recursive=False
            )
            self.observer.start()
            self._started = True
            logger.info(f"Config Monitor started for {self.config_path}")
        except RuntimeError as e:
            logger.error(f"Failed to start Config Monitor for {self.config_path}: {e}")
            raise

    def stop(self):
        if not self._started:
            return
        try:
            if self.observer.is_alive():
                self.observer.stop()
                self.observer.join()
            logger.info(f"Config Monitor stopped for {self.config_path}")
        except Exception as e:
            logger.warning(f"Error stopping Config Monitor: {e}")
        finally:
            self._started = False
