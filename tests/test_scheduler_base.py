"""
Unit tests for AgentScheduler base abstractions.
"""

import pytest
from datetime import datetime
from monoco.core.scheduler import (
    AgentStatus,
    AgentTask,
    AgentScheduler,
)


class TestAgentStatus:
    """Test suite for AgentStatus enum."""

    def test_status_values(self):
        """All expected statuses should be defined."""
        assert AgentStatus.PENDING.value == "pending"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.TERMINATED.value == "terminated"
        assert AgentStatus.TIMEOUT.value == "timeout"

    def test_status_comparison(self):
        """Status can be compared by value."""
        assert AgentStatus.PENDING == AgentStatus("pending")
        assert AgentStatus.RUNNING != AgentStatus.PENDING


class TestAgentTask:
    """Test suite for AgentTask dataclass."""

    def test_task_creation(self):
        """Task can be created with required fields."""
        task = AgentTask(
            task_id="test-123",
            role_name="Engineer",
            issue_id="FEAT-123",
            prompt="Implement feature X",
        )
        
        assert task.task_id == "test-123"
        assert task.role_name == "Engineer"
        assert task.issue_id == "FEAT-123"
        assert task.prompt == "Implement feature X"
        assert task.engine == "gemini"  # default
        assert task.timeout == 900  # default
        assert isinstance(task.metadata, dict)
        assert isinstance(task.created_at, datetime)

    def test_task_creation_with_all_fields(self):
        """Task can be created with all fields specified."""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        task = AgentTask(
            task_id="test-456",
            role_name="Architect",
            issue_id="FEAT-456",
            prompt="Design system Y",
            engine="claude",
            timeout=1200,
            metadata={"priority": "high"},
            created_at=created_at,
        )
        
        assert task.engine == "claude"
        assert task.timeout == 1200
        assert task.metadata == {"priority": "high"}
        assert task.created_at == created_at

    def test_task_default_timestamp(self):
        """Task gets current timestamp by default."""
        before = datetime.now()
        task = AgentTask(
            task_id="test-789",
            role_name="Reviewer",
            issue_id="FEAT-789",
            prompt="Review PR",
        )
        after = datetime.now()
        
        assert before <= task.created_at <= after


class TestAgentSchedulerInterface:
    """Test that AgentScheduler ABC defines the expected interface."""

    def test_abstract_methods(self):
        """AgentScheduler should define abstract methods."""
        # Cannot instantiate ABC directly
        with pytest.raises(TypeError):
            AgentScheduler()
        
        # Check abstract methods exist
        assert hasattr(AgentScheduler, "schedule")
        assert hasattr(AgentScheduler, "terminate")
        assert hasattr(AgentScheduler, "get_status")
        assert hasattr(AgentScheduler, "list_active")
        assert hasattr(AgentScheduler, "get_stats")

    def test_concrete_scheduler_must_implement(self):
        """Concrete schedulers must implement all abstract methods."""
        
        class IncompleteScheduler(AgentScheduler):
            pass
        
        with pytest.raises(TypeError):
            IncompleteScheduler()

    def test_complete_scheduler_can_instantiate(self):
        """Complete implementation can be instantiated."""
        
        class CompleteScheduler(AgentScheduler):
            async def schedule(self, task):
                return "session-123"
            
            async def terminate(self, session_id):
                return True
            
            def get_status(self, session_id):
                return AgentStatus.RUNNING
            
            def list_active(self):
                return {}
            
            def get_stats(self):
                return {}
        
        scheduler = CompleteScheduler()
        assert scheduler is not None
