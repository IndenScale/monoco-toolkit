"""
Unit tests for ActionRouter.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from monoco.core.router import (
    ActionRouter,
    ConditionalRouter,
    RoutingRule,
    Action,
    ActionResult,
    ActionStatus,
)
from monoco.core.scheduler import AgentEvent, AgentEventType, EventBus


class TestRoutingRule:
    """Test suite for RoutingRule."""
    
    def test_rule_matches_event_type(self):
        """Rule matches based on event type."""
        
        class MockAction:
            name = "MockAction"
        
        rule = RoutingRule(
            event_types=[AgentEventType.ISSUE_CREATED],
            action=MockAction(),
        )
        
        event = AgentEvent(
            type=AgentEventType.ISSUE_CREATED,
            payload={},
        )
        
        assert rule.matches(event) is True
    
    def test_rule_does_not_match_wrong_type(self):
        """Rule doesn't match different event type."""
        
        class MockAction:
            name = "MockAction"
        
        rule = RoutingRule(
            event_types=[AgentEventType.ISSUE_CREATED],
            action=MockAction(),
        )
        
        event = AgentEvent(
            type=AgentEventType.MEMO_CREATED,
            payload={},
        )
        
        assert rule.matches(event) is False
    
    def test_rule_with_condition(self):
        """Rule matches based on condition."""
        
        class MockAction:
            name = "MockAction"
        
        def condition(event):
            return event.payload.get("stage") == "doing"
        
        rule = RoutingRule(
            event_types=[AgentEventType.ISSUE_STAGE_CHANGED],
            action=MockAction(),
            condition=condition,
        )
        
        # Event meeting condition
        event1 = AgentEvent(
            type=AgentEventType.ISSUE_STAGE_CHANGED,
            payload={"stage": "doing"},
        )
        assert rule.matches(event1) is True
        
        # Event not meeting condition
        event2 = AgentEvent(
            type=AgentEventType.ISSUE_STAGE_CHANGED,
            payload={"stage": "backlog"},
        )
        assert rule.matches(event2) is False


class TestActionRouter:
    """Test suite for ActionRouter."""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Create mock EventBus."""
        return AsyncMock(spec=EventBus)
    
    @pytest.fixture
    def sample_action(self):
        """Create sample action."""
        
        class SampleAction(Action):
            @property
            def name(self):
                return "SampleAction"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result(output="executed")
        
        return SampleAction()
    
    @pytest.mark.asyncio
    async def test_register_action(self, mock_event_bus, sample_action):
        """Action can be registered."""
        router = ActionRouter(event_bus=mock_event_bus)
        
        router.register(AgentEventType.ISSUE_CREATED, sample_action)
        
        assert len(router._rules) == 1
        assert router._rules[0].event_types == [AgentEventType.ISSUE_CREATED]
    
    @pytest.mark.asyncio
    async def test_register_multiple_event_types(self, mock_event_bus, sample_action):
        """Action can be registered for multiple event types."""
        router = ActionRouter(event_bus=mock_event_bus)
        
        router.register(
            [AgentEventType.ISSUE_CREATED, AgentEventType.ISSUE_UPDATED],
            sample_action,
        )
        
        assert len(router._rules) == 1
        assert AgentEventType.ISSUE_CREATED in router._rules[0].event_types
        assert AgentEventType.ISSUE_UPDATED in router._rules[0].event_types
    
    @pytest.mark.asyncio
    async def test_start_subscribes_to_events(self, mock_event_bus, sample_action):
        """Starting router subscribes to event types."""
        router = ActionRouter(event_bus=mock_event_bus)
        router.register(AgentEventType.ISSUE_CREATED, sample_action)
        
        await router.start()
        
        mock_event_bus.subscribe.assert_called_once()
        call_args = mock_event_bus.subscribe.call_args
        assert call_args[0][0] == AgentEventType.ISSUE_CREATED
    
    @pytest.mark.asyncio
    async def test_stop_unsubscribes_from_events(self, mock_event_bus, sample_action):
        """Stopping router unsubscribes from events."""
        router = ActionRouter(event_bus=mock_event_bus)
        router.register(AgentEventType.ISSUE_CREATED, sample_action)
        
        await router.start()
        await router.stop()
        
        # Router unsubscribes from all event types
        assert mock_event_bus.unsubscribe.call_count > 0
    
    @pytest.mark.asyncio
    async def test_handle_event_routes_to_action(self, mock_event_bus, sample_action):
        """Events are routed to matching actions."""
        router = ActionRouter(event_bus=mock_event_bus)
        router.register(AgentEventType.ISSUE_CREATED, sample_action)
        
        event = AgentEvent(
            type=AgentEventType.ISSUE_CREATED,
            payload={"issue_id": "FEAT-123"},
        )
        
        await router._handle_event(event)
        
        # Action should have been executed
        assert router._routed_count == 1
        assert len(router._execution_results) == 1
        assert router._execution_results[0].success is True
    
    @pytest.mark.asyncio
    async def test_handle_event_no_matching_rules(self, mock_event_bus, sample_action):
        """Events with no matching rules are ignored."""
        router = ActionRouter(event_bus=mock_event_bus)
        router.register(AgentEventType.ISSUE_CREATED, sample_action)
        
        event = AgentEvent(
            type=AgentEventType.MEMO_CREATED,
            payload={},
        )
        
        await router._handle_event(event)
        
        assert router._routed_count == 0
    
    @pytest.mark.asyncio
    async def test_unregister_action(self, mock_event_bus, sample_action):
        """Actions can be unregistered."""
        router = ActionRouter(event_bus=mock_event_bus)
        router.register(AgentEventType.ISSUE_CREATED, sample_action)
        
        removed = router.unregister("SampleAction")
        
        assert removed is True
        assert len(router._rules) == 0
    
    def test_get_rules(self, mock_event_bus, sample_action):
        """Router can list registered rules."""
        router = ActionRouter(event_bus=mock_event_bus)
        router.register(
            AgentEventType.ISSUE_CREATED,
            sample_action,
            condition=lambda e: True,
            priority=10,
        )
        
        rules = router.get_rules()
        
        assert len(rules) == 1
        assert rules[0]["event_types"] == [AgentEventType.ISSUE_CREATED.value]
        assert rules[0]["action"] == "SampleAction"
        assert rules[0]["priority"] == 10
        assert rules[0]["has_condition"] is True
    
    def test_get_stats(self, mock_event_bus, sample_action):
        """Router provides statistics."""
        router = ActionRouter(event_bus=mock_event_bus)
        router.register(AgentEventType.ISSUE_CREATED, sample_action)
        
        stats = router.get_stats()
        
        assert stats["name"] == "ActionRouter"
        assert stats["running"] is False
        assert stats["rules"] == 1
        assert "SampleAction" in stats["registered_actions"]
        assert stats["events_received"] == 0
        assert stats["events_routed"] == 0


class TestConditionalRouter:
    """Test suite for ConditionalRouter."""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Create mock EventBus."""
        return AsyncMock(spec=EventBus)
    
    @pytest.fixture
    def sample_action(self):
        """Create sample action."""
        
        class SampleAction(Action):
            @property
            def name(self):
                return "SampleAction"
            
            async def can_execute(self, event):
                return True
            
            async def execute(self, event):
                return ActionResult.success_result()
        
        return SampleAction()
    
    @pytest.mark.asyncio
    async def test_register_field_condition(self, mock_event_bus, sample_action):
        """Can register action with field condition."""
        router = ConditionalRouter(event_bus=mock_event_bus)
        
        router.register_field_condition(
            AgentEventType.ISSUE_STAGE_CHANGED,
            sample_action,
            field="new_stage",
            expected_value="doing",
        )
        
        # Event matching condition
        event1 = AgentEvent(
            type=AgentEventType.ISSUE_STAGE_CHANGED,
            payload={"new_stage": "doing"},
        )
        assert router._rules[0].matches(event1) is True
        
        # Event not matching condition
        event2 = AgentEvent(
            type=AgentEventType.ISSUE_STAGE_CHANGED,
            payload={"new_stage": "backlog"},
        )
        assert router._rules[0].matches(event2) is False
    
    @pytest.mark.asyncio
    async def test_register_payload_condition(self, mock_event_bus, sample_action):
        """Can register action with payload matching condition."""
        router = ConditionalRouter(event_bus=mock_event_bus)
        
        router.register_payload_condition(
            AgentEventType.ISSUE_STAGE_CHANGED,
            sample_action,
            payload_matcher={"new_stage": "doing", "issue_status": "open"},
        )
        
        # Event matching all conditions
        event1 = AgentEvent(
            type=AgentEventType.ISSUE_STAGE_CHANGED,
            payload={"new_stage": "doing", "issue_status": "open"},
        )
        assert router._rules[0].matches(event1) is True
        
        # Event matching only one condition
        event2 = AgentEvent(
            type=AgentEventType.ISSUE_STAGE_CHANGED,
            payload={"new_stage": "doing", "issue_status": "closed"},
        )
        assert router._rules[0].matches(event2) is False
