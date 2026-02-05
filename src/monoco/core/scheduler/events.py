"""
EventBus - Central event system for Agent scheduling (FEAT-0155).

Provides async event publishing/subscription mechanism for decoupled
Agent lifecycle management.
"""

import asyncio
import inspect
import logging
from enum import Enum, auto
from typing import Dict, List, Callable, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime


def _is_async_handler(handler: Callable) -> bool:
    """
    Check if a handler is async (coroutine function or has async __call__).
    
    Handles both:
    - Regular async functions: async def func(): ...
    - Callable objects with async __call__: class Handler: async def __call__(self, ...): ...
    """
    # Direct check for coroutine function
    if inspect.iscoroutinefunction(handler):
        return True
    # Check for callable object with async __call__ method
    if hasattr(handler, "__call__") and inspect.iscoroutinefunction(handler.__call__):
        return True
    return False

logger = logging.getLogger("monoco.core.scheduler.events")


class AgentEventType(Enum):
    """Event types for Agent lifecycle and triggers."""
    # Memo events
    MEMO_CREATED = "memo.created"
    MEMO_THRESHOLD = "memo.threshold"
    
    # Issue events
    ISSUE_CREATED = "issue.created"
    ISSUE_UPDATED = "issue.updated"
    ISSUE_STAGE_CHANGED = "issue.stage_changed"
    ISSUE_STATUS_CHANGED = "issue.status_changed"
    
    # Session events
    SESSION_STARTED = "session.started"
    SESSION_COMPLETED = "session.completed"
    SESSION_FAILED = "session.failed"
    SESSION_CRASHED = "session.crashed"
    SESSION_TERMINATED = "session.terminated"
    
    # PR events (for Reviewer trigger)
    PR_CREATED = "pr.created"
    PR_UPDATED = "pr.updated"
    
    # IM events (FEAT-0167)
    IM_MESSAGE_RECEIVED = "im.message.received"
    IM_MESSAGE_REPLIED = "im.message.replied"
    IM_AGENT_TRIGGER = "im.agent.trigger"
    IM_SESSION_STARTED = "im.session.started"
    IM_SESSION_CLOSED = "im.session.closed"
    IM_CHANNEL_CREATED = "im.channel.created"
    IM_CHANNEL_UPDATED = "im.channel.updated"


@dataclass
class AgentEvent:
    """Event data structure."""
    type: AgentEventType
    payload: Dict[str, Any]
    timestamp: datetime = None
    source: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


EventHandler = Callable[[AgentEvent], Any]


class EventBus:
    """
    Central async event bus for Agent scheduling.
    
    Supports:
    - Subscribe/unsubscribe handlers for specific event types
    - Publish events to all subscribed handlers
    - Async handler execution
    """
    
    def __init__(self):
        self._handlers: Dict[AgentEventType, List[EventHandler]] = {
            event_type: [] for event_type in AgentEventType
        }
        self._lock = asyncio.Lock()
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._dispatch_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the event dispatch loop."""
        if self._running:
            return
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())
        logger.info("EventBus started")
    
    async def stop(self):
        """Stop the event dispatch loop."""
        if not self._running:
            return
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
        logger.info("EventBus stopped")
    
    async def _dispatch_loop(self):
        """Background loop to dispatch events."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._dispatch_event(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error dispatching event: {e}")
    
    async def _dispatch_event(self, event: AgentEvent):
        """Dispatch event to all subscribed handlers."""
        handlers = self._handlers.get(event.type, [])
        if not handlers:
            logger.debug(f"No handlers for event {event.type.value}")
            return
        
        logger.debug(f"Dispatching {event.type.value} to {len(handlers)} handlers")
        
        # Execute handlers concurrently
        tasks = []
        for handler in handlers:
            try:
                if _is_async_handler(handler):
                    tasks.append(asyncio.create_task(handler(event)))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event.type.value}: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(self, event_type: AgentEventType, handler: EventHandler):
        """Subscribe a handler to an event type."""
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"Handler subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: AgentEventType, handler: EventHandler):
        """Unsubscribe a handler from an event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Handler unsubscribed from {event_type.value}")
    
    async def publish(self, event_type: AgentEventType, payload: Dict[str, Any], source: str = None):
        """Publish an event to the bus."""
        event = AgentEvent(type=event_type, payload=payload, source=source)
        await self._event_queue.put(event)
        logger.debug(f"Published event {event_type.value}")
    
    def get_subscriber_count(self, event_type: AgentEventType) -> int:
        """Get number of subscribers for an event type."""
        return len(self._handlers.get(event_type, []))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            "running": self._running,
            "queue_size": self._event_queue.qsize(),
            "subscribers": {
                event_type.value: len(handlers)
                for event_type, handlers in self._handlers.items()
                if handlers
            }
        }


# Global event bus instance
event_bus = EventBus()
