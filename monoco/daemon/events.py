"""
EventBus - Central event system for Agent scheduling.

DEPRECATED: This module has been moved to monoco.core.scheduler.
This file is kept for backward compatibility and re-exports from the new location.

Migration:
    Old: from monoco.daemon.events import AgentEventType, event_bus
    New: from monoco.core.scheduler import AgentEventType, event_bus
"""

import warnings
from monoco.core.scheduler import (
    AgentEventType,
    AgentEvent,
    EventBus,
    event_bus,
    EventHandler,
)

warnings.warn(
    "monoco.daemon.events is deprecated. "
    "Use monoco.core.scheduler instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "AgentEventType",
    "AgentEvent",
    "EventBus",
    "event_bus",
    "EventHandler",
]
