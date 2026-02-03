"""
AgentScheduler - Core scheduling abstraction layer for Monoco.

This module provides the high-level AgentScheduler abstraction that decouples
scheduling policies from specific Agent Provider implementations.

Architecture:
    - AgentScheduler: Abstract base class for all schedulers
    - AgentTask: Data class representing a task to be scheduled
    - AgentStatus: Enum for task lifecycle states
    - EngineAdapter: Abstract base for agent engine adapters
    - EngineFactory: Factory for creating engine adapters
    - EventBus: Central event system for agent scheduling
    - AgentEventType: Event types for agent lifecycle

Implementations:
    - LocalProcessScheduler: Local process-based scheduler (default)
    - Future: DockerScheduler, RemoteScheduler, etc.
"""

from .base import (
    AgentStatus,
    AgentTask,
    AgentScheduler,
)
from .engines import (
    EngineAdapter,
    EngineFactory,
    GeminiAdapter,
    ClaudeAdapter,
    QwenAdapter,
    KimiAdapter,
)
from .events import (
    AgentEventType,
    AgentEvent,
    EventBus,
    EventHandler,
    event_bus,
)
from .local import LocalProcessScheduler

__all__ = [
    # Base abstractions
    "AgentStatus",
    "AgentTask",
    "AgentScheduler",
    # Engine adapters
    "EngineAdapter",
    "EngineFactory",
    "GeminiAdapter",
    "ClaudeAdapter",
    "QwenAdapter",
    "KimiAdapter",
    # Events
    "AgentEventType",
    "AgentEvent",
    "EventBus",
    "EventHandler",
    "event_bus",
    # Implementations
    "LocalProcessScheduler",
]
