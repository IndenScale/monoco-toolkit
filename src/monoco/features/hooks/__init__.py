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
    AGENTHOOKS_EVENT_MAP,
    normalize_agent_event,
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
from .agenthooks_parser import (
    AgenthooksParser,
    AgenthooksConfig,
    AgenthooksMatcher,
    convert_agenthooks_to_parsed_hook,
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
    "AGENTHOOKS_EVENT_MAP",
    "normalize_agent_event",
    # Parser
    "HookParser",
    "ParseError",
    # Agenthooks Parser
    "AgenthooksParser",
    "AgenthooksConfig",
    "AgenthooksMatcher",
    "convert_agenthooks_to_parsed_hook",
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
