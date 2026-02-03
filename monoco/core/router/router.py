"""
ActionRouter - Layer 2 of the Event Automation Framework.

This module implements the ActionRouter which routes events to appropriate actions.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Set, Union

from monoco.core.scheduler import AgentEvent, AgentEventType, EventBus, event_bus

from .action import Action, ActionChain, ActionRegistry, ActionResult, ActionStatus

logger = logging.getLogger(__name__)


class RoutingRule:
    """
    A routing rule that maps events to actions.
    
    Attributes:
        event_types: Event types this rule matches
        action: Action to execute
        condition: Optional additional condition
        priority: Rule priority (higher = executed first)
    """
    
    def __init__(
        self,
        event_types: List[AgentEventType],
        action: Union[Action, ActionChain],
        condition: Optional[Callable[[AgentEvent], bool]] = None,
        priority: int = 0,
    ):
        self.event_types = event_types
        self.action = action
        self.condition = condition
        self.priority = priority
    
    def matches(self, event: AgentEvent) -> bool:
        """Check if this rule matches the event."""
        if event.type not in self.event_types:
            return False
        
        if self.condition is not None:
            if asyncio.iscoroutinefunction(self.condition):
                # Note: This is called from sync context, so we can't await
                # For async conditions, use Action.can_execute instead
                logger.warning("Async conditions in RoutingRule are not supported")
                return False
            return self.condition(event)
        
        return True


class ActionRouter:
    """
    Event router that maps events to actions (Layer 2).
    
    Responsibilities:
    - Subscribe to EventBus events
    - Route events to registered actions
    - Support conditional routing
    - Support action chains
    - Manage action lifecycle
    
    Example:
        >>> router = ActionRouter()
        >>> 
        >>> # Register simple action
        >>> router.register(AgentEventType.ISSUE_CREATED, my_action)
        >>> 
        >>> # Register with condition
        >>> router.register(
        ...     AgentEventType.ISSUE_STAGE_CHANGED,
        ...     engineer_action,
        ...     condition=lambda e: e.payload.get("new_stage") == "doing"
        ... )
        >>> 
        >>> await router.start()
    """
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        name: str = "ActionRouter",
    ):
        self.event_bus = event_bus or event_bus
        self.name = name
        self._rules: List[RoutingRule] = []
        self._registry = ActionRegistry()
        self._running = False
        self._event_handler: Optional[Callable[[AgentEvent], Any]] = None
        
        # Statistics
        self._event_count = 0
        self._routed_count = 0
        self._execution_results: List[ActionResult] = []
        self._max_results_history = 100
    
    def register(
        self,
        event_types: Union[AgentEventType, List[AgentEventType]],
        action: Union[Action, ActionChain],
        condition: Optional[Callable[[AgentEvent], bool]] = None,
        priority: int = 0,
    ) -> "ActionRouter":
        """
        Register an action for event types.
        
        Args:
            event_types: Event type(s) to subscribe to
            action: Action or ActionChain to execute
            condition: Optional condition function
            priority: Rule priority (higher = executed first)
            
        Returns:
            Self for chaining
        """
        if isinstance(event_types, AgentEventType):
            event_types = [event_types]
        
        rule = RoutingRule(
            event_types=event_types,
            action=action,
            condition=condition,
            priority=priority,
        )
        
        self._rules.append(rule)
        
        # Sort rules by priority (descending)
        self._rules.sort(key=lambda r: r.priority, reverse=True)
        
        # Register action in registry
        if isinstance(action, Action):
            self._registry.register(action)
        elif isinstance(action, ActionChain):
            for a in action.actions:
                self._registry.register(a)
        
        logger.info(
            f"Registered {action.name if hasattr(action, 'name') else type(action).__name__} "
            f"for events: {[t.value for t in event_types]}"
        )
        
        return self
    
    def unregister(self, action_name: str) -> bool:
        """
        Unregister an action by name.
        
        Args:
            action_name: Name of the action to unregister
            
        Returns:
            True if action was found and removed
        """
        # Remove from rules
        original_count = len(self._rules)
        self._rules = [
            r for r in self._rules
            if not (
                (hasattr(r.action, 'name') and r.action.name == action_name) or
                (isinstance(r.action, ActionChain) and action_name in [a.name for a in r.action.actions])
            )
        ]
        
        # Remove from registry
        self._registry.unregister(action_name)
        
        removed = len(self._rules) < original_count
        if removed:
            logger.info(f"Unregistered action: {action_name}")
        
        return removed
    
    async def start(self) -> None:
        """Start the router and subscribe to events."""
        if self._running:
            return
        
        self._running = True
        
        # Create event handler
        self._event_handler = self._handle_event
        
        # Subscribe to all event types mentioned in rules
        event_types = set()
        for rule in self._rules:
            event_types.update(rule.event_types)
        
        for event_type in event_types:
            self.event_bus.subscribe(event_type, self._event_handler)
        
        logger.info(f"Started ActionRouter with {len(self._rules)} rules")
    
    async def stop(self) -> None:
        """Stop the router and unsubscribe from events."""
        if not self._running:
            return
        
        self._running = False
        
        # Unsubscribe from all event types
        if self._event_handler:
            for event_type in AgentEventType:
                self.event_bus.unsubscribe(event_type, self._event_handler)
        
        logger.info("Stopped ActionRouter")
    
    async def _handle_event(self, event: AgentEvent) -> None:
        """
        Handle incoming events.
        
        Args:
            event: The event to route
        """
        self._event_count += 1
        
        logger.debug(f"Routing event: {event.type.value}")
        
        # Find matching rules
        matching_rules = [r for r in self._rules if r.matches(event)]
        
        if not matching_rules:
            logger.debug(f"No matching rules for event: {event.type.value}")
            return
        
        # Execute actions
        for rule in matching_rules:
            try:
                if isinstance(rule.action, ActionChain):
                    results = await rule.action.execute(event)
                    for result in results:
                        self._record_result(result)
                else:
                    result = await rule.action(event)
                    self._record_result(result)
                
                self._routed_count += 1
            
            except Exception as e:
                logger.error(f"Error executing action for {event.type.value}: {e}")
                self._record_result(ActionResult.failure_result(error=str(e)))
    
    def _record_result(self, result: ActionResult) -> None:
        """Record execution result."""
        self._execution_results.append(result)
        
        # Trim history
        if len(self._execution_results) > self._max_results_history:
            self._execution_results = self._execution_results[-self._max_results_history:]
    
    def route(self, event: AgentEvent) -> List[ActionResult]:
        """
        Manually route an event (synchronous version).
        
        Args:
            event: The event to route
            
        Returns:
            List of action results
        """
        results = []
        matching_rules = [r for r in self._rules if r.matches(event)]
        
        for rule in matching_rules:
            try:
                if isinstance(rule.action, ActionChain):
                    # For chains, we need to run async
                    loop = asyncio.get_event_loop()
                    chain_results = loop.run_until_complete(rule.action.execute(event))
                    results.extend(chain_results)
                else:
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(rule.action(event))
                    results.append(result)
            
            except Exception as e:
                logger.error(f"Error in manual route: {e}")
                results.append(ActionResult.failure_result(error=str(e)))
        
        return results
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all routing rules as dicts."""
        return [
            {
                "event_types": [t.value for t in r.event_types],
                "action": r.action.name if hasattr(r.action, 'name') else str(type(r.action)),
                "priority": r.priority,
                "has_condition": r.condition is not None,
            }
            for r in self._rules
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        success_count = sum(
            1 for r in self._execution_results
            if r.success and r.status == ActionStatus.SUCCESS
        )
        failed_count = sum(
            1 for r in self._execution_results
            if not r.success
        )
        skipped_count = sum(
            1 for r in self._execution_results
            if r.status == ActionStatus.SKIPPED
        )
        
        return {
            "name": self.name,
            "running": self._running,
            "rules": len(self._rules),
            "registered_actions": self._registry.list_actions(),
            "events_received": self._event_count,
            "events_routed": self._routed_count,
            "results": {
                "total": len(self._execution_results),
                "success": success_count,
                "failed": failed_count,
                "skipped": skipped_count,
            },
        }


class ConditionalRouter(ActionRouter):
    """
    Router with advanced conditional routing capabilities.
    
    Supports complex routing logic based on event payload.
    """
    
    def register_field_condition(
        self,
        event_types: Union[AgentEventType, List[AgentEventType]],
        action: Union[Action, ActionChain],
        field: str,
        expected_value: Any,
        priority: int = 0,
    ) -> "ConditionalRouter":
        """
        Register action with a field value condition.
        
        Args:
            event_types: Event type(s) to subscribe to
            action: Action to execute
            field: Payload field to check
            expected_value: Expected value of the field
            priority: Rule priority
            
        Returns:
            Self for chaining
        """
        def condition(event: AgentEvent) -> bool:
            return event.payload.get(field) == expected_value
        
        return self.register(event_types, action, condition, priority)
    
    def register_payload_condition(
        self,
        event_types: Union[AgentEventType, List[AgentEventType]],
        action: Union[Action, ActionChain],
        payload_matcher: Dict[str, Any],
        priority: int = 0,
    ) -> "ConditionalRouter":
        """
        Register action with a payload matching condition.
        
        Args:
            event_types: Event type(s) to subscribe to
            action: Action to execute
            payload_matcher: Dict of field -> expected value
            priority: Rule priority
            
        Returns:
            Self for chaining
        """
        def condition(event: AgentEvent) -> bool:
            return all(
                event.payload.get(k) == v
                for k, v in payload_matcher.items()
            )
        
        return self.register(event_types, action, condition, priority)
