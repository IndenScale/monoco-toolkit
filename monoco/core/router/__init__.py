"""
Router Module - Layer 2 of the Event Automation Framework.

This module provides event routing capabilities that map events to actions.
It is part of the three-layer architecture:
- Layer 1: File Watcher
- Layer 2: Action Router (this module)
- Layer 3: Action Executor

Example Usage:
    >>> from monoco.core.router import ActionRouter, Action, ActionResult
    >>> from monoco.core.scheduler import AgentEventType
    >>> 
    >>> router = ActionRouter()
    >>> 
    >>> # Register action for issue creation
    >>> router.register(AgentEventType.ISSUE_CREATED, my_action)
    >>> 
    >>> # Register with condition
    >>> router.register(
    ...     AgentEventType.ISSUE_STAGE_CHANGED,
    ...     engineer_action,
    ...     condition=lambda e: e.payload.get("new_stage") == "doing"
    ... )
    >>> 
    >>> await router.start()
"""

from .action import (
    Action,
    ActionChain,
    ActionRegistry,
    ActionResult,
    ActionStatus,
    ConditionalAction,
)
from .router import (
    ActionRouter,
    ConditionalRouter,
    RoutingRule,
)

__all__ = [
    # Actions
    "Action",
    "ActionChain",
    "ActionRegistry",
    "ActionResult",
    "ActionStatus",
    "ConditionalAction",
    # Router
    "ActionRouter",
    "ConditionalRouter",
    "RoutingRule",
]
