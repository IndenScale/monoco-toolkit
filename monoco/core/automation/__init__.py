"""
Automation Module - Configuration and orchestration for the Event Automation Framework.

This module provides:
- YAML/JSON configuration parsing
- Trigger configuration management
- Field change detection
- Automation orchestration
"""

from .config import (
    TriggerConfig,
    AutomationConfig,
    load_automation_config,
)
from .field_watcher import (
    YAMLFrontMatterExtractor,
    FieldWatcher,
    FieldCondition,
)
from .orchestrator import AutomationOrchestrator

__all__ = [
    "TriggerConfig",
    "AutomationConfig",
    "load_automation_config",
    "YAMLFrontMatterExtractor",
    "FieldWatcher",
    "FieldCondition",
    "AutomationOrchestrator",
]
