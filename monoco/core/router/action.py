"""
Action Abstractions - Layer 2 & 3 of the Event Automation Framework.

This module defines the Action ABC and ActionResult for handler return types.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

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
    They are executed by handlers when events match their conditions.
    
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
