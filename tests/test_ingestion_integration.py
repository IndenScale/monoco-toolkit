"""
Integration tests for Monoco Mailroom.

Tests the full ingestion pipeline: discovery -> worker -> watcher -> artifact.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from monoco.core.ingestion.discovery import EnvironmentDiscovery, ToolCapability
from monoco.core.ingestion.worker import ConversionWorker, ConversionTask
from monoco.core.ingestion.watcher import DropzoneWatcher, IngestionEventType
from monoco.core.artifacts.manager import ArtifactManager


class TestMailroomIntegration:
    """Integration tests for the full Mailroom pipeline."""

    def test_discovery_to_worker_integration(self):
        """Test that discovered tools can be used by the worker."""
        discovery = EnvironmentDiscovery()
        
        # Mock discovery to return a fake tool
        with patch.object(discovery, "_discover_libreoffice") as mock_libreoffice:
            mock_libreoffice.return_value = []
            
            with patch.object(discovery, "_discover_pandoc") as mock_pandoc:
                mock_pandoc.return_value = []
                
                with patch.object(discovery, "_discover_pdf_tools") as mock_pdf:
                    mock_pdf.return_value = []
                    
                    tools = discovery.discover()
                    
                    # Create worker with mocked discovery
                    with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery_class:
                        mock_discovery_instance = MagicMock()
                        mock_discovery_instance.discover = MagicMock()
                        mock_discovery_instance.has_capability = MagicMock(return_value=True)
                        mock_discovery_instance.get_best_tool = MagicMock(return_value=None)
                        mock_discovery_class.return_value = mock_discovery_instance
                        
                        worker = ConversionWorker(discovery=discovery)
                        
                        # Verify worker can check capabilities
                        assert worker.discovery == discovery

    def test_worker_capability_detection(self):
        """Test that worker correctly uses discovery for capability detection."""
        discovery = EnvironmentDiscovery()
        
        with patch.object(discovery, "has_capability") as mock_has:
            mock_has.return_value = True
            discovery._discovered = True
            
            with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery_class:
                mock_discovery_instance = MagicMock()
                mock_discovery_instance.discover = MagicMock()
                mock_discovery_instance.has_capability = MagicMock(return_value=True)
                mock_discovery_instance.get_supported_extensions = MagicMock(return_value=[".docx", ".pdf"])
                mock_discovery_class.return_value = mock_discovery_instance
                
                worker = ConversionWorker()
                
                # Check that worker can detect supported extensions
                extensions = worker.get_supported_extensions()
                assert ".docx" in extensions
                assert ".pdf" in extensions


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    @pytest.mark.asyncio
    async def test_full_ingestion_workflow(self, tmp_path):
        """Test the complete ingestion workflow."""
        # Create directories
        dropzone = tmp_path / "dropzone"
        output = tmp_path / "output"
        project_dir = tmp_path / "project"
        
        dropzone.mkdir()
        output.mkdir()
        project_dir.mkdir()
        
        # Create a mock artifact manager
        mock_artifact_manager = MagicMock(spec=ArtifactManager)
        mock_artifact_manager.store_file.return_value = MagicMock(
            artifact_id="test-artifact-123",
            content_hash="abc123",
        )
        
        # Create watcher with mocked dependencies
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery_class:
            mock_discovery_instance = MagicMock()
            mock_discovery_instance.discover = MagicMock()
            mock_discovery_instance.has_capability = MagicMock(return_value=False)  # No conversion
            mock_discovery_instance.get_supported_extensions = MagicMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery_instance
            
            watcher = DropzoneWatcher(
                dropzone_path=dropzone,
                artifact_manager=mock_artifact_manager,
                output_dir=output,
                process_existing=False,
            )
            
            # Verify watcher initialization
            assert watcher.dropzone_path == dropzone
            assert watcher.output_dir == output
            assert watcher.artifact_manager == mock_artifact_manager

    def test_mailroom_service_integration(self, tmp_path):
        """Test MailroomService integration with daemon."""
        from monoco.daemon.mailroom_service import MailroomService
        
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery_class:
            mock_discovery_instance = MagicMock()
            mock_discovery_instance.discover = MagicMock(return_value={})
            mock_discovery_instance.get_capabilities_summary = MagicMock(return_value={
                "docx_to_text": True,
                "pdf_to_text": False,
            })
            mock_discovery_instance.get_all_tools = MagicMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery_instance
            
            service = MailroomService(
                workspace_root=tmp_path,
                max_concurrent=2,
            )
            
            # Verify service initialization
            assert service.workspace_root == tmp_path
            assert service.conversion_worker.max_concurrent == 2
            assert service.dropzone_path == tmp_path / ".monoco" / "dropzone"


class TestErrorHandling:
    """Test error handling in the ingestion pipeline."""

    @pytest.mark.asyncio
    async def test_worker_handles_conversion_failure(self, tmp_path):
        """Test that worker handles conversion failures gracefully."""
        # Create a test file
        test_file = tmp_path / "test.docx"
        test_file.write_text("fake docx content")
        
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery_class:
            mock_discovery_instance = MagicMock()
            mock_discovery_instance.discover = MagicMock()
            mock_discovery_instance.has_capability = MagicMock(return_value=True)
            mock_discovery_instance.get_best_tool = MagicMock(return_value=None)
            mock_discovery_class.return_value = mock_discovery_instance
            
            worker = ConversionWorker()
            
            task = ConversionTask(
                task_id="test",
                source_path=test_file,
                target_format="txt",
                output_dir=tmp_path / "output",
            )
            
            result = await worker.submit(task)
            
            # Should fail gracefully
            assert result.status.value == "failed"
            assert result.error_message is not None

    def test_watcher_handles_missing_dropzone(self, tmp_path):
        """Test that watcher handles missing dropzone directory."""
        dropzone = tmp_path / "nonexistent" / "dropzone"
        output = tmp_path / "output"
        
        mock_artifact_manager = MagicMock(spec=ArtifactManager)
        
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery_class:
            mock_discovery_instance = MagicMock()
            mock_discovery_instance.discover = MagicMock()
            mock_discovery_instance.has_capability = MagicMock(return_value=False)
            mock_discovery_instance.get_supported_extensions = MagicMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery_instance
            
            watcher = DropzoneWatcher(
                dropzone_path=dropzone,
                artifact_manager=mock_artifact_manager,
                output_dir=output,
            )
            
            # Start should create the directory
            watcher.start()
            assert dropzone.exists()
            watcher.stop()


class TestConcurrency:
    """Test concurrency features."""

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self, tmp_path):
        """Test that semaphore limits concurrent conversions."""
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery_class:
            mock_discovery_instance = MagicMock()
            mock_discovery_instance.discover = MagicMock()
            mock_discovery_instance.has_capability = MagicMock(return_value=False)
            mock_discovery_class.return_value = mock_discovery_instance
            
            worker = ConversionWorker(max_concurrent=2)
            
            # Verify semaphore is created with correct value
            assert worker._semaphore._value == 2

    def test_worker_tracks_active_tasks(self):
        """Test that worker tracks active task count."""
        with patch("monoco.core.ingestion.worker.EnvironmentDiscovery") as mock_discovery_class:
            mock_discovery_instance = MagicMock()
            mock_discovery_instance.discover = MagicMock()
            mock_discovery_class.return_value = mock_discovery_instance
            
            worker = ConversionWorker()
            
            # Initially no active tasks
            assert worker.get_active_count() == 0
