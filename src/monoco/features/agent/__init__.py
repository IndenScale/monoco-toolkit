"""
Agent feature module - CLI interface for agent operations.

Note: The old SessionManager/RuntimeSession/ApoptosisManager architecture
has been removed in FEAT-0164. This module now provides CLI commands that
use the new AgentScheduler abstraction from core.scheduler.
"""

from .models import RoleTemplate, AgentRoleConfig as AgentConfig, SchedulerConfig
from .worker import Worker
from .config import load_scheduler_config, load_agent_config
from .defaults import DEFAULT_ROLES

# Re-export engines from core.scheduler for backward compatibility
from monoco.core.scheduler import (
    EngineAdapter,
    EngineFactory,
    GeminiAdapter,
    ClaudeAdapter,
    QwenAdapter,
    KimiAdapter,
)

__all__ = [
    "RoleTemplate",
    "AgentConfig",
    "SchedulerConfig",
    "load_agent_config",
    "Worker",
    "load_scheduler_config",
    "DEFAULT_ROLES",
    # Re-exported from core.scheduler
    "EngineAdapter",
    "EngineFactory",
    "GeminiAdapter",
    "ClaudeAdapter",
    "QwenAdapter",
    "KimiAdapter",
]
