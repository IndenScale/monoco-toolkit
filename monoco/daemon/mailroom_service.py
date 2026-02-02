"""
Mailroom Service for Monoco Daemon.

Manages automated document ingestion with concurrent processing,
environment discovery, and artifact registration.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from monoco.core.ingestion.discovery import EnvironmentDiscovery
from monoco.core.ingestion.worker import ConversionWorker
from monoco.core.ingestion.watcher import DropzoneWatcher, IngestionEvent
from monoco.core.artifacts.manager import ArtifactManager

logger = logging.getLogger(__name__)


class MailroomService:
    """
    Service for automated document ingestion in Monoco Daemon.
    
    Features:
    - Environment discovery for conversion tools
    - Dropzone monitoring for new files
    - Concurrent conversion processing
    - Artifact registration
    - SSE event broadcasting
    """

    def __init__(
        self,
        workspace_root: Path,
        broadcaster: Optional[Any] = None,
        dropzone_path: Optional[Path] = None,
        max_concurrent: int = 4,
    ):
        """
        Initialize the Mailroom service.
        
        Args:
            workspace_root: Root directory of the workspace
            broadcaster: SSE broadcaster for events
            dropzone_path: Path to dropzone directory (default: workspace/.monoco/dropzone)
            max_concurrent: Maximum concurrent conversion tasks
        """
        self.workspace_root = Path(workspace_root)
        self.broadcaster = broadcaster
        
        # Default dropzone location
        self.dropzone_path = dropzone_path or (self.workspace_root / ".monoco" / "dropzone")
        
        # Initialize components
        self.discovery = EnvironmentDiscovery()
        self.conversion_worker = ConversionWorker(
            discovery=self.discovery,
            max_concurrent=max_concurrent,
        )
        
        # Artifact manager (lazy init)
        self._artifact_manager: Optional[ArtifactManager] = None
        
        # Watcher (lazy init)
        self._watcher: Optional[DropzoneWatcher] = None
        
        # State
        self._running = False
        self._stats: Dict[str, Any] = {
            "files_detected": 0,
            "conversions_success": 0,
            "conversions_failed": 0,
            "artifacts_registered": 0,
        }

    @property
    def artifact_manager(self) -> ArtifactManager:
        """Get or create the artifact manager."""
        if self._artifact_manager is None:
            self._artifact_manager = ArtifactManager(self.workspace_root)
        return self._artifact_manager

    async def start(self) -> None:
        """Start the Mailroom service."""
        if self._running:
            return

        logger.info("Starting Mailroom service...")

        # Perform environment discovery
        tools = self.discovery.discover()
        total_tools = sum(len(t) for t in tools.values())
        logger.info(f"Discovered {total_tools} conversion tools")

        # Log discovered capabilities
        capabilities = self.discovery.get_capabilities_summary()
        logger.info(f"Capabilities: {capabilities}")

        # Initialize and start dropzone watcher
        self._watcher = DropzoneWatcher(
            dropzone_path=self.dropzone_path,
            artifact_manager=self.artifact_manager,
            conversion_worker=self.conversion_worker,
            process_existing=False,  # Don't process existing files on startup
        )
        
        # Set up event callback
        self._watcher.set_event_callback(self._on_ingestion_event)
        
        # Start watching (this is synchronous, runs in background thread)
        self._watcher.start()
        
        self._running = True
        logger.info(f"Mailroom service started. Dropzone: {self.dropzone_path}")

    async def stop(self) -> None:
        """Stop the Mailroom service."""
        if not self._running:
            return

        logger.info("Stopping Mailroom service...")

        if self._watcher:
            self._watcher.stop()
            self._watcher = None

        self._running = False
        logger.info("Mailroom service stopped")

    def _on_ingestion_event(self, event: IngestionEvent) -> None:
        """Handle ingestion events from the watcher."""
        # Update stats
        if event.event_type.value == "file_detected":
            self._stats["files_detected"] += 1
        elif event.event_type.value == "conversion_completed":
            self._stats["conversions_success"] += 1
        elif event.event_type.value == "conversion_failed":
            self._stats["conversions_failed"] += 1
        elif event.event_type.value == "artifact_registered":
            self._stats["artifacts_registered"] += 1

        # Broadcast via SSE if broadcaster available
        if self.broadcaster:
            asyncio.create_task(self._broadcast_event(event))

    async def _broadcast_event(self, event: IngestionEvent) -> None:
        """Broadcast ingestion event to SSE clients."""
        try:
            payload = {
                "type": event.event_type.value,
                "file_path": str(event.file_path),
                "task_id": event.task_id,
                "artifact_id": event.artifact_id,
                "error_message": event.error_message,
                "metadata": event.metadata,
                "timestamp": event.timestamp.isoformat(),
            }
            await self.broadcaster.broadcast("MAILROOM_EVENT", payload)
        except Exception as e:
            logger.error(f"Failed to broadcast mailroom event: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current service status and statistics."""
        capabilities = self.discovery.get_capabilities_summary()
        
        return {
            "running": self._running,
            "dropzone_path": str(self.dropzone_path),
            "capabilities": capabilities,
            "supported_extensions": self.conversion_worker.get_supported_extensions(),
            "stats": self._stats.copy(),
            "tools": [
                {
                    "name": tool.name,
                    "type": tool.tool_type.value,
                    "version": tool.version,
                    "capabilities": [c.value for c in tool.capabilities],
                }
                for tool in self.discovery.get_all_tools()
            ],
        }

    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._running

    def get_discovery(self) -> EnvironmentDiscovery:
        """Get the environment discovery instance."""
        return self.discovery

    def get_worker(self) -> ConversionWorker:
        """Get the conversion worker instance."""
        return self.conversion_worker
