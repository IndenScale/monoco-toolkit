"""
Tests for Monoco Mailroom Conversion Worker.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from monoco.core.ingestion.worker import (
    ConversionWorker,
    ConversionTask,
    ConversionResult,
    ConversionStatus,
)
from monoco.core.ingestion.discovery import ToolCapability, ConversionTool, ToolType


class TestConversionTask:
    """Test suite for ConversionTask."""

    def test_task_creation(self, tmp_path):
        """Test creating a conversion task."""
        source = tmp_path / "test.docx"
        output = tmp_path / "output"
        
        task = ConversionTask(
            task_id="test-123",
            source_path=source,
            target_format="txt",
            output_dir=output,
        )
        
        assert task.task_id == "test-123"
        assert task.source_path == source
        assert task.target_format == "txt"
        assert task.output_dir == output

    def test_source_extension(self, tmp_path):
        """Test source_extension property."""
        task = ConversionTask(
            task_id="test",
            source_path=tmp_path / "document.DOCX",
            target_format="txt",
            output_dir=tmp_path,
        )
        
        assert task.source_extension == ".docx"


class TestConversionResult:
    """Test suite for ConversionResult."""

    def test_result_creation(self, tmp_path):
        """Test creating a conversion result."""
        output = tmp_path / "output.txt"
        
        result = ConversionResult(
            task_id="test-123",
            status=ConversionStatus.SUCCESS,
            output_path=output,
            processing_time_ms=1500.0,
        )
        
        assert result.task_id == "test-123"
        assert result.status == ConversionStatus.SUCCESS
        assert result.output_path == output
        assert result.processing_time_ms == 1500.0


class TestConversionWorker:
    """Test suite for ConversionWorker."""

    def test_initialization(self):
        """Test worker initialization."""
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_instance.discover = MagicMock()
            mock_instance.get_supported_extensions = MagicMock(return_value=[".docx"])
            mock_discovery.return_value = mock_instance
            
            worker = ConversionWorker(max_concurrent=2, timeout_seconds=60.0)
            
            assert worker.max_concurrent == 2
            assert worker.timeout_seconds == 60.0

    def test_can_convert_with_supported_extension(self):
        """Test can_convert returns True for supported extensions."""
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_instance.discover = MagicMock()
            mock_instance.has_capability = MagicMock(return_value=True)
            mock_discovery.return_value = mock_instance
            
            worker = ConversionWorker()
            
            with patch.object(worker, "EXTENSION_CAPABILITIES", {".docx": ToolCapability.DOCX_TO_MD}):
                result = worker.can_convert(Path("test.docx"))
                assert result is True

    def test_can_convert_with_unsupported_extension(self):
        """Test can_convert returns False for unsupported extensions."""
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_instance.discover = MagicMock()
            mock_discovery.return_value = mock_instance
            
            worker = ConversionWorker()
            
            result = worker.can_convert(Path("test.xyz"))
            assert result is False

    def test_get_supported_extensions(self):
        """Test get_supported_extensions returns list of extensions."""
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_instance.discover = MagicMock()
            mock_instance.has_capability = MagicMock(return_value=True)
            mock_discovery.return_value = mock_instance
            
            worker = ConversionWorker()
            
            with patch.object(worker, "EXTENSION_CAPABILITIES", {
                ".docx": ToolCapability.DOCX_TO_MD,
                ".pdf": ToolCapability.PDF_TO_TEXT,
            }):
                extensions = worker.get_supported_extensions()
                assert ".docx" in extensions
                assert ".pdf" in extensions

    @pytest.mark.asyncio
    async def test_submit_with_nonexistent_file(self, tmp_path):
        """Test submit handles non-existent files."""
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_instance.discover = MagicMock()
            mock_instance.has_capability = MagicMock(return_value=True)
            mock_instance.get_best_tool = MagicMock()
            mock_discovery.return_value = mock_instance
            
            worker = ConversionWorker()
            
            task = ConversionTask(
                task_id="test",
                source_path=tmp_path / "nonexistent.docx",
                target_format="txt",
                output_dir=tmp_path / "output",
            )
            
            result = await worker.submit(task)
            
            assert result.status == ConversionStatus.FAILED
            assert "does not exist" in result.error_message

    @pytest.mark.asyncio
    async def test_submit_with_unsupported_extension(self, tmp_path):
        """Test submit handles unsupported extensions."""
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_instance.discover = MagicMock()
            mock_instance.has_capability = MagicMock(return_value=False)
            mock_discovery.return_value = mock_instance
            
            worker = ConversionWorker()
            
            # Create a test file
            test_file = tmp_path / "test.xyz"
            test_file.write_text("test")
            
            task = ConversionTask(
                task_id="test",
                source_path=test_file,
                target_format="txt",
                output_dir=tmp_path / "output",
            )
            
            result = await worker.submit(task)
            
            assert result.status == ConversionStatus.FAILED
            assert "Unsupported" in result.error_message

    def test_set_callbacks(self):
        """Test setting progress and completion callbacks."""
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_instance.discover = MagicMock()
            mock_discovery.return_value = mock_instance
            
            worker = ConversionWorker()
            
            progress_callback = MagicMock()
            complete_callback = MagicMock()
            
            worker.set_callbacks(on_progress=progress_callback, on_complete=complete_callback)
            
            assert worker._on_progress == progress_callback
            assert worker._on_complete == complete_callback


class TestConversionWorkerConcurrency:
    """Test suite for worker concurrency features."""

    @pytest.mark.asyncio
    async def test_submit_batch(self, tmp_path):
        """Test batch submission of tasks."""
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_instance.discover = MagicMock()
            mock_instance.has_capability = MagicMock(return_value=False)
            mock_discovery.return_value = mock_instance
            
            worker = ConversionWorker()
            
            # Create test files
            for i in range(3):
                (tmp_path / f"test{i}.xyz").write_text("test")
            
            tasks = [
                ConversionTask(
                    task_id=f"test-{i}",
                    source_path=tmp_path / f"test{i}.xyz",
                    target_format="txt",
                    output_dir=tmp_path / "output",
                )
                for i in range(3)
            ]
            
            results = await worker.submit_batch(tasks)
            
            assert len(results) == 3
            for result in results:
                assert isinstance(result, ConversionResult)
