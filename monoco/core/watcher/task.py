"""
TaskWatcher - Monitors task files for changes.

Part of Layer 1 (File Watcher) in the event automation framework.
Emits events for task status changes and completion.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from monoco.core.scheduler import AgentEventType, EventBus, event_bus

from .base import (
    ChangeType,
    FieldChange,
    FileEvent,
    FilesystemWatcher,
    WatchConfig,
    PollingWatcher,
)

logger = logging.getLogger(__name__)


class TaskFileEvent(FileEvent):
    """FileEvent specific to Task files."""
    
    def __init__(
        self,
        path: Path,
        change_type: ChangeType,
        task_changes: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        super().__init__(
            path=path,
            change_type=change_type,
            watcher_name="TaskWatcher",
            **kwargs,
        )
        self.task_changes = task_changes or []
    
    def to_agent_event_type(self) -> Optional[AgentEventType]:
        """Tasks map to issue updates for now."""
        return AgentEventType.ISSUE_UPDATED
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to payload with Task-specific fields."""
        payload = super().to_payload()
        payload["task_changes"] = self.task_changes
        return payload


@dataclass
class TaskItem:
    """Represents a single task item."""
    content: str
    state: str  # " ", "x", "X", "-", "/"
    line_number: int
    level: int = 0
    
    @property
    def is_completed(self) -> bool:
        return self.state.lower() == "x"
    
    @property
    def is_in_progress(self) -> bool:
        return self.state in ("-", "/")


class TaskWatcher(PollingWatcher):
    """
    Watcher for task files.
    
    Monitors task files (e.g., tasks.md, TODO.md) for:
    - Task creation
    - Task status changes (todo -> doing -> done)
    - Task completion
    
    Example:
        >>> config = WatchConfig(
        ...     path=Path("./tasks.md"),
        ...     patterns=["*.md"],
        ... )
        >>> watcher = TaskWatcher(config)
        >>> await watcher.start()
    """
    
    # Regex to match task items
    TASK_PATTERN = re.compile(
        r"^(\s*)-\s*\[([ xX\-/])\]\s*(.+)$",
        re.MULTILINE,
    )
    
    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        name: str = "TaskWatcher",
    ):
        super().__init__(config, event_bus, name)
        self._task_cache: Dict[str, TaskItem] = {}  # task_id -> TaskItem
    
    async def _check_changes(self) -> None:
        """Check for task file changes."""
        if not self.config.path.exists():
            return
        
        try:
            content = self._read_file_content(self.config.path) or ""
            current_tasks = self._parse_tasks(content)
            
            # Detect changes
            task_changes = self._detect_task_changes(current_tasks)
            
            if task_changes:
                await self._emit_task_changes(task_changes)
            
            # Update cache
            self._task_cache = current_tasks
        
        except Exception as e:
            logger.error(f"Error checking task file: {e}")
    
    def _parse_tasks(self, content: str) -> Dict[str, TaskItem]:
        """Parse task items from content."""
        tasks = {}
        lines = content.split("\n")
        
        for line_num, line in enumerate(lines, 1):
            match = self.TASK_PATTERN.match(line)
            if match:
                indent = match.group(1)
                state = match.group(2)
                task_content = match.group(3).strip()
                
                # Generate task ID from content hash
                import hashlib
                task_id = hashlib.md5(
                    f"{line_num}:{task_content}".encode()
                ).hexdigest()[:12]
                
                tasks[task_id] = TaskItem(
                    content=task_content,
                    state=state,
                    line_number=line_num,
                    level=len(indent) // 2,
                )
        
        return tasks
    
    def _detect_task_changes(
        self,
        current_tasks: Dict[str, TaskItem],
    ) -> List[Dict[str, Any]]:
        """Detect changes between cached and current tasks."""
        changes = []
        current_ids = set(current_tasks.keys())
        cached_ids = set(self._task_cache.keys())
        
        # New tasks
        for task_id in current_ids - cached_ids:
            task = current_tasks[task_id]
            changes.append({
                "type": "created",
                "task_id": task_id,
                "content": task.content,
                "state": task.state,
            })
        
        # Deleted tasks
        for task_id in cached_ids - current_ids:
            task = self._task_cache[task_id]
            changes.append({
                "type": "deleted",
                "task_id": task_id,
                "content": task.content,
            })
        
        # Modified tasks
        for task_id in current_ids & cached_ids:
            current = current_tasks[task_id]
            cached = self._task_cache[task_id]
            
            if current.state != cached.state:
                changes.append({
                    "type": "state_changed",
                    "task_id": task_id,
                    "content": current.content,
                    "old_state": cached.state,
                    "new_state": current.state,
                    "is_completed": current.is_completed,
                })
        
        return changes
    
    async def _emit_task_changes(self, changes: List[Dict[str, Any]]) -> None:
        """Emit events for task changes."""
        event = TaskFileEvent(
            path=self.config.path,
            change_type=ChangeType.MODIFIED,
            task_changes=changes,
            metadata={
                "total_changes": len(changes),
                "completed_tasks": sum(1 for c in changes if c.get("is_completed")),
            },
        )
        await self.emit(event)
        
        # Log summary
        created = sum(1 for c in changes if c["type"] == "created")
        completed = sum(1 for c in changes if c["type"] == "state_changed" and c.get("is_completed"))
        logger.debug(f"Task changes: {created} created, {completed} completed")
    
    def get_task_stats(self) -> Dict[str, int]:
        """Get task statistics."""
        total = len(self._task_cache)
        completed = sum(1 for t in self._task_cache.values() if t.is_completed)
        in_progress = sum(1 for t in self._task_cache.values() if t.is_in_progress)
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": total - completed - in_progress,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        stats = super().get_stats()
        stats.update(self.get_task_stats())
        return stats
