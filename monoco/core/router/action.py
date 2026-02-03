"""
Action Abstractions - Layer 2 & 3 of the Event Automation Framework.

This module defines the Action ABC and related classes for the execution layer.
Actions are the units of work that respond to events.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from monoco.core.scheduler import AgentEvent, AgentEventType

logger = logging.getLogger(__name__)


class ActionStatus(Enum):
    """Status of an Action execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class ActionResult:
    """
    Result of an Action execution.
    
    Attributes:
        success: Whether the action succeeded
        status: Detailed status
        output: Output data from the action
        error: Error message if failed
        metadata: Additional metadata
        started_at: Execution start time
        completed_at: Execution completion time
    """
    success: bool
    status: ActionStatus
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @classmethod
    def success_result(
        cls,
        output: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ActionResult":
        """Create a success result."""
        return cls(
            success=True,
            status=ActionStatus.SUCCESS,
            output=output,
            metadata=metadata or {},
            completed_at=datetime.now(),
        )
    
    @classmethod
    def failure_result(
        cls,
        error: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ActionResult":
        """Create a failure result."""
        return cls(
            success=False,
            status=ActionStatus.FAILED,
            error=error,
            metadata=metadata or {},
            completed_at=datetime.now(),
        )
    
    @classmethod
    def skipped_result(
        cls,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ActionResult":
        """Create a skipped result."""
        return cls(
            success=True,
            status=ActionStatus.SKIPPED,
            metadata={"reason": reason, **(metadata or {})},
            completed_at=datetime.now(),
        )


class Action(ABC):
    """
    Abstract base class for Actions (Layer 3).
    
    Actions are the units of work that respond to events.
    They are executed by the ActionRouter when events match their conditions.
    
    Responsibilities:
    - Define execution conditions (can_execute)
    - Implement execution logic (execute)
    - Return execution results
    
    Example:
        >>> class MyAction(Action):
        ...     @property
        ...     def name(self) -> str:
        ...         return "MyAction"
        ...     
        ...     async def can_execute(self, event: AgentEvent) -> bool:
        ...         return event.type == AgentEventType.ISSUE_CREATED
        ...     
        ...     async def execute(self, event: AgentEvent) -> ActionResult:
        ...         # Do something
        ...         return ActionResult.success_result()
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._execution_count = 0
        self._last_execution: Optional[datetime] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this action."""
        pass
    
    @abstractmethod
    async def can_execute(self, event: AgentEvent) -> bool:
        """
        Check if this action should execute for the given event.
        
        Args:
            event: The event to check
            
        Returns:
            True if the action should execute, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute(self, event: AgentEvent) -> ActionResult:
        """
        Execute the action.
        
        Args:
            event: The event that triggered this action
            
        Returns:
            ActionResult indicating success/failure
        """
        pass
    
    async def __call__(self, event: AgentEvent) -> ActionResult:
        """
        Make action callable - checks conditions then executes.
        
        Args:
            event: The event to process
            
        Returns:
            ActionResult
        """
        self._last_execution = datetime.now()
        
        try:
            if not await self.can_execute(event):
                return ActionResult.skipped_result(
                    reason="Conditions not met",
                    metadata={"action": self.name, "event_type": event.type.value},
                )
            
            self._execution_count += 1
            result = await self.execute(event)
            
            # Ensure result has timestamps
            if result.started_at is None:
                result.started_at = self._last_execution
            
            return result
        
        except Exception as e:
            logger.error(f"Action {self.name} failed: {e}", exc_info=True)
            return ActionResult.failure_result(
                error=str(e),
                metadata={"action": self.name, "event_type": event.type.value},
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get action statistics."""
        return {
            "name": self.name,
            "execution_count": self._execution_count,
            "last_execution": self._last_execution.isoformat() if self._last_execution else None,
        }


class ConditionalAction(Action):
    """
    Action with configurable conditions.
    
    Allows defining conditions declaratively without subclassing.
    """
    
    def __init__(
        self,
        name: str,
        execute_fn: Callable[[AgentEvent], Any],
        condition_fn: Optional[Callable[[AgentEvent], bool]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self._name = name
        self._execute_fn = execute_fn
        self._condition_fn = condition_fn
    
    @property
    def name(self) -> str:
        return self._name
    
    async def can_execute(self, event: AgentEvent) -> bool:
        if self._condition_fn is None:
            return True
        
        if hasattr(self._condition_fn, '__await__'):
            return await self._condition_fn(event)
        return self._condition_fn(event)
    
    async def execute(self, event: AgentEvent) -> ActionResult:
        try:
            if hasattr(self._execute_fn, '__await__'):
                result = await self._execute_fn(event)
            else:
                result = self._execute_fn(event)
            
            if isinstance(result, ActionResult):
                return result
            return ActionResult.success_result(output=result)
        
        except Exception as e:
            return ActionResult.failure_result(error=str(e))


class ActionChain:
    """
    Chain of actions that execute sequentially.
    
    Each action in the chain receives the output of the previous action.
    If any action fails, the chain stops.
    """
    
    def __init__(self, name: str, actions: Optional[List[Action]] = None):
        self.name = name
        self.actions = actions or []
        self._results: List[ActionResult] = []
    
    def add(self, action: Action) -> "ActionChain":
        """Add an action to the chain."""
        self.actions.append(action)
        return self
    
    async def execute(self, event: AgentEvent) -> List[ActionResult]:
        """
        Execute all actions in the chain.
        
        Args:
            event: The triggering event
            
        Returns:
            List of ActionResults for each action
        """
        self._results = []
        context = {"event": event, "chain_name": self.name}
        
        for action in self.actions:
            # Check if previous action failed
            if self._results and not self._results[-1].success:
                self._results.append(ActionResult.skipped_result(
                    reason="Previous action in chain failed"
                ))
                continue
            
            # Execute action with context
            result = await action(event)
            result.metadata["chain_context"] = context.copy()
            self._results.append(result)
            
            # Update context with output
            if result.success and result.output is not None:
                context[f"{action.name}_output"] = result.output
        
        return self._results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chain statistics."""
        return {
            "name": self.name,
            "actions": len(self.actions),
            "action_names": [a.name for a in self.actions],
            "last_results": len(self._results),
        }


class ActionRegistry:
    """
    Registry for managing actions.
    
    Provides action lookup and management.
    """
    
    def __init__(self):
        self._actions: Dict[str, Action] = {}
    
    def register(self, action: Action) -> None:
        """Register an action."""
        self._actions[action.name] = action
        logger.debug(f"Registered action: {action.name}")
    
    def unregister(self, name: str) -> Optional[Action]:
        """Unregister an action."""
        return self._actions.pop(name, None)
    
    def get(self, name: str) -> Optional[Action]:
        """Get an action by name."""
        return self._actions.get(name)
    
    def list_actions(self) -> List[str]:
        """List all registered action names."""
        return list(self._actions.keys())
    
    def clear(self) -> None:
        """Clear all registered actions."""
        self._actions.clear()
