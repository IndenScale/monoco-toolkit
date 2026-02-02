"""
Dropzone Watcher for Monoco Mailroom.

Monitors dropzone directories for new files and triggers
automated ingestion workflows.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any, Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent

from .worker import ConversionWorker, ConversionTask, ConversionResult, ConversionStatus
from ..artifacts.manager import ArtifactManager
from ..artifacts.models import ArtifactSourceType

logger = logging.getLogger(__name__)


class IngestionEventType(str, Enum):
    """Types of ingestion events."""
    FILE_DETECTED = "file_detected"
    CONVERSION_STARTED = "conversion_started"
    CONVERSION_COMPLETED = "conversion_completed"
    CONVERSION_FAILED = "conversion_failed"
    ARTIFACT_REGISTERED = "artifact_registered"


@dataclass
class IngestionEvent:
    """Event emitted during the ingestion process."""
    event_type: IngestionEventType
    file_path: Path
    task_id: Optional[str] = None
    artifact_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DropzoneHandler(FileSystemEventHandler):
    """File system event handler for dropzone monitoring."""

    def __init__(
        self,
        dropzone_path: Path,
        on_file_detected: Callable[[Path], None],
        supported_extensions: Optional[Set[str]] = None,
    ):
        self.dropzone_path = Path(dropzone_path)
        self.on_file_detected = on_file_detected
        self.supported_extensions = supported_extensions or {
            ".docx", ".doc", ".pdf", ".odt",
            ".xlsx", ".xls", ".pptx", ".ppt",
        }
        self._processed_files: Set[Path] = set()

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if self._should_process(file_path):
            self._processed_files.add(file_path.resolve())
            self.on_file_detected(file_path)

    def on_moved(self, event):
        """Handle file move events (e.g., atomic writes)."""
        if event.is_directory:
            return
        
        file_path = Path(event.dest_path)
        if self._should_process(file_path):
            self._processed_files.add(file_path.resolve())
            self.on_file_detected(file_path)

    def _should_process(self, file_path: Path) -> bool:
        """Check if a file should be processed."""
        # Skip hidden files
        if file_path.name.startswith("."):
            return False
        
        # Skip temporary files
        if file_path.suffix in (".tmp", ".temp", ".part"):
            return False
        
        # Check extension
        if file_path.suffix.lower() not in self.supported_extensions:
            return False
        
        # Skip already processed
        if file_path.resolve() in self._processed_files:
            return False
        
        return True


class DropzoneWatcher:
    """
    Watches dropzone directories and orchestrates automated ingestion.
    
    Features:
    - Real-time file system monitoring
    - Automatic conversion using ConversionWorker
    - Artifact registration with ArtifactManager
    - Event callbacks for integration
    """

    def __init__(
        self,
        dropzone_path: Path,
        artifact_manager: ArtifactManager,
        conversion_worker: Optional[ConversionWorker] = None,
        output_dir: Optional[Path] = None,
        process_existing: bool = False,
    ):
        """
        Initialize the dropzone watcher.
        
        Args:
            dropzone_path: Directory to monitor for new files
            artifact_manager: ArtifactManager for registering converted files
            conversion_worker: ConversionWorker for document conversion
            output_dir: Directory for converted files (default: dropzone/converted)
            process_existing: Whether to process files already in dropzone
        """
        self.dropzone_path = Path(dropzone_path)
        self.artifact_manager = artifact_manager
        self.conversion_worker = conversion_worker or ConversionWorker()
        self.output_dir = output_dir or (self.dropzone_path / "converted")
        self.process_existing = process_existing
        
        # Event callbacks
        self._on_event: Optional[Callable[[IngestionEvent], None]] = None
        
        # State
        self._observer: Optional[Observer] = None
        self._running = False
        self._pending_tasks: dict[str, asyncio.Task] = {}

    def set_event_callback(self, callback: Callable[[IngestionEvent], None]) -> None:
        """Set callback for ingestion events."""
        self._on_event = callback

    def _emit_event(self, event: IngestionEvent) -> None:
        """Emit an ingestion event."""
        if self._on_event:
            try:
                self._on_event(event)
            except Exception:
                pass

    def start(self) -> None:
        """Start watching the dropzone directory."""
        if self._running:
            return

        # Ensure directories exist
        self.dropzone_path.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set up file system observer
        self._handler = DropzoneHandler(
            self.dropzone_path,
            self._on_file_detected,
            set(self.conversion_worker.get_supported_extensions()),
        )
        
        self._observer = Observer()
        self._observer.schedule(self._handler, str(self.dropzone_path), recursive=False)
        self._observer.start()
        
        self._running = True
        logger.info(f"Started watching dropzone: {self.dropzone_path}")

        # Process existing files if requested
        if self.process_existing:
            self._scan_existing_files()

    def stop(self) -> None:
        """Stop watching the dropzone directory."""
        if not self._running:
            return

        self._running = False

        # Cancel pending tasks
        for task in self._pending_tasks.values():
            task.cancel()
        self._pending_tasks.clear()

        # Stop observer
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

        logger.info(f"Stopped watching dropzone: {self.dropzone_path}")

    def _scan_existing_files(self) -> None:
        """Scan and process existing files in dropzone."""
        for file_path in self.dropzone_path.iterdir():
            if file_path.is_file() and self._handler._should_process(file_path):
                self._on_file_detected(file_path)

    def _on_file_detected(self, file_path: Path) -> None:
        """Handle newly detected file."""
        logger.info(f"File detected: {file_path}")
        
        self._emit_event(IngestionEvent(
            event_type=IngestionEventType.FILE_DETECTED,
            file_path=file_path,
        ))

        # Create async task for processing
        task_id = str(uuid.uuid4())
        asyncio.create_task(self._process_file(file_path, task_id))

    async def _process_file(self, file_path: Path, task_id: str) -> None:
        """Process a detected file through the ingestion pipeline."""
        try:
            # Step 1: Check if conversion is needed/possible
            if not self.conversion_worker.can_convert(file_path):
                logger.warning(f"Cannot convert file: {file_path}")
                self._emit_event(IngestionEvent(
                    event_type=IngestionEventType.CONVERSION_FAILED,
                    file_path=file_path,
                    task_id=task_id,
                    error_message="No conversion tool available for this file type",
                ))
                return

            # Step 2: Create conversion task
            conversion_task = ConversionTask(
                task_id=task_id,
                source_path=file_path,
                target_format="txt",
                output_dir=self.output_dir,
            )

            self._emit_event(IngestionEvent(
                event_type=IngestionEventType.CONVERSION_STARTED,
                file_path=file_path,
                task_id=task_id,
            ))

            # Step 3: Perform conversion
            result = await self.conversion_worker.submit(conversion_task)

            if result.status != ConversionStatus.SUCCESS:
                logger.error(f"Conversion failed for {file_path}: {result.error_message}")
                self._emit_event(IngestionEvent(
                    event_type=IngestionEventType.CONVERSION_FAILED,
                    file_path=file_path,
                    task_id=task_id,
                    error_message=result.error_message,
                ))
                return

            self._emit_event(IngestionEvent(
                event_type=IngestionEventType.CONVERSION_COMPLETED,
                file_path=file_path,
                task_id=task_id,
                metadata={
                    "output_path": str(result.output_path),
                    "processing_time_ms": result.processing_time_ms,
                },
            ))

            # Step 4: Register as artifact
            if result.output_path and result.output_path.exists():
                artifact_meta = self._register_artifact(
                    result.output_path,
                    source_file=file_path,
                    conversion_metadata=result.metadata,
                )
                
                self._emit_event(IngestionEvent(
                    event_type=IngestionEventType.ARTIFACT_REGISTERED,
                    file_path=file_path,
                    task_id=task_id,
                    artifact_id=artifact_meta.artifact_id,
                    metadata={
                        "content_hash": artifact_meta.content_hash,
                        "content_type": artifact_meta.content_type,
                    },
                ))

                logger.info(f"Successfully ingested {file_path} as artifact {artifact_meta.artifact_id}")

        except Exception as e:
            logger.exception(f"Error processing file {file_path}")
            self._emit_event(IngestionEvent(
                event_type=IngestionEventType.CONVERSION_FAILED,
                file_path=file_path,
                task_id=task_id,
                error_message=str(e),
            ))

    def _register_artifact(
        self,
        file_path: Path,
        source_file: Path,
        conversion_metadata: dict[str, Any],
    ) -> Any:
        """Register converted file as an artifact."""
        metadata = {
            "source_file": str(source_file),
            "original_filename": source_file.name,
            **conversion_metadata,
        }
        
        return self.artifact_manager.store_file(
            file_path=file_path,
            source_type=ArtifactSourceType.IMPORTED,
            content_type="text/plain",
            tags=["mailroom", "converted", source_file.suffix.lower().lstrip(".")],
            metadata=metadata,
        )

    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running

    def get_stats(self) -> dict[str, Any]:
        """Get watcher statistics."""
        return {
            "running": self._running,
            "dropzone_path": str(self.dropzone_path),
            "output_dir": str(self.output_dir),
            "pending_tasks": len(self._pending_tasks),
            "supported_extensions": list(self.conversion_worker.get_supported_extensions()),
        }
