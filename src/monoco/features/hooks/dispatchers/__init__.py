"""
Hook Dispatchers for Universal Hooks system.

Provides type-specific dispatchers for Git, IDE, and Agent hooks.
"""

from .git_dispatcher import GitHookDispatcher
from .agent_dispatcher import (
    AgentHookDispatcher,
    ClaudeCodeDispatcher,
    GeminiDispatcher,
    create_agent_dispatchers,
    get_dispatcher_for_provider,
)

__all__ = [
    "GitHookDispatcher",
    "AgentHookDispatcher",
    "ClaudeCodeDispatcher",
    "GeminiDispatcher",
    "create_agent_dispatchers",
    "get_dispatcher_for_provider",
]
