"""
Executor Module - Layer 3 of the Event Automation Framework.

This module provides concrete Action implementations for various execution types.
It is part of the three-layer architecture:
- Layer 1: File Watcher
- Layer 2: Action Router
- Layer 3: Action Executor (this module)

Available Actions:
- SpawnAgentAction: Spawn agent sessions
- RunPytestAction: Execute pytest tests
- GitCommitAction: Perform git commits
- GitPushAction: Push to remote
- SendIMAction: Send notifications

Example Usage:
    >>> from monoco.core.executor import SpawnAgentAction
    >>> from monoco.core.scheduler import AgentEventType
    >>> from monoco.core.router import ActionRouter
    >>> 
    >>> action = SpawnAgentAction(role="Engineer")
    >>> router = ActionRouter()
    >>> router.register(AgentEventType.ISSUE_STAGE_CHANGED, action)
"""

from .agent_action import SpawnAgentAction
from .pytest_action import RunPytestAction
from .git_action import GitCommitAction, GitPushAction
from .im_action import SendIMAction

__all__ = [
    "SpawnAgentAction",
    "RunPytestAction",
    "GitCommitAction",
    "GitPushAction",
    "SendIMAction",
]
