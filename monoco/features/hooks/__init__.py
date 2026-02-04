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
from .dispatchers import (
    GitHookDispatcher,
    AgentHookDispatcher,
    ClaudeCodeDispatcher,
    GeminiDispatcher,
    create_agent_dispatchers,
    get_dispatcher_for_provider,
)
from .universal_interceptor import (
    UniversalInterceptor,
    AgentAdapter,
    ClaudeAdapter,
    GeminiAdapter,
    UnifiedDecision,
    UnifiedHookInput,
)

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
    # Dispatchers
    "GitHookDispatcher",
    "AgentHookDispatcher",
    "ClaudeCodeDispatcher",
    "GeminiDispatcher",
    "create_agent_dispatchers",
    "get_dispatcher_for_provider",
    # Universal Interceptor (ACL)
    "UniversalInterceptor",
    "AgentAdapter",
    "ClaudeAdapter",
    "GeminiAdapter",
    "UnifiedDecision",
    "UnifiedHookInput",
]
