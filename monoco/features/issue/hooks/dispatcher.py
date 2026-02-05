"""
Issue Hook Dispatcher

Core execution engine for Issue Lifecycle Hooks.
Responsible for:
- Loading built-in and user-defined hooks
- Executing hooks in priority order
- Aggregating results and making final decisions
- Providing debug information
"""

import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any, Union
from dataclasses import dataclass
from enum import Enum

from .models import (
    IssueEvent,
    IssueHookContext,
    IssueHookResult,
    HookDecision,
    HookMetadata,
    Diagnostic,
)

logger = logging.getLogger(__name__)


class HookExecutionError(Exception):
    """Exception raised when hook execution fails."""
    pass


@dataclass
class HookExecutionInfo:
    """Information about a single hook execution."""
    hook_name: str
    event: IssueEvent
    start_time: float
    end_time: Optional[float] = None
    result: Optional[IssueHookResult] = None
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time) * 1000
        return None
    
    @property
    def success(self) -> bool:
        return self.error is None and (self.result is None or self.result.decision != HookDecision.DENY)


class IssueHookDispatcher:
    """
    Central dispatcher for Issue Lifecycle Hooks.
    
    Loads and executes hooks for Issue lifecycle events, supporting:
    - Built-in hooks from monoco/hooks/issue/
    - User-defined hooks from .monoco/hooks/issue/
    - Synchronous execution with priority ordering
    - Decision aggregation (allow/warn/deny)
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the dispatcher.
        
        Args:
            project_root: Project root path for resolving user hooks
        """
        self.project_root = project_root
        self._builtins_dir = Path(__file__).parent / "builtin"
        self._user_hooks_dir: Optional[Path] = None
        if project_root:
            self._user_hooks_dir = project_root / ".monoco" / "hooks" / "issue"
        
        # Hook registries
        self._builtins: Dict[IssueEvent, List[HookMetadata]] = {e: [] for e in IssueEvent}
        self._user_hooks: Dict[IssueEvent, List[HookMetadata]] = {e: [] for e in IssueEvent}
        
        # Python callable hooks (for built-in hooks)
        self._callable_hooks: Dict[str, Callable[[IssueHookContext], IssueHookResult]] = {}
        
        # Execution history for debugging
        self._execution_history: List[HookExecutionInfo] = []
        
        # Load hooks
        self._load_builtins()
        self._load_user_hooks()
    
    def _load_builtins(self) -> None:
        """Load built-in hooks from monoco/hooks/issue/builtin/."""
        if not self._builtins_dir.exists():
            logger.debug(f"Built-in hooks directory not found: {self._builtins_dir}")
            return
        
        # Scan for Python modules and scripts
        for hook_file in self._builtins_dir.glob("*.py"):
            if hook_file.name.startswith("_"):
                continue
            try:
                self._register_builtin_from_file(hook_file)
            except Exception as e:
                logger.warning(f"Failed to load built-in hook {hook_file}: {e}")
    
    def _register_builtin_from_file(self, hook_file: Path) -> None:
        """Register a built-in hook from a Python file."""
        # For now, we'll use a simplified approach
        # In production, this would use importlib to load the module
        # and extract hook functions with proper metadata
        logger.debug(f"Registering built-in hook: {hook_file}")
    
    def _load_user_hooks(self) -> None:
        """Load user-defined hooks from .monoco/hooks/issue/."""
        if not self._user_hooks_dir or not self._user_hooks_dir.exists():
            logger.debug(f"User hooks directory not found: {self._user_hooks_dir}")
            return
        
        for hook_file in self._user_hooks_dir.rglob("*"):
            if hook_file.is_file() and not hook_file.name.startswith("_"):
                try:
                    self._register_user_hook_from_file(hook_file)
                except Exception as e:
                    logger.warning(f"Failed to load user hook {hook_file}: {e}")
    
    def _register_user_hook_from_file(self, hook_file: Path) -> None:
        """Register a user-defined hook from a file."""
        # Parse frontmatter or metadata from the file
        # This is a simplified implementation
        logger.debug(f"Registering user hook: {hook_file}")
    
    def register_callable(
        self,
        name: str,
        events: List[IssueEvent],
        fn: Callable[[IssueHookContext], IssueHookResult],
        priority: int = 100,
        enabled: bool = True,
    ) -> None:
        """
        Register a Python callable as a hook.
        
        Args:
            name: Unique hook name
            events: List of events this hook handles
            fn: Callable that receives context and returns result
            priority: Execution priority (lower = earlier)
            enabled: Whether the hook is enabled
        """
        self._callable_hooks[name] = fn
        metadata = HookMetadata(
            name=name,
            events=events,
            priority=priority,
            enabled=enabled,
            script_type="builtin",
        )
        
        for event in events:
            self._builtins[event].append(metadata)
            # Sort by priority
            self._builtins[event].sort(key=lambda m: m.priority)
    
    def get_hooks_for_event(self, event: IssueEvent) -> List[HookMetadata]:
        """
        Get all hooks registered for a specific event.
        
        Returns built-in hooks first (sorted by priority), then user hooks.
        """
        builtins = [h for h in self._builtins.get(event, []) if h.enabled]
        user_hooks = [h for h in self._user_hooks.get(event, []) if h.enabled]
        
        # Merge and sort by priority
        all_hooks = builtins + user_hooks
        all_hooks.sort(key=lambda m: m.priority)
        return all_hooks
    
    def execute(
        self,
        event: IssueEvent,
        context: IssueHookContext,
    ) -> IssueHookResult:
        """
        Execute all hooks for a given event.
        
        Args:
            event: The lifecycle event
            context: Execution context
            
        Returns:
            Aggregated result from all hook executions
        """
        if context.no_hooks:
            logger.debug(f"Hooks disabled for event {event}")
            return IssueHookResult.allow("Hooks skipped (no-hooks flag)")
        
        hooks = self.get_hooks_for_event(event)
        
        if not hooks:
            logger.debug(f"No hooks registered for event {event}")
            return IssueHookResult.allow()
        
        if context.debug_hooks:
            logger.info(f"Executing {len(hooks)} hooks for event {event}")
        
        # Execute hooks and collect results
        all_results: List[IssueHookResult] = []
        all_suggestions: List[str] = []
        all_diagnostics: List[Diagnostic] = []
        execution_infos: List[HookExecutionInfo] = []
        
        final_decision = HookDecision.ALLOW
        messages: List[str] = []
        
        for hook in hooks:
            info = HookExecutionInfo(
                hook_name=hook.name,
                event=event,
                start_time=time.time(),
            )
            
            try:
                result = self._execute_single_hook(hook, context)
                info.result = result
                info.end_time = time.time()
                
                # Collect results
                all_results.append(result)
                all_suggestions.extend(result.suggestions)
                all_diagnostics.extend(result.diagnostics)
                
                if result.message:
                    messages.append(f"[{hook.name}] {result.message}")
                
                # Update decision (DENY takes precedence)
                if result.decision == HookDecision.DENY:
                    final_decision = HookDecision.DENY
                    if context.debug_hooks:
                        logger.info(f"Hook {hook.name} denied execution")
                    # Continue executing other hooks for full feedback, but remember the deny
                elif result.decision == HookDecision.WARN and final_decision == HookDecision.ALLOW:
                    final_decision = HookDecision.WARN
                    
            except Exception as e:
                info.error = str(e)
                info.end_time = time.time()
                logger.error(f"Hook {hook.name} failed: {e}")
                
                # Hook failure defaults to DENY for safety
                if not context.force:
                    final_decision = HookDecision.DENY
                    messages.append(f"[{hook.name}] Execution failed: {e}")
                    all_suggestions.append(f"Check hook {hook.name} implementation or use --force to bypass")
            
            execution_infos.append(info)
            self._execution_history.append(info)
        
        # Construct final result
        final_message = "\n".join(messages) if messages else ""
        
        result = IssueHookResult(
            decision=final_decision,
            message=final_message,
            diagnostics=all_diagnostics,
            suggestions=list(set(all_suggestions)),  # Deduplicate
            context={
                "event": event.value,
                "hooks_executed": len(hooks),
                "execution_details": [
                    {
                        "name": i.hook_name,
                        "duration_ms": i.duration_ms,
                        "success": i.success,
                        "error": i.error,
                    }
                    for i in execution_infos
                ] if context.debug_hooks else None,
            },
        )
        
        return result
    
    def _execute_single_hook(
        self,
        hook: HookMetadata,
        context: IssueHookContext,
    ) -> IssueHookResult:
        """
        Execute a single hook.
        
        Args:
            hook: Hook metadata
            context: Execution context
            
        Returns:
            Hook execution result
        """
        # Check if it's a callable hook
        if hook.name in self._callable_hooks:
            start = time.time()
            result = self._callable_hooks[hook.name](context)
            duration = (time.time() - start) * 1000
            
            # Add execution info to result
            return result.model_copy(update={
                "execution_time_ms": duration,
                "hook_name": hook.name,
            })
        
        # Check if it's a Python script
        if hook.script_path and hook.script_path.suffix == ".py":
            return self._execute_python_script(hook, context)
        
        # Check if it's a shell script
        if hook.script_path and hook.script_path.suffix in (".sh", ".bash"):
            return self._execute_shell_script(hook, context)
        
        # Unknown hook type
        return IssueHookResult.deny(
            f"Unknown hook type for {hook.name}",
            suggestions=["Check hook script extension (.py or .sh)"]
        )
    
    def _execute_python_script(
        self,
        hook: HookMetadata,
        context: IssueHookContext,
    ) -> IssueHookResult:
        """Execute a Python script hook."""
        # TODO: Implement Python script execution
        # This would use importlib or subprocess to execute the script
        return IssueHookResult.allow("Python script execution not yet implemented")
    
    def _execute_shell_script(
        self,
        hook: HookMetadata,
        context: IssueHookContext,
    ) -> IssueHookResult:
        """Execute a shell script hook."""
        # TODO: Implement shell script execution
        # This would use subprocess to execute the script
        return IssueHookResult.allow("Shell script execution not yet implemented")
    
    def get_execution_history(self) -> List[HookExecutionInfo]:
        """Get the execution history for debugging."""
        return self._execution_history.copy()
    
    def clear_history(self) -> None:
        """Clear the execution history."""
        self._execution_history.clear()


# Global dispatcher instance (singleton pattern)
_dispatcher_instance: Optional[IssueHookDispatcher] = None


def get_dispatcher(project_root: Optional[Path] = None) -> IssueHookDispatcher:
    """
    Get the global IssueHookDispatcher instance.
    
    Args:
        project_root: Project root path (used only on first call)
        
    Returns:
        The global dispatcher instance
    """
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = IssueHookDispatcher(project_root)
    return _dispatcher_instance


def reset_dispatcher() -> None:
    """Reset the global dispatcher instance (mainly for testing)."""
    global _dispatcher_instance
    _dispatcher_instance = None
