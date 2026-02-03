"""
Base abstractions for FilesystemWatcher - Layer 1 of the event automation framework.

This module defines the core abstractions for file system event watching:
- FilesystemWatcher: Abstract base class for all file watchers
- FileEvent: Dataclass representing a file system event
- WatchConfig: Configuration for file watching
- ChangeType: Enum for types of file changes
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from monoco.core.scheduler import AgentEventType, EventBus, event_bus

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of file system changes."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"
    RENAMED = "renamed"


@dataclass
class FileEvent:
    """
    Represents a file system event.
    
    Attributes:
        path: Path to the file or directory
        change_type: Type of change (created, modified, deleted, etc.)
        watcher_name: Name of the watcher that emitted this event
        old_path: Original path for move/rename events
        old_content: Previous content hash or snapshot (for content tracking)
        new_content: Current content hash or snapshot
        metadata: Additional event metadata
        timestamp: Event timestamp
    """
    path: Path
    change_type: ChangeType
    watcher_name: str
    old_path: Optional[Path] = None
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_agent_event_type(self) -> Optional[AgentEventType]:
        """Convert FileEvent to AgentEventType if applicable."""
        # This will be overridden by specific watchers
        return None
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to payload dict for EventBus."""
        return {
            "path": str(self.path),
            "change_type": self.change_type.value,
            "watcher_name": self.watcher_name,
            "old_path": str(self.old_path) if self.old_path else None,
            "old_content": self.old_content,
            "new_content": self.new_content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class WatchConfig:
    """
    Configuration for file watching.
    
    Attributes:
        path: Path to watch (file or directory)
        patterns: Glob patterns to match (e.g., "*.md", "*.yaml")
        exclude_patterns: Patterns to exclude
        recursive: Whether to watch recursively
        field_extractors: Optional field extractors for content parsing
        poll_interval: Polling interval in seconds (for polling-based watchers)
    """
    path: Path
    patterns: List[str] = field(default_factory=lambda: ["*"])
    exclude_patterns: List[str] = field(default_factory=list)
    recursive: bool = True
    field_extractors: Dict[str, Callable[[str], Any]] = field(default_factory=dict)
    poll_interval: float = 5.0
    
    def should_watch(self, file_path: Path) -> bool:
        """Check if a file should be watched based on patterns."""
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if file_path.match(pattern):
                return False
        
        # Check include patterns
        for pattern in self.patterns:
            if file_path.match(pattern):
                return True
        
        return False


@dataclass
class FieldChange:
    """Represents a change in a specific field."""
    field_name: str
    old_value: Any
    new_value: Any
    change_type: ChangeType = ChangeType.MODIFIED


class FilesystemWatcher(ABC):
    """
    Abstract base class for file system watchers (Layer 1).
    
    Responsibilities:
    - Monitor file system changes
    - Emit FileEvent objects
    - Integrate with EventBus for event publishing
    
    Lifecycle:
        1. Create watcher with config
        2. Call start() to begin watching
        3. File events are emitted via emit() or callbacks
        4. Call stop() to cleanup
    
    Example:
        >>> config = WatchConfig(path=Path("./Issues"), patterns=["*.md"])
        >>> watcher = IssueWatcher(config)
        >>> await watcher.start()
        >>> # Events are automatically emitted to EventBus
        >>> await watcher.stop()
    """
    
    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        name: Optional[str] = None,
    ):
        self.config = config
        self.event_bus = event_bus or event_bus
        self.name = name or self.__class__.__name__
        self._running = False
        self._callbacks: List[Callable[[FileEvent], None]] = []
        self._state_cache: Dict[str, Any] = {}  # For tracking state changes
    
    @abstractmethod
    async def start(self) -> None:
        """Start watching the file system."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop watching and cleanup resources."""
        pass
    
    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running
    
    def register_callback(self, callback: Callable[[FileEvent], None]) -> None:
        """Register a callback for file events."""
        self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[FileEvent], None]) -> None:
        """Unregister a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def emit(self, event: FileEvent) -> None:
        """
        Emit a file event to all registered callbacks and EventBus.
        
        Args:
            event: The FileEvent to emit
        """
        # Call local callbacks
        for callback in self._callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in callback for {event}: {e}")
        
        # Publish to EventBus if available
        if self.event_bus:
            try:
                agent_event_type = event.to_agent_event_type()
                if agent_event_type:
                    await self.event_bus.publish(
                        agent_event_type,
                        event.to_payload(),
                        source=f"watcher.{self.name}",
                    )
            except Exception as e:
                logger.error(f"Error publishing to EventBus: {e}")
    
    def _get_file_hash(self, file_path: Path) -> Optional[str]:
        """Get a hash of file content for change detection."""
        try:
            import hashlib
            content = file_path.read_text(encoding="utf-8")
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return None
    
    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content safely."""
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.debug(f"Could not read {file_path}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        return {
            "name": self.name,
            "running": self._running,
            "config": {
                "path": str(self.config.path),
                "patterns": self.config.patterns,
                "recursive": self.config.recursive,
            },
            "callbacks": len(self._callbacks),
        }


class PollingWatcher(FilesystemWatcher):
    """
    Base class for polling-based file watchers.
    
    Useful for watching specific files or when native file system
    events are not available/reliable.
    """
    
    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        name: Optional[str] = None,
    ):
        super().__init__(config, event_bus, name)
        self._poll_task: Optional[asyncio.Task] = None
        self._file_states: Dict[Path, Dict[str, Any]] = {}
    
    async def start(self) -> None:
        """Start polling loop."""
        if self._running:
            return
        
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info(f"Started polling watcher: {self.name}")
    
    async def stop(self) -> None:
        """Stop polling loop."""
        if not self._running:
            return
        
        self._running = False
        
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
        
        logger.info(f"Stopped polling watcher: {self.name}")
    
    async def _poll_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                await self._check_changes()
                await asyncio.sleep(self.config.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in poll loop: {e}")
                await asyncio.sleep(self.config.poll_interval)
    
    @abstractmethod
    async def _check_changes(self) -> None:
        """Check for changes - implement in subclass."""
        pass
    
    def _scan_files(self) -> Dict[Path, Dict[str, Any]]:
        """Scan watched path and return file states."""
        states = {}
        
        if self.config.path.is_file():
            files = [self.config.path]
        else:
            if self.config.recursive:
                files = list(self.config.path.rglob("*"))
            else:
                files = list(self.config.path.glob("*"))
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            if not self.config.should_watch(file_path):
                continue
            
            try:
                stat = file_path.stat()
                content = self._read_file_content(file_path)
                states[file_path] = {
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                    "content": content,
                    "hash": self._get_file_hash(file_path) if content else None,
                }
            except Exception as e:
                logger.debug(f"Could not stat {file_path}: {e}")
        
        return states


class WatchdogWatcher(FilesystemWatcher):
    """
    Base class for watchdog-based file watchers.
    
    Uses the watchdog library for efficient native file system events.
    """
    
    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        name: Optional[str] = None,
    ):
        super().__init__(config, event_bus, name)
        self._observer: Optional[Any] = None
    
    def _should_process(self, file_path: Path) -> bool:
        """Check if a file should be processed."""
        # Skip hidden files
        if file_path.name.startswith("."):
            return False
        
        # Skip temporary files
        if file_path.suffix in (".tmp", ".temp", ".part", ".swp", "~"):
            return False
        
        return self.config.should_watch(file_path)
