"""
Issue Hooks Integration Module

Provides helper functions for integrating Issue Lifecycle Hooks into CLI commands.
This module handles the boilerplate of:
- Building hook context from command parameters
- Executing pre/post hooks
- Handling hook results and user feedback
"""

import logging
from pathlib import Path
from typing import Optional, Callable, Any, Dict
from functools import wraps

import typer

from .models import IssueHookContext, IssueEvent, HookDecision, IssueHookResult
from .dispatcher import get_dispatcher
from monoco.core.output import OutputManager

logger = logging.getLogger(__name__)


def build_hook_context(
    event: IssueEvent,
    issue_id: Optional[str] = None,
    project_root: Optional[Path] = None,
    current_branch: Optional[str] = None,
    from_status: Optional[str] = None,
    to_status: Optional[str] = None,
    from_stage: Optional[str] = None,
    to_stage: Optional[str] = None,
    force: bool = False,
    no_hooks: bool = False,
    debug_hooks: bool = False,
    extra: Optional[Dict[str, Any]] = None,
) -> IssueHookContext:
    """
    Build an IssueHookContext from command parameters.
    
    Args:
        event: The lifecycle event
        issue_id: The target issue ID
        project_root: Project root path
        current_branch: Current git branch
        from_status: Source status
        to_status: Target status
        from_stage: Source stage
        to_stage: Target stage
        force: Force flag
        no_hooks: Skip hooks flag
        debug_hooks: Debug mode flag
        extra: Additional context
        
    Returns:
        Populated IssueHookContext
    """
    # Try to get current branch if not provided
    if not current_branch and project_root:
        try:
            from monoco.core import git
            current_branch = git.get_current_branch(project_root)
        except Exception:
            pass
    
    # Try to get default branch
    default_branch = "main"
    if project_root:
        try:
            from monoco.core import git
            # Simple heuristic - could be improved
            if git.branch_exists(project_root, "master"):
                default_branch = "master"
        except Exception:
            pass
    
    return IssueHookContext(
        event=event,
        trigger_source="cli",
        issue_id=issue_id,
        from_status=from_status,
        to_status=to_status,
        from_stage=from_stage,
        to_stage=to_stage,
        project_root=project_root,
        current_branch=current_branch,
        default_branch=default_branch,
        force=force,
        no_hooks=no_hooks,
        debug_hooks=debug_hooks,
        extra=extra or {},
    )


def execute_hooks(
    event: IssueEvent,
    context: IssueHookContext,
    project_root: Optional[Path] = None,
) -> IssueHookResult:
    """
    Execute hooks for a lifecycle event.
    
    Args:
        event: The lifecycle event
        context: Hook execution context
        project_root: Project root (for dispatcher lookup)
        
    Returns:
        Hook execution result
    """
    dispatcher = get_dispatcher(project_root)
    return dispatcher.execute(event, context)


def handle_hook_result(
    result: IssueHookResult,
    command_name: str = "Command",
    exit_on_deny: bool = True,
) -> bool:
    """
    Handle hook execution result and provide user feedback.
    
    Args:
        result: Hook execution result
        command_name: Name of the command (for error messages)
        exit_on_deny: Whether to exit on DENY decision
        
    Returns:
        True if execution should continue, False if blocked
    """
    # Debug output
    if result.context and result.context.get("execution_details"):
        details = result.context["execution_details"]
        for detail in details:
            if detail:
                logger.debug(
                    f"Hook {detail.get('name')}: "
                    f"{detail.get('duration_ms', 0):.1f}ms, "
                    f"success={detail.get('success')}"
                )
    
    if result.decision == HookDecision.ALLOW:
        return True
    
    if result.decision == HookDecision.WARN:
        # Show warning but continue
        if result.message:
            OutputManager.print({
                "warning": result.message,
                "suggestions": result.suggestions,
            })
        return True
    
    if result.decision == HookDecision.DENY:
        # Build error message
        lines = [f"{command_name} blocked by pre-hook validation:"]
        
        if result.message:
            lines.append(f"  {result.message}")
        
        if result.diagnostics:
            for diag in result.diagnostics:
                lines.append(f"  [{diag.severity}] {diag.message}")
        
        error_msg = "\n".join(lines)
        
        # Include suggestions in output
        if OutputManager.is_agent_mode():
            OutputManager.print({
                "error": error_msg,
                "suggestions": result.suggestions,
                "decision": "deny",
            })
        else:
            from rich.console import Console
            console = Console()
            console.print(f"[red]{error_msg}[/red]")
            
            if result.suggestions:
                console.print("\n[yellow]Suggestions:[/yellow]")
                for suggestion in result.suggestions:
                    console.print(f"  • {suggestion}")
        
        if exit_on_deny:
            raise typer.Exit(code=1)
        
        return False
    
    return True


def with_issue_hooks(
    command_name: str,
    pre_event: IssueEvent,
    post_event: IssueEvent,
):
    """
    Decorator to add lifecycle hooks to a command function.
    
    This decorator wraps a command function to:
    1. Execute pre-hooks before the command
    2. Execute post-hooks after successful command execution
    
    Args:
        command_name: Human-readable command name
        pre_event: Pre-execution event
        post_event: Post-execution event
        
    Example:
        @with_issue_hooks("Start", IssueEvent.PRE_START, IssueEvent.POST_START)
        def start(issue_id: str, ...):
            # Command implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract common parameters from kwargs
            issue_id = kwargs.get('issue_id') or (args[0] if args else None)
            project_root = kwargs.get('project_root')
            force = kwargs.get('force', False)
            no_hooks = kwargs.get('no_hooks', False)
            debug_hooks = kwargs.get('debug_hooks', False)
            
            # Build context for pre-hook
            pre_context = build_hook_context(
                event=pre_event,
                issue_id=issue_id,
                project_root=project_root,
                force=force,
                no_hooks=no_hooks,
                debug_hooks=debug_hooks,
            )
            
            # Execute pre-hooks
            pre_result = execute_hooks(pre_event, pre_context, project_root)
            if not handle_hook_result(pre_result, command_name):
                return None
            
            # Execute the command
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                # Command failed, don't run post-hooks
                raise
            
            # Build context for post-hook (include result info)
            post_context = build_hook_context(
                event=post_event,
                issue_id=issue_id,
                project_root=project_root,
                force=force,
                no_hooks=no_hooks,
                debug_hooks=debug_hooks,
                extra={"command_result": result},
            )
            
            # Execute post-hooks (errors here don't fail the command)
            try:
                post_result = execute_hooks(post_event, post_context, project_root)
                if debug_hooks and post_result.message:
                    OutputManager.print({
                        "post_hook_result": post_result.message,
                    })
            except Exception as e:
                logger.warning(f"Post-hook execution failed: {e}")
            
            return result
        
        return wrapper
    return decorator


def add_hook_options_to_command(command_func: Callable) -> Callable:
    """
    Add --no-hooks and --debug-hooks options to a command.
    
    This is a convenience function to add hook-related CLI options
    to existing commands.
    
    Args:
        command_func: The command function to modify
        
    Returns:
        Modified command function with hook options
    """
    # Note: In practice, these options need to be added to the typer command
    # definition. This function serves as documentation of the expected options.
    return command_func


class HookContextManager:
    """
    Context manager for executing hooks around a command.
    
    Usage:
        with HookContextManager("start", "FEAT-123", project_root) as ctx:
            # Pre-hooks executed here
            result = do_actual_work()
            # Post-hooks executed here
    """
    
    def __init__(
        self,
        command: str,
        issue_id: Optional[str],
        project_root: Optional[Path],
        force: bool = False,
        no_hooks: bool = False,
        debug_hooks: bool = False,
    ):
        self.command = command
        self.issue_id = issue_id
        self.project_root = project_root
        self.force = force
        self.no_hooks = no_hooks
        self.debug_hooks = debug_hooks
        
        from .models import get_events_for_command
        self.pre_event, self.post_event = get_events_for_command(command)
        self.pre_result: Optional[IssueHookResult] = None
        self.post_result: Optional[IssueHookResult] = None
    
    def __enter__(self):
        """Execute pre-hooks."""
        if self.pre_event and not self.no_hooks:
            context = build_hook_context(
                event=self.pre_event,
                issue_id=self.issue_id,
                project_root=self.project_root,
                force=self.force,
                no_hooks=self.no_hooks,
                debug_hooks=self.debug_hooks,
            )
            self.pre_result = execute_hooks(self.pre_event, context, self.project_root)
            handle_hook_result(self.pre_result, self.command)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Execute post-hooks if no exception occurred."""
        if self.post_event and not self.no_hooks and exc_type is None:
            try:
                context = build_hook_context(
                    event=self.post_event,
                    issue_id=self.issue_id,
                    project_root=self.project_root,
                    force=self.force,
                    no_hooks=self.no_hooks,
                    debug_hooks=self.debug_hooks,
                )
                self.post_result = execute_hooks(self.post_event, context, self.project_root)
            except Exception as e:
                logger.warning(f"Post-hook execution failed: {e}")
        return False  # Don't suppress exceptions
