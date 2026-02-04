"""
Unit tests for Automation Configuration.
"""

import pytest
from pathlib import Path

from monoco.core.automation.config import (
    ActionConfig,
    TriggerConfig,
    AutomationConfig,
    load_automation_config,
    create_default_config,
    save_automation_config,
)
from monoco.core.scheduler import AgentEventType


class TestActionConfig:
    """Test suite for ActionConfig."""
    
    def test_action_config_creation(self):
        """ActionConfig can be created."""
        config = ActionConfig(
            type="SpawnAgentAction",
            params={"role": "Engineer"},
        )
        
        assert config.type == "SpawnAgentAction"
        assert config.params == {"role": "Engineer"}
    
    def test_action_config_from_dict(self):
        """ActionConfig can be created from dict."""
        data = {
            "type": "RunPytestAction",
            "params": {"test_path": "tests/"},
        }
        
        config = ActionConfig.from_dict(data)
        
        assert config.type == "RunPytestAction"
        assert config.params == {"test_path": "tests/"}
    
    def test_action_config_from_dict_minimal(self):
        """ActionConfig can be created from minimal dict."""
        data = {"type": "SendIMAction"}
        
        config = ActionConfig.from_dict(data)
        
        assert config.type == "SendIMAction"
        assert config.params == {}


class TestTriggerConfig:
    """Test suite for TriggerConfig."""
    
    def test_trigger_config_creation(self):
        """TriggerConfig can be created."""
        action = ActionConfig(type="SpawnAgentAction", params={"role": "Engineer"})
        
        config = TriggerConfig(
            name="issue_doing",
            watcher="IssueWatcher",
            event_type="issue.stage_changed",
            condition="value == 'doing'",
            field="stage",
            actions=[action],
            enabled=True,
            priority=10,
        )
        
        assert config.name == "issue_doing"
        assert config.watcher == "IssueWatcher"
        assert config.event_type == "issue.stage_changed"
        assert config.condition == "value == 'doing'"
        assert config.field == "stage"
        assert len(config.actions) == 1
        assert config.enabled is True
        assert config.priority == 10
    
    def test_trigger_config_from_dict(self):
        """TriggerConfig can be created from dict."""
        data = {
            "name": "memo_threshold",
            "watcher": "MemoWatcher",
            "event_type": "memo.threshold",
            "condition": "pending_count >= 5",
            "actions": [
                {"type": "SpawnAgentAction", "params": {"role": "Architect"}},
            ],
        }
        
        config = TriggerConfig.from_dict(data)
        
        assert config.name == "memo_threshold"
        assert config.watcher == "MemoWatcher"
        assert config.event_type == "memo.threshold"
        assert len(config.actions) == 1
        assert config.actions[0].type == "SpawnAgentAction"
    
    def test_trigger_config_to_agent_event_type(self):
        """TriggerConfig can convert event_type to AgentEventType."""
        config = TriggerConfig(
            name="test",
            watcher="TestWatcher",
            event_type="issue.stage_changed",
            actions=[],
        )
        
        event_type = config.to_agent_event_type()
        
        assert event_type == AgentEventType.ISSUE_STAGE_CHANGED
    
    def test_trigger_config_unknown_event_type(self):
        """TriggerConfig returns None for unknown event_type."""
        config = TriggerConfig(
            name="test",
            watcher="TestWatcher",
            event_type="unknown.event",
            actions=[],
        )
        
        event_type = config.to_agent_event_type()
        
        assert event_type is None


class TestAutomationConfig:
    """Test suite for AutomationConfig."""
    
    def test_automation_config_creation(self):
        """AutomationConfig can be created."""
        trigger = TriggerConfig(
            name="test",
            watcher="TestWatcher",
            actions=[],
        )
        
        config = AutomationConfig(
            version="1.0",
            triggers=[trigger],
            settings={"key": "value"},
        )
        
        assert config.version == "1.0"
        assert len(config.triggers) == 1
        assert config.settings == {"key": "value"}
    
    def test_automation_config_from_dict(self):
        """AutomationConfig can be created from dict."""
        data = {
            "version": "1.0",
            "triggers": [
                {
                    "name": "trigger1",
                    "watcher": "Watcher1",
                    "actions": [{"type": "Action1"}],
                },
            ],
            "settings": {"interval": 5},
        }
        
        config = AutomationConfig.from_dict(data)
        
        assert config.version == "1.0"
        assert len(config.triggers) == 1
        assert config.triggers[0].name == "trigger1"
        assert config.settings == {"interval": 5}
    
    def test_automation_config_from_yaml(self):
        """AutomationConfig can be loaded from YAML."""
        yaml_content = """
version: "1.0"
triggers:
  - name: test_trigger
    watcher: TestWatcher
    event_type: issue.created
    actions:
      - type: TestAction
settings:
  interval: 5
"""
        
        config = AutomationConfig.from_yaml(yaml_content)
        
        assert config.version == "1.0"
        assert len(config.triggers) == 1
        assert config.triggers[0].name == "test_trigger"
    
    def test_automation_config_from_json(self):
        """AutomationConfig can be loaded from JSON."""
        json_content = '''
        {
            "version": "1.0",
            "triggers": [
                {
                    "name": "test_trigger",
                    "watcher": "TestWatcher",
                    "actions": [{"type": "TestAction"}]
                }
            ],
            "settings": {"interval": 5}
        }
        '''
        
        config = AutomationConfig.from_json(json_content)
        
        assert config.version == "1.0"
        assert len(config.triggers) == 1
    
    def test_automation_config_to_yaml(self):
        """AutomationConfig can be exported to YAML."""
        trigger = TriggerConfig(
            name="test",
            watcher="TestWatcher",
            event_type="issue.created",
            actions=[ActionConfig(type="TestAction")],
        )
        
        config = AutomationConfig(
            version="1.0",
            triggers=[trigger],
        )
        
        yaml_output = config.to_yaml()
        
        assert "version: '1.0'" in yaml_output or 'version: "1.0"' in yaml_output
        assert "test" in yaml_output
        assert "TestWatcher" in yaml_output
    
    def test_automation_config_to_json(self):
        """AutomationConfig can be exported to JSON."""
        trigger = TriggerConfig(
            name="test",
            watcher="TestWatcher",
            actions=[ActionConfig(type="TestAction")],
        )
        
        config = AutomationConfig(
            version="1.0",
            triggers=[trigger],
        )
        
        json_output = config.to_json()
        
        assert '"version": "1.0"' in json_output
        assert '"name": "test"' in json_output
    
    def test_get_enabled_triggers(self):
        """Can get only enabled triggers."""
        trigger1 = TriggerConfig(name="enabled", watcher="Watcher", enabled=True, actions=[])
        trigger2 = TriggerConfig(name="disabled", watcher="Watcher", enabled=False, actions=[])
        
        config = AutomationConfig(triggers=[trigger1, trigger2])
        
        enabled = config.get_enabled_triggers()
        
        assert len(enabled) == 1
        assert enabled[0].name == "enabled"
    
    def test_get_trigger(self):
        """Can get trigger by name."""
        trigger = TriggerConfig(name="test", watcher="Watcher", actions=[])
        
        config = AutomationConfig(triggers=[trigger])
        
        found = config.get_trigger("test")
        not_found = config.get_trigger("nonexistent")
        
        assert found is trigger
        assert not_found is None
    
    def test_add_trigger(self):
        """Can add trigger."""
        config = AutomationConfig()
        trigger = TriggerConfig(name="new", watcher="Watcher", actions=[])
        
        config.add_trigger(trigger)
        
        assert len(config.triggers) == 1
        assert config.triggers[0].name == "new"
    
    def test_add_trigger_replaces_existing(self):
        """Adding trigger with same name replaces existing."""
        trigger1 = TriggerConfig(name="test", watcher="Watcher1", actions=[])
        trigger2 = TriggerConfig(name="test", watcher="Watcher2", actions=[])
        
        config = AutomationConfig(triggers=[trigger1])
        config.add_trigger(trigger2)
        
        assert len(config.triggers) == 1
        assert config.triggers[0].watcher == "Watcher2"
    
    def test_remove_trigger(self):
        """Can remove trigger by name."""
        trigger = TriggerConfig(name="test", watcher="Watcher", actions=[])
        config = AutomationConfig(triggers=[trigger])
        
        removed = config.remove_trigger("test")
        not_removed = config.remove_trigger("nonexistent")
        
        assert removed is True
        assert not_removed is False
        assert len(config.triggers) == 0


class TestConfigLoading:
    """Test suite for config loading functions."""
    
    def test_create_default_config(self):
        """Default config can be created."""
        config = create_default_config()
        
        assert config.version == "1.0"
        assert len(config.triggers) == 3
        assert config.get_trigger("memo_threshold") is not None
        assert config.get_trigger("issue_doing") is not None
        assert "default_poll_interval" in config.settings
    
    def test_load_automation_config_not_found(self, tmp_path):
        """Loading non-existent config returns empty config."""
        config_path = tmp_path / "nonexistent.yaml"
        
        config = load_automation_config(config_path)
        
        assert config.version == "1.0"
        assert len(config.triggers) == 0
    
    def test_load_automation_config_create_default(self, tmp_path):
        """Can create default config if not found."""
        config_path = tmp_path / "automation.yaml"
        
        config = load_automation_config(config_path, create_default=True)
        
        assert len(config.triggers) == 3
        assert config_path.exists()
    
    def test_load_automation_config_from_yaml_file(self, tmp_path):
        """Can load config from YAML file."""
        config_path = tmp_path / "automation.yaml"
        config_path.write_text("""
version: "1.0"
triggers:
  - name: test_trigger
    watcher: TestWatcher
    actions:
      - type: TestAction
""")
        
        config = load_automation_config(config_path)
        
        assert len(config.triggers) == 1
        assert config.triggers[0].name == "test_trigger"
    
    def test_save_automation_config(self, tmp_path):
        """Can save config to file."""
        config_path = tmp_path / "output" / "automation.yaml"
        trigger = TriggerConfig(name="test", watcher="Watcher", actions=[])
        config = AutomationConfig(triggers=[trigger])
        
        save_automation_config(config, config_path)
        
        assert config_path.exists()
        content = config_path.read_text()
        assert "test" in content
        assert "Watcher" in content
