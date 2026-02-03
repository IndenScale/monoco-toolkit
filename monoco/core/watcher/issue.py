"""
IssueWatcher - Monitors Issue files for changes.

Part of Layer 1 (File Watcher) in the event automation framework.
Emits events for Issue creation, modification, and deletion,
as well as field-level changes in YAML Front Matter.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from monoco.core.scheduler import AgentEventType, EventBus, event_bus
from monoco.features.issue.domain.parser import MarkdownParser
from monoco.features.issue.domain.models import Issue

from .base import (
    ChangeType,
    FieldChange,
    FileEvent,
    FilesystemWatcher,
    WatchConfig,
    PollingWatcher,
)

logger = logging.getLogger(__name__)


class IssueFileEvent(FileEvent):
    """FileEvent specific to Issue files."""
    
    def __init__(
        self,
        path: Path,
        change_type: ChangeType,
        issue_id: Optional[str] = None,
        field_changes: Optional[List[FieldChange]] = None,
        **kwargs,
    ):
        super().__init__(
            path=path,
            change_type=change_type,
            watcher_name="IssueWatcher",
            **kwargs,
        )
        self.issue_id = issue_id
        self.field_changes = field_changes or []
    
    def to_agent_event_type(self) -> Optional[AgentEventType]:
        """Convert to appropriate AgentEventType."""
        if self.change_type == ChangeType.CREATED:
            return AgentEventType.ISSUE_CREATED
        elif self.change_type == ChangeType.MODIFIED:
            # Check for specific field changes
            for fc in self.field_changes:
                if fc.field_name == "stage":
                    return AgentEventType.ISSUE_STAGE_CHANGED
                elif fc.field_name == "status":
                    return AgentEventType.ISSUE_STATUS_CHANGED
            return AgentEventType.ISSUE_UPDATED
        return None
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to payload with Issue-specific fields."""
        payload = super().to_payload()
        payload["issue_id"] = self.issue_id
        payload["field_changes"] = [
            {
                "field": fc.field_name,
                "old_value": fc.old_value,
                "new_value": fc.new_value,
            }
            for fc in self.field_changes
        ]
        return payload


class IssueWatcher(PollingWatcher):
    """
    Watcher for Issue files.
    
    Monitors the Issues/ directory for:
    - New Issue file creation
    - Issue file modifications
    - Issue file deletion
    - YAML Front Matter field changes (status, stage, assignee, etc.)
    
    Example:
        >>> config = WatchConfig(
        ...     path=Path("./Issues"),
        ...     patterns=["*.md"],
        ...     recursive=True,
        ... )
        >>> watcher = IssueWatcher(config)
        >>> await watcher.start()
    """
    
    # Fields to track for changes
    TRACKED_FIELDS = ["status", "stage", "assignee", "criticality", "title"]
    
    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        name: str = "IssueWatcher",
        tracked_fields: Optional[List[str]] = None,
    ):
        # Ensure we watch for markdown files in Issues directory
        if not config.patterns:
            config.patterns = ["*.md"]
        
        super().__init__(config, event_bus, name)
        self.tracked_fields = tracked_fields or self.TRACKED_FIELDS
        self._issue_cache: Dict[str, Dict[str, Any]] = {}  # issue_id -> field values
    
    async def _check_changes(self) -> None:
        """Check for Issue file changes."""
        current_states = self._scan_files()
        current_paths = set(current_states.keys())
        cached_paths = set(self._file_states.keys())
        
        # Detect new files
        for path in current_paths - cached_paths:
            await self._handle_new_file(path, current_states[path])
        
        # Detect deleted files
        for path in cached_paths - current_paths:
            await self._handle_deleted_file(path)
        
        # Detect modified files
        for path in current_paths & cached_paths:
            old_state = self._file_states[path]
            new_state = current_states[path]
            
            if old_state.get("hash") != new_state.get("hash"):
                await self._handle_modified_file(path, old_state, new_state)
        
        # Update cache
        self._file_states = current_states
    
    async def _handle_new_file(self, path: Path, state: Dict[str, Any]) -> None:
        """Handle new Issue file creation."""
        content = state.get("content", "")
        issue = self._parse_issue(content, path)
        
        if issue:
            # Cache the issue fields
            self._issue_cache[issue.frontmatter.id] = self._extract_tracked_fields(issue)
            
            event = IssueFileEvent(
                path=path,
                change_type=ChangeType.CREATED,
                issue_id=issue.frontmatter.id,
                new_content=content,
                metadata={
                    "title": issue.frontmatter.title,
                    "status": issue.frontmatter.status,
                    "stage": issue.frontmatter.stage,
                },
            )
            await self.emit(event)
            logger.debug(f"Issue created: {issue.frontmatter.id}")
    
    async def _handle_deleted_file(self, path: Path) -> None:
        """Handle Issue file deletion."""
        # Find issue_id from path (would need to track this)
        event = IssueFileEvent(
            path=path,
            change_type=ChangeType.DELETED,
            metadata={"path": str(path)},
        )
        await self.emit(event)
        logger.debug(f"Issue deleted: {path}")
    
    async def _handle_modified_file(
        self,
        path: Path,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
    ) -> None:
        """Handle Issue file modification."""
        old_content = old_state.get("content", "")
        new_content = new_state.get("content", "")
        
        issue = self._parse_issue(new_content, path)
        if not issue:
            return
        
        issue_id = issue.frontmatter.id
        
        # Detect field changes
        field_changes = self._detect_field_changes(issue_id, issue)
        
        # Update cache
        self._issue_cache[issue_id] = self._extract_tracked_fields(issue)
        
        # Emit event with field changes
        event = IssueFileEvent(
            path=path,
            change_type=ChangeType.MODIFIED,
            issue_id=issue_id,
            old_content=old_content,
            new_content=new_content,
            field_changes=field_changes,
            metadata={
                "title": issue.frontmatter.title,
                "status": issue.frontmatter.status,
                "stage": issue.frontmatter.stage,
            },
        )
        await self.emit(event)
        
        # Also emit individual field change events
        for fc in field_changes:
            await self._emit_field_change_event(issue, fc)
        
        if field_changes:
            logger.debug(f"Issue {issue_id} modified: {[fc.field_name for fc in field_changes]}")
    
    async def _emit_field_change_event(
        self,
        issue: Issue,
        field_change: FieldChange,
    ) -> None:
        """Emit a specific field change event."""
        event_type = None
        
        if field_change.field_name == "stage":
            event_type = AgentEventType.ISSUE_STAGE_CHANGED
        elif field_change.field_name == "status":
            event_type = AgentEventType.ISSUE_STATUS_CHANGED
        
        if event_type and self.event_bus:
            await self.event_bus.publish(
                event_type,
                {
                    "issue_id": issue.frontmatter.id,
                    "issue_title": issue.frontmatter.title,
                    "old_value": field_change.old_value,
                    "new_value": field_change.new_value,
                    "field": field_change.field_name,
                    "path": str(issue.path) if issue.path else None,
                },
                source=f"watcher.{self.name}",
            )
    
    def _parse_issue(self, content: str, path: Path) -> Optional[Issue]:
        """Parse Issue from content."""
        try:
            return MarkdownParser.parse(content, str(path))
        except Exception as e:
            logger.debug(f"Could not parse issue from {path}: {e}")
            return None
    
    def _extract_tracked_fields(self, issue: Issue) -> Dict[str, Any]:
        """Extract tracked fields from an Issue."""
        fm = issue.frontmatter
        fields = {}
        
        for field_name in self.tracked_fields:
            if hasattr(fm, field_name):
                fields[field_name] = getattr(fm, field_name)
        
        return fields
    
    def _detect_field_changes(
        self,
        issue_id: str,
        issue: Issue,
    ) -> List[FieldChange]:
        """Detect changes in tracked fields."""
        changes = []
        old_fields = self._issue_cache.get(issue_id, {})
        new_fields = self._extract_tracked_fields(issue)
        
        for field_name in self.tracked_fields:
            old_value = old_fields.get(field_name)
            new_value = new_fields.get(field_name)
            
            if old_value != new_value and old_value is not None:
                changes.append(FieldChange(
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                ))
        
        return changes
    
    def get_issue_state(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Get cached state for an issue."""
        return self._issue_cache.get(issue_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        stats = super().get_stats()
        stats.update({
            "tracked_issues": len(self._issue_cache),
            "tracked_fields": self.tracked_fields,
        })
        return stats
