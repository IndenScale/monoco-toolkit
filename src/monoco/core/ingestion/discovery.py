"""
Environment Discovery Module for Monoco Mailroom.

Automatically detects available document conversion tools in the system,
including LibreOffice (soffice), Pandoc, and PDF processing engines.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class ToolType(str, Enum):
    """Types of conversion tools supported."""
    LIBREOFFICE = "libreoffice"
    PANDOC = "pandoc"
    PDF2TEXT = "pdf2text"
    PDFTOHTML = "pdftohtml"
    CUSTOM = "custom"


class ToolCapability(str, Enum):
    """Capabilities of conversion tools."""
    DOCX_TO_TEXT = "docx_to_text"
    DOCX_TO_MD = "docx_to_md"
    PDF_TO_TEXT = "pdf_to_text"
    PDF_TO_HTML = "pdf_to_html"
    ODT_TO_TEXT = "odt_to_text"
    XLSX_TO_CSV = "xlsx_to_csv"
    PPTX_TO_TEXT = "pptx_to_text"


@dataclass
class ConversionTool:
    """Represents a discovered conversion tool."""
    name: str
    tool_type: ToolType
    executable_path: Path
    version: str = "unknown"
    capabilities: list[ToolCapability] = field(default_factory=list)
    priority: int = 0  # Higher = preferred

    def is_available(self) -> bool:
        """Check if the tool executable exists and is runnable."""
        return self.executable_path.exists() and os.access(self.executable_path, os.X_OK)


class EnvironmentDiscovery:
    """
    Discovers and manages document conversion tools in the system.
    
    Automatically detects:
    - LibreOffice (soffice) for Office document conversion
    - Pandoc for markdown/text conversion
    - PDF utilities (pdftotext, pdftohtml)
    """

    # Known executable names to search for
    LIBREOFFICE_BINARIES = ["soffice", "libreoffice", "soffice.bin"]
    PANDOC_BINARIES = ["pandoc"]
    PDF_TOOLS = ["pdftotext", "pdftohtml", "pdf2txt.py"]

    def __init__(self):
        self._tools: dict[ToolType, list[ConversionTool]] = {}
        self._discovered = False

    def discover(self, force: bool = False) -> dict[ToolType, list[ConversionTool]]:
        """
        Discover all available conversion tools.
        
        Args:
            force: Force re-discovery even if already done
            
        Returns:
            Dictionary mapping tool types to lists of discovered tools
        """
        if self._discovered and not force:
            return self._tools

        self._tools = {
            ToolType.LIBREOFFICE: self._discover_libreoffice(),
            ToolType.PANDOC: self._discover_pandoc(),
            ToolType.PDF2TEXT: self._discover_pdf_tools(),
        }
        
        self._discovered = True
        return self._tools

    def _find_executable(self, names: list[str]) -> Optional[Path]:
        """Find the first available executable from a list of names."""
        for name in names:
            path = shutil.which(name)
            if path:
                return Path(path).resolve()
        return None

    def _get_version(self, executable: Path, version_arg: str = "--version") -> str:
        """Get version string from an executable."""
        try:
            result = subprocess.run(
                [str(executable), version_arg],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            # Extract version from first line of output
            output = result.stdout or result.stderr
            if output:
                first_line = output.strip().split("\n")[0]
                return first_line
        except (subprocess.TimeoutExpired, OSError, ValueError):
            pass
        return "unknown"

    def _discover_libreoffice(self) -> list[ConversionTool]:
        """Discover LibreOffice installation."""
        tools = []
        executable = self._find_executable(self.LIBREOFFICE_BINARIES)
        
        if executable:
            version = self._get_version(executable)
            tools.append(ConversionTool(
                name="LibreOffice",
                tool_type=ToolType.LIBREOFFICE,
                executable_path=executable,
                version=version,
                capabilities=[
                    ToolCapability.DOCX_TO_TEXT,
                    ToolCapability.DOCX_TO_MD,
                    ToolCapability.ODT_TO_TEXT,
                    ToolCapability.XLSX_TO_CSV,
                    ToolCapability.PPTX_TO_TEXT,
                ],
                priority=100,  # High priority for Office docs
            ))
        
        return tools

    def _discover_pandoc(self) -> list[ConversionTool]:
        """Discover Pandoc installation."""
        tools = []
        executable = self._find_executable(self.PANDOC_BINARIES)
        
        if executable:
            version = self._get_version(executable)
            tools.append(ConversionTool(
                name="Pandoc",
                tool_type=ToolType.PANDOC,
                executable_path=executable,
                version=version,
                capabilities=[
                    ToolCapability.DOCX_TO_MD,
                    ToolCapability.DOCX_TO_TEXT,
                    ToolCapability.ODT_TO_TEXT,
                ],
                priority=90,
            ))
        
        return tools

    def _discover_pdf_tools(self) -> list[ConversionTool]:
        """Discover PDF conversion tools."""
        tools = []
        
        # pdftotext (from poppler-utils)
        pdftotext = self._find_executable(["pdftotext"])
        if pdftotext:
            version = self._get_version(pdftotext, "-v")
            tools.append(ConversionTool(
                name="pdftotext",
                tool_type=ToolType.PDF2TEXT,
                executable_path=pdftotext,
                version=version,
                capabilities=[ToolCapability.PDF_TO_TEXT],
                priority=100,
            ))
        
        # pdftohtml
        pdftohtml = self._find_executable(["pdftohtml"])
        if pdftohtml:
            version = self._get_version(pdftohtml, "-v")
            tools.append(ConversionTool(
                name="pdftohtml",
                tool_type=ToolType.PDFTOHTML,
                executable_path=pdftohtml,
                version=version,
                capabilities=[ToolCapability.PDF_TO_HTML],
                priority=80,
            ))
        
        return tools

    def get_best_tool(self, capability: ToolCapability) -> Optional[ConversionTool]:
        """
        Get the best available tool for a specific capability.
        
        Args:
            capability: The required conversion capability
            
        Returns:
            Best matching ConversionTool or None
        """
        if not self._discovered:
            self.discover()

        candidates = []
        for tool_list in self._tools.values():
            for tool in tool_list:
                if capability in tool.capabilities:
                    candidates.append(tool)

        if not candidates:
            return None

        # Sort by priority (highest first)
        candidates.sort(key=lambda t: t.priority, reverse=True)
        return candidates[0]

    def get_all_tools(self) -> list[ConversionTool]:
        """Get all discovered tools."""
        if not self._discovered:
            self.discover()
        
        all_tools = []
        for tool_list in self._tools.values():
            all_tools.extend(tool_list)
        return all_tools

    def has_capability(self, capability: ToolCapability) -> bool:
        """Check if any tool supports the given capability."""
        return self.get_best_tool(capability) is not None

    def get_capabilities_summary(self) -> dict[str, bool]:
        """Get a summary of available capabilities."""
        return {
            cap.value: self.has_capability(cap)
            for cap in ToolCapability
        }


# Import os here to avoid issues with dataclass
import os
