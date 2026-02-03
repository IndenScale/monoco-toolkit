"""
Base abstractions for AgentScheduler.

Defines the core AgentScheduler ABC, AgentTask dataclass, and AgentStatus enum.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class AgentStatus(Enum):
    """
    Lifecycle states for an agent task.
    
    States:
        PENDING: Task is queued, waiting for resources
        RUNNING: Task is actively executing
        COMPLETED: Task finished successfully
        FAILED: Task failed with an error
        TERMINATED: Task was manually terminated
        TIMEOUT: Task exceeded its time limit
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    TIMEOUT = "timeout"


@dataclass
class AgentTask:
    """
    Data class representing a task to be scheduled.
    
    Attributes:
        task_id: Unique identifier for the task
        role_name: Name of the agent role (e.g., "Engineer", "Architect")
        issue_id: Associated issue ID
        prompt: The instruction/context to send to the agent
        engine: Agent engine to use (e.g., "gemini", "claude")
        timeout: Maximum execution time in seconds
        metadata: Additional task metadata
        created_at: Task creation timestamp
    """
    task_id: str
    role_name: str
    issue_id: str
    prompt: str
    engine: str = "gemini"
    timeout: int = 900
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Ensure created_at is set."""
        if self.created_at is None:
            self.created_at = datetime.now()


class AgentScheduler(ABC):
    """
    High-level scheduling abstraction that decouples scheduling policies
    from specific Agent Provider implementations.
    
    Responsibilities:
        - Task scheduling and lifecycle management
        - Resource quota control (concurrency limits)
        - Status monitoring and event publishing
    
    Implementations:
        - LocalProcessScheduler: Local process mode (current)
        - DockerScheduler: Container mode (future)
        - RemoteScheduler: Remote service mode (future)
    
    Example:
        >>> scheduler = LocalProcessScheduler(max_concurrent=5)
        >>> task = AgentTask(
        ...     task_id="uuid-123",
        ...     role_name="Engineer",
        ...     issue_id="FEAT-123",
        ...     prompt="Implement feature X",
        ...     engine="gemini"
        ... )
        >>> session_id = await scheduler.schedule(task)
        >>> status = scheduler.get_status(session_id)
    """
    
    @abstractmethod
    async def schedule(self, task: AgentTask) -> str:
        """
        Schedule a task for execution.
        
        Args:
            task: The task to schedule
            
        Returns:
            session_id: Unique identifier for the scheduled session
            
        Raises:
            RuntimeError: If scheduling fails
        """
        pass
    
    @abstractmethod
    async def terminate(self, session_id: str) -> bool:
        """
        Terminate a running or pending task.
        
        Args:
            session_id: The session ID to terminate
            
        Returns:
            True if termination was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_status(self, session_id: str) -> Optional[AgentStatus]:
        """
        Get the current status of a task.
        
        Args:
            session_id: The session ID to query
            
        Returns:
            The current AgentStatus, or None if session not found
        """
        pass
    
    @abstractmethod
    def list_active(self) -> Dict[str, AgentStatus]:
        """
        List all active (pending or running) tasks.
        
        Returns:
            Dictionary mapping session_id to AgentStatus
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scheduler statistics.
        
        Returns:
            Dictionary containing scheduler metrics
        """
        pass
