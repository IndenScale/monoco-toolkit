"""
Automation Configuration - YAML/JSON configuration for triggers.

Part of the Event Automation Framework.
Provides configuration schema and loading for automation triggers.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from monoco.core.scheduler import AgentEventType

logger = logging.getLogger(__name__)


@dataclass
class ActionConfig:
    """Configuration for an action."""
    type: str
    params: Dict[str, Any] = dataclass_field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionConfig":
        """Create from dict."""
        return cls(
            type=data.get("type", ""),
            params=data.get("params", {}),
        )


@dataclass
class TriggerConfig:
    """
    Configuration for a trigger.
    
    Attributes:
        name: Unique trigger name
        watcher: Watcher type (IssueWatcher, MemoWatcher, etc.)
        event_type: Event type to listen for
        condition: Optional condition expression
        field: Optional field to watch (for field-level triggers)
        actions: List of actions to execute
        enabled: Whether trigger is enabled
    """
    name: str
    watcher: str
    event_type: Optional[str] = None
    condition: Optional[str] = None
    field: Optional[str] = None
    actions: List[ActionConfig] = dataclass_field(default_factory=list)
    enabled: bool = True
    priority: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerConfig":
        """Create from dict."""
        actions = [
            ActionConfig.from_dict(a) if isinstance(a, dict) else ActionConfig(type=a)
            for a in data.get("actions", [])
        ]
        
        return cls(
            name=data.get("name", "unnamed"),
            watcher=data.get("watcher", ""),
            event_type=data.get("event_type"),
            condition=data.get("condition"),
            field=data.get("field"),
            actions=actions,
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
        )
    
    def to_agent_event_type(self) -> Optional[AgentEventType]:
        """Convert event_type string to AgentEventType."""
        if not self.event_type:
            return None
        
        try:
            return AgentEventType(self.event_type)
        except ValueError:
            # Try to map common patterns
            mapping = {
                "issue.created": AgentEventType.ISSUE_CREATED,
                "issue.updated": AgentEventType.ISSUE_UPDATED,
                "issue.stage_changed": AgentEventType.ISSUE_STAGE_CHANGED,
                "issue.status_changed": AgentEventType.ISSUE_STATUS_CHANGED,
                "memo.created": AgentEventType.MEMO_CREATED,
                "memo.threshold": AgentEventType.MEMO_THRESHOLD,
                "session.completed": AgentEventType.SESSION_COMPLETED,
                "session.failed": AgentEventType.SESSION_FAILED,
                "pr.created": AgentEventType.PR_CREATED,
            }
            return mapping.get(self.event_type)


@dataclass
class AutomationConfig:
    """
    Complete automation configuration.
    
    Attributes:
        version: Configuration version
        triggers: List of trigger configurations
        settings: Global settings
    """
    version: str = "1.0"
    triggers: List[TriggerConfig] = dataclass_field(default_factory=list)
    settings: Dict[str, Any] = dataclass_field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomationConfig":
        """Create from dict."""
        triggers = [
            TriggerConfig.from_dict(t)
            for t in data.get("triggers", [])
        ]
        
        return cls(
            version=data.get("version", "1.0"),
            triggers=triggers,
            settings=data.get("settings", {}),
        )
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> "AutomationConfig":
        """Load from YAML string."""
        data = yaml.safe_load(yaml_content)
        return cls.from_dict(data or {})
    
    @classmethod
    def from_json(cls, json_content: str) -> "AutomationConfig":
        """Load from JSON string."""
        data = json.loads(json_content)
        return cls.from_dict(data)
    
    def to_yaml(self) -> str:
        """Export to YAML string."""
        data = {
            "version": self.version,
            "triggers": [
                {
                    "name": t.name,
                    "watcher": t.watcher,
                    "event_type": t.event_type,
                    "condition": t.condition,
                    "field": t.field,
                    "actions": [
                        {"type": a.type, "params": a.params}
                        for a in t.actions
                    ],
                    "enabled": t.enabled,
                    "priority": t.priority,
                }
                for t in self.triggers
            ],
            "settings": self.settings,
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    def to_json(self) -> str:
        """Export to JSON string."""
        data = {
            "version": self.version,
            "triggers": [
                {
                    "name": t.name,
                    "watcher": t.watcher,
                    "event_type": t.event_type,
                    "condition": t.condition,
                    "field": t.field,
                    "actions": [
                        {"type": a.type, "params": a.params}
                        for a in t.actions
                    ],
                    "enabled": t.enabled,
                    "priority": t.priority,
                }
                for t in self.triggers
            ],
            "settings": self.settings,
        }
        return json.dumps(data, indent=2)
    
    def get_enabled_triggers(self) -> List[TriggerConfig]:
        """Get all enabled triggers."""
        return [t for t in self.triggers if t.enabled]
    
    def get_trigger(self, name: str) -> Optional[TriggerConfig]:
        """Get trigger by name."""
        for trigger in self.triggers:
            if trigger.name == name:
                return trigger
        return None
    
    def add_trigger(self, trigger: TriggerConfig) -> None:
        """Add a trigger."""
        # Remove existing trigger with same name
        self.triggers = [t for t in self.triggers if t.name != trigger.name]
        self.triggers.append(trigger)
    
    def remove_trigger(self, name: str) -> bool:
        """Remove a trigger by name."""
        original_count = len(self.triggers)
        self.triggers = [t for t in self.triggers if t.name != name]
        return len(self.triggers) < original_count


def load_automation_config(
    path: Union[str, Path],
    create_default: bool = False,
) -> AutomationConfig:
    """
    Load automation configuration from file.
    
    Supports .yaml, .yml, and .json files.
    
    Args:
        path: Path to configuration file
        create_default: If True and file doesn't exist, create default config
        
    Returns:
        AutomationConfig instance
    """
    path = Path(path)
    
    if not path.exists():
        if create_default:
            default_config = create_default_config()
            path.write_text(default_config.to_yaml())
            logger.info(f"Created default automation config at {path}")
            return default_config
        else:
            logger.warning(f"Config file not found: {path}")
            return AutomationConfig()
    
    content = path.read_text(encoding="utf-8")
    
    if path.suffix in (".yaml", ".yml"):
        return AutomationConfig.from_yaml(content)
    elif path.suffix == ".json":
        return AutomationConfig.from_json(content)
    else:
        # Try YAML first, then JSON
        try:
            return AutomationConfig.from_yaml(content)
        except yaml.YAMLError:
            return AutomationConfig.from_json(content)


def create_default_config() -> AutomationConfig:
    """Create a default automation configuration."""
    return AutomationConfig(
        version="1.0",
        triggers=[
            TriggerConfig(
                name="memo_threshold",
                watcher="MemoWatcher",
                event_type="memo.threshold",
                condition="pending_count >= 5",
                actions=[
                    ActionConfig(
                        type="SpawnAgentAction",
                        params={"role": "Architect"},
                    ),
                ],
            ),
            TriggerConfig(
                name="issue_doing",
                watcher="IssueWatcher",
                event_type="issue.stage_changed",
                field="stage",
                condition="value == 'doing'",
                actions=[
                    ActionConfig(
                        type="SpawnAgentAction",
                        params={"role": "Engineer"},
                    ),
                ],
            ),
            TriggerConfig(
                name="issue_completed",
                watcher="IssueWatcher",
                event_type="issue.stage_changed",
                field="stage",
                condition="value == 'done'",
                actions=[
                    ActionConfig(
                        type="SendIMAction",
                        params={
                            "channel": "console",
                            "message_template": "Issue {issue_id} completed!",
                        },
                    ),
                ],
            ),
        ],
        settings={
            "default_poll_interval": 5.0,
            "max_concurrent_actions": 10,
            "action_timeout": 300,
        },
    )


def save_automation_config(
    config: AutomationConfig,
    path: Union[str, Path],
    format: str = "yaml",
) -> None:
    """
    Save automation configuration to file.
    
    Args:
        config: Configuration to save
        path: Path to save to
        format: "yaml" or "json"
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == "yaml":
        content = config.to_yaml()
        if path.suffix not in (".yaml", ".yml"):
            path = path.with_suffix(".yaml")
    else:
        content = config.to_json()
        if path.suffix != ".json":
            path = path.with_suffix(".json")
    
    path.write_text(content, encoding="utf-8")
    logger.info(f"Saved automation config to {path}")
