"""
Issue Lifecycle Hooks System

Provides lifecycle hooks for Monoco Issue commands, following ADR-001.

Usage:
    from monoco.features.issue.hooks import get_dispatcher, IssueEvent
    
    dispatcher = get_dispatcher(project_root)
    result = dispatcher.execute(
        event=IssueEvent.PRE_SUBMIT,
        context=IssueHookContext(
            issue_id="FEAT-0123",
            event=IssueEvent.PRE_SUBMIT,
            ...
        )
    )
    
    if result.decision == HookDecision.DENY:
        print(f"Blocked: {result.message}")
        for suggestion in result.suggestions:
            print(f"  Suggestion: {suggestion}")
"""

from .models import (
    IssueEvent,
    AgnosticAgentEvent,
    HookDecision,
    Diagnostic,
    IssueHookResult,
    IssueHookContext,
    HookMetadata,
    NamingACL,
    COMMAND_EVENT_MAP,
    get_events_for_command,
)

from .dispatcher import (
    IssueHookDispatcher,
    HookExecutionInfo,
    get_dispatcher,
    reset_dispatcher,
)

from .builtin import register_all_builtins
from .agent_adapter import (
    AgentToolAdapter,
    ParsedIssueCommand,
    create_adapter,
)
from .integration import (
    build_hook_context,
    execute_hooks,
    handle_hook_result,
    with_issue_hooks,
    HookContextManager,
)

__all__ = [
    # Models
    "IssueEvent",
    "AgnosticAgentEvent",
    "HookDecision",
    "Diagnostic",
    "IssueHookResult",
    "IssueHookContext",
    "HookMetadata",
    "NamingACL",
    "COMMAND_EVENT_MAP",
    "get_events_for_command",
    # Dispatcher
    "IssueHookDispatcher",
    "HookExecutionInfo",
    "get_dispatcher",
    "reset_dispatcher",
    # Built-in hooks
    "register_all_builtins",
    # Agent adapter
    "AgentToolAdapter",
    "ParsedIssueCommand",
    "create_adapter",
    # Integration helpers
    "build_hook_context",
    "execute_hooks",
    "handle_hook_result",
    "with_issue_hooks",
    "HookContextManager",
]


def init_hooks(project_root) -> IssueHookDispatcher:
    """
    Initialize the Issue Hooks system.
    
    This is the main entry point for setting up the hooks system.
    It creates the dispatcher and registers all built-in hooks.
    
    Args:
        project_root: The project root path
        
    Returns:
        Configured IssueHookDispatcher instance
    """
    dispatcher = get_dispatcher(project_root)
    register_all_builtins(dispatcher)
    return dispatcher
