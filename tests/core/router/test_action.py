"""
Unit tests for Action classes.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from monoco.core.router import (
    Action,
    ActionChain,
    ActionRegistry,
    ActionResult,
    ActionStatus,
    ConditionalAction,
)
from monoco.core.scheduler import AgentEvent, AgentEventType


class TestActionStatus:
    """Test suite for ActionStatus enum."""
    
    def test_status_values(self):
        """All expected statuses should be defined."""
        assert ActionStatus.PENDING.value == "pending"
        assert ActionStatus.RUNNING.value == "running"
        assert ActionStatus.SUCCESS.value == "success"
        assert ActionStatus.FAILED.value == "failed"
        assert ActionStatus.SKIPPED.value == "skipped"
        assert ActionStatus.CANCELLED.value == "cancelled"


class TestActionResult:
    """Test suite for ActionResult dataclass."""
    
    def test_success_result(self):
        """Can create success result."""
        result = ActionResult.success_result(
            output={"key": "value"},
            metadata={"meta": "data"},
        )
        
        assert result.success is True
        assert result.status == ActionStatus.SUCCESS
        assert result.output == {"key": "value"}
        assert result.completed_at is not None
    
    def test_failure_result(self):
        """Can create failure result."""
        result = ActionResult.failure_result(
            error="Something went wrong",
            metadata={"context": "info"},
        )
        
        assert result.success is False
        assert result.status == ActionStatus.FAILED
        assert result.error == "Something went wrong"
    
    def test_skipped_result(self):
        """Can create skipped result."""
        result = ActionResult.skipped_result(reason="Conditions not met")
        
        assert result.success is True
        assert result.status == ActionStatus.SKIPPED
        assert result.metadata["reason"] == "Conditions not met"


class TestAction:
    """Test suite for Action ABC."""
    
    def test_cannot_instantiate_abc(self):
        """Cannot instantiate abstract base class."""
        with pytest.raises(TypeError):
            Action()
    
    @pytest.mark.asyncio
    async def test_action_call_success(self):
        """Action call returns success result."""
        
        class TestAction(Action):
            @property
            def name(self):
                return "TestAction"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result(output="test")
        
        action = TestAction()
        event = AgentEvent(
            type=AgentEventType.ISSUE_CREATED,
            payload={"issue_id": "FEAT-123"},
        )
        
        result = await action(event)
        
        assert result.success is True
        assert result.status == ActionStatus.SUCCESS
        assert result.output == "test"
    
    @pytest.mark.asyncio
    async def test_action_call_skipped(self):
        """Action call returns skipped when can_execute is False."""
        
        class TestAction(Action):
            @property
            def name(self):
                return "TestAction"
            
            async def can_execute(self, event):
                return False
            
            async def execute(self, event):
                return ActionResult.success_result()
        
        action = TestAction()
        event = AgentEvent(
            type=AgentEventType.ISSUE_CREATED,
            payload={},
        )
        
        result = await action(event)
        
        assert result.success is True
        assert result.status == ActionStatus.SKIPPED
    
    @pytest.mark.asyncio
    async def test_action_call_exception(self):
        """Action call handles exceptions gracefully."""
        
        class TestAction(Action):
            @property
            def name(self):
                return "TestAction"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                raise ValueError("Test error")
        
        action = TestAction()
        event = AgentEvent(
            type=AgentEventType.ISSUE_CREATED,
            payload={},
        )
        
        result = await action(event)
        
        assert result.success is False
        assert result.status == ActionStatus.FAILED
        assert "Test error" in result.error
    
    def test_action_stats(self):
        """Action tracks execution statistics."""
        
        class TestAction(Action):
            @property
            def name(self):
                return "TestAction"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result()
        
        action = TestAction()
        
        stats = action.get_stats()
        
        assert stats["name"] == "TestAction"
        assert stats["execution_count"] == 0
        assert stats["last_execution"] is None


class TestConditionalAction:
    """Test suite for ConditionalAction."""
    
    @pytest.mark.asyncio
    async def test_conditional_action_with_condition(self):
        """ConditionalAction respects condition function."""
        
        def condition(event):
            return event.payload.get("should_run") is True
        
        def execute_fn(event):
            return {"executed": True}
        
        action = ConditionalAction(
            name="ConditionalTest",
            execute_fn=execute_fn,
            condition_fn=condition,
        )
        
        # Event that meets condition
        event1 = AgentEvent(
            type=AgentEventType.ISSUE_CREATED,
            payload={"should_run": True},
        )
        result1 = await action(event1)
        assert result1.success is True
        assert result1.output == {"executed": True}
        
        # Event that doesn't meet condition
        event2 = AgentEvent(
            type=AgentEventType.ISSUE_CREATED,
            payload={"should_run": False},
        )
        result2 = await action(event2)
        assert result2.status == ActionStatus.SKIPPED
    
    @pytest.mark.asyncio
    async def test_conditional_action_without_condition(self):
        """ConditionalAction without condition always executes."""
        
        def execute_fn(event):
            return {"executed": True}
        
        action = ConditionalAction(
            name="AlwaysRun",
            execute_fn=execute_fn,
        )
        
        event = AgentEvent(
            type=AgentEventType.ISSUE_CREATED,
            payload={},
        )
        result = await action(event)
        
        assert result.success is True
        assert result.output == {"executed": True}


class TestActionChain:
    """Test suite for ActionChain."""
    
    @pytest.mark.asyncio
    async def test_chain_execution(self):
        """ActionChain executes actions sequentially."""
        
        class TestAction(Action):
            def __init__(self, name, return_value):
                super().__init__()
                self._name = name
                self.return_value = return_value
            
            @property
            def name(self):
                return self._name
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result(output=self.return_value)
        
        action1 = TestAction("Action1", "result1")
        action2 = TestAction("Action2", "result2")
        
        chain = ActionChain("TestChain", [action1, action2])
        
        event = AgentEvent(
            type=AgentEventType.ISSUE_CREATED,
            payload={},
        )
        
        results = await chain.execute(event)
        
        assert len(results) == 2
        assert results[0].output == "result1"
        assert results[1].output == "result2"
    
    @pytest.mark.asyncio
    async def test_chain_stops_on_failure(self):
        """ActionChain stops when an action fails."""
        
        class SuccessAction(Action):
            @property
            def name(self):
                return "Success"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result()
        
        class FailAction(Action):
            @property
            def name(self):
                return "Fail"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.failure_result(error="Failed")
        
        action1 = SuccessAction()
        action2 = FailAction()
        action3 = SuccessAction()
        
        chain = ActionChain("TestChain", [action1, action2, action3])
        
        event = AgentEvent(
            type=AgentEventType.ISSUE_CREATED,
            payload={},
        )
        
        results = await chain.execute(event)
        
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].status == ActionStatus.SKIPPED  # Third action skipped
    
    def test_chain_add(self):
        """Actions can be added to chain."""
        
        class TestAction(Action):
            @property
            def name(self):
                return "Test"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result()
        
        chain = ActionChain("TestChain")
        action = TestAction()
        
        chain.add(action)
        
        assert len(chain.actions) == 1


class TestActionRegistry:
    """Test suite for ActionRegistry."""
    
    def test_register_and_get(self):
        """Actions can be registered and retrieved."""
        registry = ActionRegistry()
        
        class TestAction(Action):
            @property
            def name(self):
                return "TestAction"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result()
        
        action = TestAction()
        registry.register(action)
        
        retrieved = registry.get("TestAction")
        assert retrieved is action
    
    def test_unregister(self):
        """Actions can be unregistered."""
        registry = ActionRegistry()
        
        class TestAction(Action):
            @property
            def name(self):
                return "TestAction"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result()
        
        action = TestAction()
        registry.register(action)
        
        removed = registry.unregister("TestAction")
        assert removed is action
        assert registry.get("TestAction") is None
    
    def test_list_actions(self):
        """Registry can list registered actions."""
        registry = ActionRegistry()
        
        class TestAction1(Action):
            @property
            def name(self):
                return "Action1"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result()
        
        class TestAction2(Action):
            @property
            def name(self):
                return "Action2"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result()
        
        registry.register(TestAction1())
        registry.register(TestAction2())
        
        actions = registry.list_actions()
        
        assert "Action1" in actions
        assert "Action2" in actions
