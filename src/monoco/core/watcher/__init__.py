"""
Watcher Module - Layer 1 of the Event Automation Framework.

This module provides file system watching capabilities with event emission.
It is part of the three-layer architecture:
- Layer 1: File Watcher (this module)
- Layer 2: Action Router
- Layer 3: Action Executor

Example Usage:
    >>> from monoco.core.watcher import IssueWatcher, WatchConfig
    >>> from pathlib import Path
    >>>
    >>> config = WatchConfig(
    ...     path=Path("./Issues"),
    ...     patterns=["*.md"),
    ...     recursive=True,
    ... )
    >>> watcher = IssueWatcher(config)
    >>> await watcher.start()
    >>> # Events are automatically emitted to EventBus
    >>> await watcher.stop()
"""

from .base import (
    ChangeType,
    FieldChange,
    FileEvent,
    FilesystemWatcher,
    PollingWatcher,
    WatchdogWatcher,
    WatchConfig,
)
from .issue import IssueWatcher, IssueFileEvent
from .memo import MemoWatcher, MemoFileEvent
from .task import TaskWatcher, TaskFileEvent

__all__ = [
    # Base classes
    "ChangeType",
    "FieldChange",
    "FileEvent",
    "FilesystemWatcher",
    "PollingWatcher",
    "WatchdogWatcher",
    "WatchConfig",
    # Concrete watchers
    "IssueWatcher",
    "IssueFileEvent",
    "MemoWatcher",
    "MemoFileEvent",
    "TaskWatcher",
    "TaskFileEvent",
]
