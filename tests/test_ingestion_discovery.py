"""
Tests for Monoco Mailroom Environment Discovery.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from monoco.core.ingestion.discovery import (
    EnvironmentDiscovery,
    ConversionTool,
    ToolType,
    ToolCapability,
)


class TestEnvironmentDiscovery:
    """Test suite for EnvironmentDiscovery."""

    def test_initialization(self):
        """Test that discovery initializes correctly."""
        discovery = EnvironmentDiscovery()
        assert not discovery._discovered
        assert discovery._tools == {}

    def test_discover_returns_tools_dict(self):
        """Test that discover returns a dictionary of tools."""
        discovery = EnvironmentDiscovery()
        
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/soffice"
            
            with patch.object(discovery, "_get_version") as mock_version:
                mock_version.return_value = "LibreOffice 7.5"
                tools = discovery.discover()
        
        assert isinstance(tools, dict)
        assert ToolType.LIBREOFFICE in tools
        assert discovery._discovered

    def test_get_best_tool_returns_highest_priority(self):
        """Test that get_best_tool returns the highest priority tool."""
        discovery = EnvironmentDiscovery()
        
        # Manually set up tools
        tool1 = ConversionTool(
            name="Tool1",
            tool_type=ToolType.PANDOC,
            executable_path=Path("/usr/bin/tool1"),
            capabilities=[ToolCapability.DOCX_TO_MD],
            priority=50,
        )
        tool2 = ConversionTool(
            name="Tool2",
            tool_type=ToolType.LIBREOFFICE,
            executable_path=Path("/usr/bin/tool2"),
            capabilities=[ToolCapability.DOCX_TO_MD],
            priority=100,
        )
        
        discovery._tools = {
            ToolType.PANDOC: [tool1],
            ToolType.LIBREOFFICE: [tool2],
        }
        discovery._discovered = True
        
        best = discovery.get_best_tool(ToolCapability.DOCX_TO_MD)
        assert best is not None
        assert best.name == "Tool2"
        assert best.priority == 100

    def test_get_best_tool_returns_none_for_missing_capability(self):
        """Test that get_best_tool returns None when capability not available."""
        discovery = EnvironmentDiscovery()
        discovery._tools = {}
        discovery._discovered = True
        
        best = discovery.get_best_tool(ToolCapability.PDF_TO_HTML)
        assert best is None

    def test_has_capability(self):
        """Test has_capability method."""
        discovery = EnvironmentDiscovery()
        
        tool = ConversionTool(
            name="PDFTool",
            tool_type=ToolType.PDF2TEXT,
            executable_path=Path("/usr/bin/pdftotext"),
            capabilities=[ToolCapability.PDF_TO_TEXT],
            priority=100,
        )
        
        discovery._tools = {ToolType.PDF2TEXT: [tool]}
        discovery._discovered = True
        
        assert discovery.has_capability(ToolCapability.PDF_TO_TEXT)
        assert not discovery.has_capability(ToolCapability.DOCX_TO_MD)

    def test_get_capabilities_summary(self):
        """Test get_capabilities_summary returns all capabilities."""
        discovery = EnvironmentDiscovery()
        discovery._discovered = True
        discovery._tools = {}
        
        summary = discovery.get_capabilities_summary()
        
        assert isinstance(summary, dict)
        for cap in ToolCapability:
            assert cap.value in summary
            assert summary[cap.value] is False  # No tools configured


class TestConversionTool:
    """Test suite for ConversionTool dataclass."""

    def test_tool_creation(self):
        """Test creating a ConversionTool."""
        tool = ConversionTool(
            name="TestTool",
            tool_type=ToolType.LIBREOFFICE,
            executable_path=Path("/usr/bin/test"),
            version="1.0",
            capabilities=[ToolCapability.DOCX_TO_TEXT],
            priority=50,
        )
        
        assert tool.name == "TestTool"
        assert tool.tool_type == ToolType.LIBREOFFICE
        assert tool.version == "1.0"
        assert len(tool.capabilities) == 1

    def test_is_available_checks_executable(self, tmp_path):
        """Test is_available checks if executable exists."""
        # Create a temporary executable file
        exe_path = tmp_path / "test_exe"
        exe_path.write_text("#!/bin/bash\necho test")
        exe_path.chmod(0o755)
        
        tool = ConversionTool(
            name="Test",
            tool_type=ToolType.CUSTOM,
            executable_path=exe_path,
        )
        
        assert tool.is_available()
        
        # Test non-existent file
        tool2 = ConversionTool(
            name="Test2",
            tool_type=ToolType.CUSTOM,
            executable_path=Path("/nonexistent/path"),
        )
        assert not tool2.is_available()


class TestToolType:
    """Test suite for ToolType enum."""

    def test_tool_type_values(self):
        """Test that ToolType has expected values."""
        assert ToolType.LIBREOFFICE.value == "libreoffice"
        assert ToolType.PANDOC.value == "pandoc"
        assert ToolType.PDF2TEXT.value == "pdf2text"
        assert ToolType.PDFTOHTML.value == "pdftohtml"
        assert ToolType.CUSTOM.value == "custom"


class TestToolCapability:
    """Test suite for ToolCapability enum."""

    def test_capability_values(self):
        """Test that ToolCapability has expected values."""
        assert ToolCapability.DOCX_TO_TEXT.value == "docx_to_text"
        assert ToolCapability.DOCX_TO_MD.value == "docx_to_md"
        assert ToolCapability.PDF_TO_TEXT.value == "pdf_to_text"
