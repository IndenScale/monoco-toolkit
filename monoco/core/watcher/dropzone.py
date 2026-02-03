"""
DropzoneWatcher - Adapter for the existing dropzone watcher.

Part of Layer 1 (File Watcher) in the event automation framework.
Wraps the existing ingestion watcher to fit the FilesystemWatcher interface.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from monoco.core.scheduler import AgentEventType, EventBus, event_bus
from monoco.core.ingestion.watcher import (
    DropzoneWatcher as LegacyDropzoneWatcher,
    IngestionEvent,
    IngestionEventType,
)
from monoco.core.artifacts.manager import ArtifactManager

from .base import (
    ChangeType,
    FileEvent,
    FilesystemWatcher,
    WatchConfig,
)

logger = logging.getLogger(__name__)


class DropzoneFileEvent(FileEvent):
    """FileEvent specific to Dropzone."""
    
    def __init__(
        self,
        path: Path,
        change_type: ChangeType,
        ingestion_event_type: IngestionEventType,
        artifact_id: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            path=path,
            change_type=change_type,
            watcher_name="DropzoneWatcher",
            **kwargs,
        )
        self.ingestion_event_type = ingestion_event_type
        self.artifact_id = artifact_id
    
    def to_agent_event_type(self) -> Optional[AgentEventType]:
        """Dropzone events don't map directly to agent events."""
        return None
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to payload with Dropzone-specific fields."""
        payload = super().to_payload()
        payload["ingestion_event_type"] = self.ingestion_event_type.value
        payload["artifact_id"] = self.artifact_id
        return payload


class DropzoneWatcher(FilesystemWatcher):
    """
    Adapter for the existing DropzoneWatcher.
    
    Wraps the legacy ingestion watcher to provide a unified interface
    while maintaining backward compatibility.
    
    Example:
        >>> from monoco.core.artifacts.manager import ArtifactManager
        >>> artifact_manager = ArtifactManager()
        >>> config = WatchConfig(path=Path("./.monoco/dropzone"))
        >>> watcher = DropzoneWatcher(config, artifact_manager)
        >>> await watcher.start()
    """
    
    def __init__(
        self,
        config: WatchConfig,
        artifact_manager: ArtifactManager,
        event_bus: Optional[EventBus] = None,
        name: str = "DropzoneWatcher",
    ):
        super().__init__(config, event_bus, name)
        self.artifact_manager = artifact_manager
        
        # Create legacy watcher
        self._legacy_watcher = LegacyDropzoneWatcher(
            dropzone_path=config.path,
            artifact_manager=artifact_manager,
            process_existing=False,
        )
        
        # Set up event forwarding
        self._legacy_watcher.set_event_callback(self._on_ingestion_event)
    
    async def start(self) -> None:
        """Start watching the dropzone."""
        if self._running:
            return
        
        self._legacy_watcher.start()
        self._running = True
        logger.info(f"Started DropzoneWatcher: {self.config.path}")
    
    async def stop(self) -> None:
        """Stop watching the dropzone."""
        if not self._running:
            return
        
        self._legacy_watcher.stop()
        self._running = False
        logger.info(f"Stopped DropzoneWatcher: {self.config.path}")
    
    def _on_ingestion_event(self, event: IngestionEvent) -> None:
        """Handle ingestion events from legacy watcher."""
        # Map ingestion event type to change type
        change_type_map = {
            IngestionEventType.FILE_DETECTED: ChangeType.CREATED,
            IngestionEventType.CONVERSION_STARTED: ChangeType.MODIFIED,
            IngestionEventType.CONVERSION_COMPLETED: ChangeType.MODIFIED,
            IngestionEventType.CONVERSION_FAILED: ChangeType.MODIFIED,
            IngestionEventType.ARTIFACT_REGISTERED: ChangeType.MODIFIED,
        }
        
        change_type = change_type_map.get(event.event_type, ChangeType.MODIFIED)
        
        # Create unified event
        file_event = DropzoneFileEvent(
            path=event.file_path,
            change_type=change_type,
            ingestion_event_type=event.event_type,
            artifact_id=event.artifact_id,
            metadata={
                "task_id": event.task_id,
                "error_message": event.error_message,
                **event.metadata,
            },
        )
        
        # Emit synchronously (called from sync context)
        asyncio.create_task(self.emit(file_event))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        stats = super().get_stats()
        legacy_stats = self._legacy_watcher.get_stats()
        stats.update(legacy_stats)
        return stats
