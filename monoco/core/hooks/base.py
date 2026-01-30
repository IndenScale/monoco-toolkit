"""
Base classes for Session Lifecycle Hooks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from .context import HookContext


class HookStatus(str, Enum):
    """Status of hook execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"
    WARNING = "warning"


@dataclass
class HookResult:
    """Result of a hook execution."""
    status: HookStatus
    message: str = ""
    details: Optional[dict] = None

    @classmethod
    def success(cls, message: str = "", details: Optional[dict] = None) -> "HookResult":
        return cls(status=HookStatus.SUCCESS, message=message, details=details)

    @classmethod
    def failure(cls, message: str = "", details: Optional[dict] = None) -> "HookResult":
        return cls(status=HookStatus.FAILURE, message=message, details=details)

    @classmethod
    def skipped(cls, message: str = "", details: Optional[dict] = None) -> "HookResult":
        return cls(status=HookStatus.SKIPPED, message=message, details=details)

    @classmethod
    def warning(cls, message: str = "", details: Optional[dict] = None) -> "HookResult":
        return cls(status=HookStatus.WARNING, message=message, details=details)


class SessionLifecycleHook(ABC):
    """
    Abstract base class for session lifecycle hooks.
    
    Hooks can be registered to execute at specific points in a session's lifecycle:
    - on_session_start: Called when a session starts
    - on_session_end: Called when a session ends (terminate)
    
    Example:
        class MyHook(SessionLifecycleHook):
            def on_session_start(self, context: HookContext) -> HookResult:
                print(f"Session {context.session_id} started")
                return HookResult.success()
            
            def on_session_end(self, context: HookContext) -> HookResult:
                print(f"Session {context.session_id} ended")
                return HookResult.success()
    """

    def __init__(self, name: Optional[str] = None, config: Optional[dict] = None):
        """
        Initialize the hook.
        
        Args:
            name: Optional name for the hook. If not provided, uses class name.
            config: Optional configuration dictionary for the hook.
        """
        self.name = name or self.__class__.__name__
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

    @abstractmethod
    def on_session_start(self, context: HookContext) -> HookResult:
        """
        Called when a session starts.
        
        Args:
            context: The hook context containing session information.
            
        Returns:
            HookResult indicating the outcome of the hook execution.
        """
        pass

    @abstractmethod
    def on_session_end(self, context: HookContext) -> HookResult:
        """
        Called when a session ends.
        
        Args:
            context: The hook context containing session information.
            
        Returns:
            HookResult indicating the outcome of the hook execution.
        """
        pass

    def is_enabled(self) -> bool:
        """Check if this hook is enabled."""
        return self.enabled
