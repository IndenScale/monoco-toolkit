"""
Hook Registry - Manages registration and execution of session lifecycle hooks.
"""

import logging
from typing import List, Type, Optional, Dict, Any
from pathlib import Path

from .base import SessionLifecycleHook, HookResult, HookStatus
from .context import HookContext

logger = logging.getLogger("monoco.core.hooks")


class HookRegistry:
    """
    Registry for managing session lifecycle hooks.
    
    Responsible for:
    - Registering hooks
    - Executing hooks in order
    - Handling hook errors gracefully
    - Loading hooks from configuration
    """

    def __init__(self):
        self._hooks: List[SessionLifecycleHook] = []
        self._hook_classes: Dict[str, Type[SessionLifecycleHook]] = {}

    def register(self, hook: SessionLifecycleHook) -> None:
        """
        Register a hook instance.
        
        Args:
            hook: The hook instance to register
        """
        if not isinstance(hook, SessionLifecycleHook):
            raise TypeError(f"Hook must be a SessionLifecycleHook, got {type(hook)}")
        
        self._hooks.append(hook)
        logger.debug(f"Registered hook: {hook.name}")

    def register_class(
        self, 
        hook_class: Type[SessionLifecycleHook], 
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a hook class (will be instantiated).
        
        Args:
            hook_class: The hook class to register
            name: Optional name for the hook instance
            config: Optional configuration for the hook
        """
        if not issubclass(hook_class, SessionLifecycleHook):
            raise TypeError(f"Hook class must inherit from SessionLifecycleHook")
        
        instance = hook_class(name=name, config=config)
        self.register(instance)

    def unregister(self, name: str) -> bool:
        """
        Unregister a hook by name.
        
        Args:
            name: The name of the hook to unregister
            
        Returns:
            True if a hook was removed, False otherwise
        """
        for i, hook in enumerate(self._hooks):
            if hook.name == name:
                self._hooks.pop(i)
                logger.debug(f"Unregistered hook: {name}")
                return True
        return False

    def get_hooks(self, enabled_only: bool = True) -> List[SessionLifecycleHook]:
        """
        Get all registered hooks.
        
        Args:
            enabled_only: If True, only return enabled hooks
            
        Returns:
            List of hook instances
        """
        if enabled_only:
            return [h for h in self._hooks if h.is_enabled()]
        return self._hooks.copy()

    def clear(self) -> None:
        """Clear all registered hooks."""
        self._hooks.clear()
        logger.debug("Cleared all hooks")

    def execute_on_session_start(self, context: HookContext) -> List[HookResult]:
        """
        Execute all registered hooks' on_session_start methods.
        
        Args:
            context: The hook context
            
        Returns:
            List of results from each hook
        """
        return self._execute_hooks("on_session_start", context)

    def execute_on_session_end(self, context: HookContext) -> List[HookResult]:
        """
        Execute all registered hooks' on_session_end methods.
        
        Args:
            context: The hook context
            
        Returns:
            List of results from each hook
        """
        return self._execute_hooks("on_session_end", context)

    def _execute_hooks(
        self, 
        method_name: str, 
        context: HookContext
    ) -> List[HookResult]:
        """
        Execute a hook method on all registered hooks.
        
        Errors in individual hooks don't stop execution of other hooks.
        
        Args:
            method_name: The name of the method to call
            context: The hook context
            
        Returns:
            List of results from each hook
        """
        results = []
        hooks = self.get_hooks(enabled_only=True)
        
        for hook in hooks:
            try:
                method = getattr(hook, method_name)
                result = method(context)
                results.append(result)
                
                if result.status == HookStatus.FAILURE:
                    logger.warning(
                        f"Hook '{hook.name}' {method_name} failed: {result.message}"
                    )
                elif result.status == HookStatus.WARNING:
                    logger.warning(
                        f"Hook '{hook.name}' {method_name} warning: {result.message}"
                    )
                else:
                    logger.debug(
                        f"Hook '{hook.name}' {method_name} succeeded: {result.message}"
                    )
                    
            except Exception as e:
                logger.error(f"Hook '{hook.name}' {method_name} raised exception: {e}")
                results.append(HookResult.failure(str(e)))
        
        return results

    def load_from_config(self, config: Dict[str, Any], project_root: Path) -> None:
        """
        Load and register hooks from configuration.
        
        Args:
            config: The hooks configuration dictionary
            project_root: The project root path
        """
        if not config:
            return
        
        # Import built-in hooks
        from .builtin.git_cleanup import GitCleanupHook
        from .builtin.logging_hook import LoggingHook
        
        # Map of hook names to classes
        builtin_hooks = {
            "git_cleanup": GitCleanupHook,
            "logging": LoggingHook,
        }
        
        for hook_name, hook_config in config.items():
            if isinstance(hook_config, bool):
                # Simple enable/disable: "git_cleanup: true"
                if hook_config and hook_name in builtin_hooks:
                    self.register_class(builtin_hooks[hook_name], name=hook_name)
            elif isinstance(hook_config, dict):
                # Full configuration: "git_cleanup: { enabled: true, ... }"
                enabled = hook_config.get("enabled", True)
                if enabled and hook_name in builtin_hooks:
                    self.register_class(
                        builtin_hooks[hook_name], 
                        name=hook_name, 
                        config=hook_config
                    )
            else:
                logger.warning(f"Unknown hook config format for '{hook_name}'")


# Global registry instance
_global_registry: Optional[HookRegistry] = None


def get_registry() -> HookRegistry:
    """Get the global hook registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = HookRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _global_registry
    _global_registry = HookRegistry()
