"""
Agent Engine Adapters for Monoco Scheduler.

DEPRECATED: This module has been moved to monoco.core.scheduler.
This file is kept for backward compatibility and re-exports from the new location.

Migration:
    Old: from monoco.features.agent.engines import EngineAdapter, EngineFactory
    New: from monoco.core.scheduler import EngineAdapter, EngineFactory
"""

import warnings
from monoco.core.scheduler import (
    EngineAdapter,
    EngineFactory,
    GeminiAdapter,
    ClaudeAdapter,
    QwenAdapter,
    KimiAdapter,
)

warnings.warn(
    "monoco.features.agent.engines is deprecated. "
    "Use monoco.core.scheduler instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "EngineAdapter",
    "EngineFactory",
    "GeminiAdapter",
    "ClaudeAdapter",
    "QwenAdapter",
    "KimiAdapter",
]
