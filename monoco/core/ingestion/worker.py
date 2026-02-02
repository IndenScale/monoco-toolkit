"""
Conversion Worker for Monoco Mailroom.

Handles document conversion tasks using discovered tools.
Supports concurrent processing with asyncio.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any

from .discovery import EnvironmentDiscovery, ToolCapability, ConversionTool

logger = logging.getLogger(__name__)


class ConversionStatus(str, Enum):
    """Status of a conversion task."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ConversionTask:
    """Represents a document conversion task."""
    task_id: str
    source_path: Path
    target_format: str
    output_dir: Path
    options: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def source_extension(self) -> str:
        """Get the source file extension."""
        return self.source_path.suffix.lower()


@dataclass
class ConversionResult:
    """Result of a conversion operation."""
    task_id: str
    status: ConversionStatus
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    processing_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class ConversionWorker:
    """
    Worker for processing document conversion tasks.
    
    Features:
    - Async processing with semaphore-controlled concurrency
    - Tool selection based on file type and capability
    - Automatic cleanup of temporary files
    - Progress callbacks
    """

    # File extension to required capability mapping
    EXTENSION_CAPABILITIES = {
        ".docx": ToolCapability.DOCX_TO_MD,
        ".doc": ToolCapability.DOCX_TO_TEXT,
        ".odt": ToolCapability.ODT_TO_TEXT,
        ".pdf": ToolCapability.PDF_TO_TEXT,
        ".xlsx": ToolCapability.XLSX_TO_CSV,
        ".xls": ToolCapability.XLSX_TO_CSV,
        ".pptx": ToolCapability.PPTX_TO_TEXT,
        ".ppt": ToolCapability.PPTX_TO_TEXT,
    }

    def __init__(
        self,
        discovery: Optional[EnvironmentDiscovery] = None,
        max_concurrent: int = 4,
        timeout_seconds: float = 120.0,
    ):
        """
        Initialize the conversion worker.
        
        Args:
            discovery: EnvironmentDiscovery instance (creates new if None)
            max_concurrent: Maximum concurrent conversion tasks
            timeout_seconds: Timeout for individual conversions
        """
        self.discovery = discovery or EnvironmentDiscovery()
        self.discovery.discover()
        
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks: dict[str, asyncio.Task] = {}
        
        # Callbacks
        self._on_progress: Optional[Callable[[str, ConversionStatus, float], None]] = None
        self._on_complete: Optional[Callable[[ConversionResult], None]] = None

    def set_callbacks(
        self,
        on_progress: Optional[Callable[[str, ConversionStatus, float], None]] = None,
        on_complete: Optional[Callable[[ConversionResult], None]] = None,
    ) -> None:
        """Set progress and completion callbacks."""
        self._on_progress = on_progress
        self._on_complete = on_complete

    def _notify_progress(self, task_id: str, status: ConversionStatus, progress: float) -> None:
        """Notify progress callback."""
        if self._on_progress:
            try:
                self._on_progress(task_id, status, progress)
            except Exception:
                pass

    def _notify_complete(self, result: ConversionResult) -> None:
        """Notify completion callback."""
        if self._on_complete:
            try:
                self._on_complete(result)
            except Exception:
                pass

    def can_convert(self, file_path: Path) -> bool:
        """
        Check if a file can be converted.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if conversion is possible
        """
        ext = file_path.suffix.lower()
        if ext not in self.EXTENSION_CAPABILITIES:
            return False
        
        capability = self.EXTENSION_CAPABILITIES[ext]
        return self.discovery.has_capability(capability)

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        supported = []
        for ext, capability in self.EXTENSION_CAPABILITIES.items():
            if self.discovery.has_capability(capability):
                supported.append(ext)
        return supported

    async def submit(self, task: ConversionTask) -> ConversionResult:
        """
        Submit a conversion task for processing.
        
        Args:
            task: The conversion task to process
            
        Returns:
            ConversionResult with status and output details
        """
        async with self._semaphore:
            return await self._process_task(task)

    async def submit_batch(
        self,
        tasks: list[ConversionTask],
    ) -> list[ConversionResult]:
        """
        Submit multiple tasks for concurrent processing.
        
        Args:
            tasks: List of conversion tasks
            
        Returns:
            List of ConversionResults (order may vary)
        """
        coroutines = [self.submit(task) for task in tasks]
        return await asyncio.gather(*coroutines, return_exceptions=True)

    async def _process_task(self, task: ConversionTask) -> ConversionResult:
        """Process a single conversion task."""
        import time
        start_time = time.time()
        
        self._notify_progress(task.task_id, ConversionStatus.PROCESSING, 0.0)
        
        try:
            # Validate source file
            if not task.source_path.exists():
                return self._create_error_result(
                    task, "Source file does not exist"
                )

            # Get required capability
            ext = task.source_extension
            if ext not in self.EXTENSION_CAPABILITIES:
                return self._create_error_result(
                    task, f"Unsupported file extension: {ext}"
                )

            capability = self.EXTENSION_CAPABILITIES[ext]
            tool = self.discovery.get_best_tool(capability)
            
            if not tool:
                return self._create_error_result(
                    task, f"No tool available for {capability.value}"
                )

            # Perform conversion
            result = await self._convert_with_tool(task, tool, capability)
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            
            self._notify_complete(result)
            return result

        except asyncio.TimeoutError:
            result = self._create_error_result(task, "Conversion timeout")
            self._notify_complete(result)
            return result
        except Exception as e:
            logger.exception(f"Conversion failed for task {task.task_id}")
            result = self._create_error_result(task, str(e))
            self._notify_complete(result)
            return result

    def _create_error_result(self, task: ConversionTask, message: str) -> ConversionResult:
        """Create a failed conversion result."""
        return ConversionResult(
            task_id=task.task_id,
            status=ConversionStatus.FAILED,
            error_message=message,
        )

    async def _convert_with_tool(
        self,
        task: ConversionTask,
        tool: ConversionTool,
        capability: ToolCapability,
    ) -> ConversionResult:
        """Convert using the specified tool."""
        
        if tool.tool_type.value == "libreoffice":
            return await self._convert_with_libreoffice(task, tool)
        elif tool.tool_type.value == "pandoc":
            return await self._convert_with_pandoc(task, tool)
        elif tool.tool_type.value in ("pdf2text", "pdftohtml"):
            return await self._convert_with_pdf_tool(task, tool)
        else:
            return self._create_error_result(task, f"Unknown tool type: {tool.tool_type}")

    async def _convert_with_libreoffice(
        self,
        task: ConversionTask,
        tool: ConversionTool,
    ) -> ConversionResult:
        """Convert using LibreOffice."""
        # Create temp directory for conversion
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Build LibreOffice command
            cmd = [
                str(tool.executable_path),
                "--headless",
                "--convert-to", "txt:Text",
                "--outdir", str(tmp_path),
                str(task.source_path),
            ]
            
            # Run conversion
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds,
                )
                
                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    return self._create_error_result(task, f"LibreOffice error: {error_msg}")
                
                # Find output file
                base_name = task.source_path.stem
                output_file = tmp_path / f"{base_name}.txt"
                
                if not output_file.exists():
                    return self._create_error_result(task, "Output file not created")
                
                # Move to final destination
                task.output_dir.mkdir(parents=True, exist_ok=True)
                final_output = task.output_dir / f"{base_name}.txt"
                shutil.move(str(output_file), str(final_output))
                
                return ConversionResult(
                    task_id=task.task_id,
                    status=ConversionStatus.SUCCESS,
                    output_path=final_output,
                    metadata={
                        "tool": tool.name,
                        "tool_version": tool.version,
                    },
                )
                
            except asyncio.TimeoutError:
                return self._create_error_result(task, "LibreOffice conversion timeout")

    async def _convert_with_pandoc(
        self,
        task: ConversionTask,
        tool: ConversionTool,
    ) -> ConversionResult:
        """Convert using Pandoc."""
        task.output_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = task.source_path.stem
        output_file = task.output_dir / f"{base_name}.md"
        
        cmd = [
            str(tool.executable_path),
            str(task.source_path),
            "-o", str(output_file),
            "-t", "markdown",
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                return self._create_error_result(task, f"Pandoc error: {error_msg}")
            
            return ConversionResult(
                task_id=task.task_id,
                status=ConversionStatus.SUCCESS,
                output_path=output_file,
                metadata={
                    "tool": tool.name,
                    "tool_version": tool.version,
                },
            )
            
        except asyncio.TimeoutError:
            return self._create_error_result(task, "Pandoc conversion timeout")

    async def _convert_with_pdf_tool(
        self,
        task: ConversionTask,
        tool: ConversionTool,
    ) -> ConversionResult:
        """Convert PDF using pdftotext or similar."""
        task.output_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = task.source_path.stem
        output_file = task.output_dir / f"{base_name}.txt"
        
        cmd = [
            str(tool.executable_path),
            str(task.source_path),
            str(output_file),
        ]
        
        # Add layout preservation for pdftotext
        if "pdftotext" in tool.name:
            cmd.insert(1, "-layout")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                return self._create_error_result(task, f"PDF tool error: {error_msg}")
            
            return ConversionResult(
                task_id=task.task_id,
                status=ConversionStatus.SUCCESS,
                output_path=output_file,
                metadata={
                    "tool": tool.name,
                    "tool_version": tool.version,
                },
            )
            
        except asyncio.TimeoutError:
            return self._create_error_result(task, "PDF conversion timeout")

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel an active task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if cancelled, False if not found
        """
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.cancel()
            return True
        return False

    def get_active_count(self) -> int:
        """Get number of currently active tasks."""
        return len(self._active_tasks)
