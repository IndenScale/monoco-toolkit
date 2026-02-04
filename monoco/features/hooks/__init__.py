"""
Universal Hooks management feature for Monoco.

Provides a unified hooks system for Git, IDE, and Agent integration
with Front Matter metadata support.
"""

from .models import (
    HookType,
    HookMetadata,
    GitEvent,
    AgentEvent,
    IDEEvent,
    ParsedHook,
    HookGroup,
)
from .parser import HookParser, ParseError
from .manager import UniversalHookManager, ValidationResult, HookDispatcher

__all__ = [
    # Models
    "HookType",
    "HookMetadata",
    "GitEvent",
    "AgentEvent",
    "IDEEvent",
    "ParsedHook",
    "HookGroup",
    # Parser
    "HookParser",
    "ParseError",
    # Manager
    "UniversalHookManager",
    "ValidationResult",
    "HookDispatcher",
]
