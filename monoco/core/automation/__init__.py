"""
Automation Module - Event-driven automation framework.

This module provides:
- Field change detection
- Independent Event Handlers for Agent collaboration (FEAT-0162)

Architecture: No Workflow or Orchestration. Each handler is an independent,
stateless microservice that responds to specific events. Workflow emerges
from the natural interaction of handlers.
"""

from .field_watcher import (
    YAMLFrontMatterExtractor,
    FieldWatcher,
    FieldCondition,
)
from .handlers import (
    TaskFileHandler,
    IssueStageHandler,
    MemoThresholdHandler,
    PRCreatedHandler,
    start_all_handlers,
    stop_all_handlers,
)

__all__ = [
    # Field watching
    "YAMLFrontMatterExtractor",
    "FieldWatcher",
    "FieldCondition",
    # Independent Event Handlers (FEAT-0162)
    "TaskFileHandler",
    "IssueStageHandler",
    "MemoThresholdHandler",
    "PRCreatedHandler",
    # Convenience functions
    "start_all_handlers",
    "stop_all_handlers",
]
