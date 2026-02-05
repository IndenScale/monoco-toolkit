"""
Router Module - Layer 2 of the Event Automation Framework.

This module provides Action ABC and ActionResult for handlers.
"""

from .action import (
    Action,
    ActionResult,
    ActionStatus,
)

__all__ = [
    "Action",
    "ActionResult",
    "ActionStatus",
]
