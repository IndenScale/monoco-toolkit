"""
Monoco Native Hook System

Provides lifecycle hooks for Agent Sessions, independent of specific CLI tools.
"""

from .base import SessionLifecycleHook, HookResult, HookStatus
from .context import HookContext
from .registry import HookRegistry, get_registry, reset_registry

__all__ = [
    "SessionLifecycleHook",
    "HookResult",
    "HookStatus",
    "HookContext",
    "HookRegistry",
    "get_registry",
    "reset_registry",
]
