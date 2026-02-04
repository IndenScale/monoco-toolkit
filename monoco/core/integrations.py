"""
Core Integration Registry for Agent Frameworks.

This module provides a centralized registry for managing integrations with various
agent frameworks (Cursor, Claude, Gemini, Qwen, Antigravity, etc.).

It defines the standard structure for framework integrations and provides utilities
for detection and configuration.
"""

from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AgentIntegration(BaseModel):
    """
    Configuration for a single agent framework integration.

    Attributes:
        key: Unique identifier for the framework (e.g., 'cursor', 'gemini')
        name: Human-readable name of the framework
        system_prompt_file: Path to the system prompt/rules file relative to project root
        skill_root_dir: Path to the skills directory relative to project root
        bin_name: Optional name of the binary to check for (e.g., 'cursor', 'gemini')
        version_cmd: Optional command to check version (e.g., '--version')
        enabled: Whether this integration is active (default: True)
    """

    key: str = Field(..., description="Unique framework identifier")
    name: str = Field(..., description="Human-readable framework name")
    system_prompt_file: str = Field(
        ..., description="Path to system prompt file (relative to project root)"
    )
    skill_root_dir: str = Field(
        ..., description="Path to skills directory (relative to project root)"
    )
    bin_name: Optional[str] = Field(
        None, description="Binary name to check for availability"
    )
    version_cmd: Optional[str] = Field(None, description="Command to check version")
    enabled: bool = Field(
        default=True, description="Whether this integration is active"
    )

    def check_health(self) -> "AgentProviderHealth":
        """
        Check health of this integration.
        """
        import shutil
        import subprocess
        import time

        if not self.bin_name:
            return AgentProviderHealth(
                available=True
            )  # If no binary required, assume ok

        bin_path = shutil.which(self.bin_name)
        if not bin_path:
            return AgentProviderHealth(
                available=False, error=f"Binary '{self.bin_name}' not found in PATH"
            )

        if not self.version_cmd:
            return AgentProviderHealth(available=True, path=bin_path)

        start_time = time.time()
        try:
            # We use a shortcut to check version cmd
            # Some tools might need e.g. 'cursor --version'
            subprocess.run(
                [self.bin_name] + self.version_cmd.split(),
                check=True,
                capture_output=True,
                timeout=5,
            )
            latency = int((time.time() - start_time) * 1000)
            return AgentProviderHealth(
                available=True, path=bin_path, latency_ms=latency
            )
        except Exception as e:
            return AgentProviderHealth(available=False, path=bin_path, error=str(e))


class AgentProviderHealth(BaseModel):
    """Health check result for an agent provider."""

    available: bool
    path: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None


# Default Integration Registry
DEFAULT_INTEGRATIONS: Dict[str, AgentIntegration] = {
    "claude": AgentIntegration(
        key="claude",
        name="Claude Code",
        system_prompt_file="CLAUDE.md",
        skill_root_dir=".claude/skills/",
        bin_name="claude",
        version_cmd="--version",
    ),
    "gemini": AgentIntegration(
        key="gemini",
        name="Gemini CLI",
        system_prompt_file="GEMINI.md",
        skill_root_dir=".gemini/skills/",
        bin_name="gemini",
        version_cmd="--version",
    ),
    "agent": AgentIntegration(
        key="agent",
        name="Generic Agent",
        system_prompt_file="AGENTS.md",
        skill_root_dir=".agent/skills/",
    ),
}


def get_integration(
    name: str, config_overrides: Optional[Dict[str, AgentIntegration]] = None
) -> Optional[AgentIntegration]:
    """
    Get an agent integration by name.

    Args:
        name: The framework key (e.g., 'cursor', 'gemini')
        config_overrides: Optional user-defined integrations from config

    Returns:
        AgentIntegration if found, None otherwise

    Priority:
        1. User config overrides
        2. Default registry
    """
    # Check user overrides first
    if config_overrides and name in config_overrides:
        return config_overrides[name]

    # Fall back to defaults
    return DEFAULT_INTEGRATIONS.get(name)


def get_all_integrations(
    config_overrides: Optional[Dict[str, AgentIntegration]] = None,
    enabled_only: bool = True,
) -> Dict[str, AgentIntegration]:
    """
    Get all available integrations.

    Args:
        config_overrides: Optional user-defined integrations from config
        enabled_only: If True, only return enabled integrations

    Returns:
        Dictionary of all integrations (merged defaults + overrides)
    """
    # Start with defaults
    all_integrations = DEFAULT_INTEGRATIONS.copy()

    # Merge user overrides
    if config_overrides:
        all_integrations.update(config_overrides)

    # Filter by enabled status if requested
    if enabled_only:
        return {k: v for k, v in all_integrations.items() if v.enabled}

    return all_integrations


def detect_frameworks(root: Path) -> List[str]:
    """
    Auto-detect which agent frameworks are present in the project.

    Detection is based on the existence of characteristic files/directories
    for each framework.

    Args:
        root: Project root directory

    Returns:
        List of detected framework keys (e.g., ['cursor', 'gemini'])

    Example:
        >>> root = Path("/path/to/project")
        >>> frameworks = detect_frameworks(root)
        >>> print(frameworks)
        ['cursor', 'gemini']
    """
    detected = []

    for key, integration in DEFAULT_INTEGRATIONS.items():
        # Check if system prompt file exists
        prompt_file = root / integration.system_prompt_file

        # Check if skill directory exists
        skill_dir = root / integration.skill_root_dir

        # Consider framework present if either exists
        if prompt_file.exists() or skill_dir.exists():
            detected.append(key)

    return detected


def get_active_integrations(
    root: Path,
    config_overrides: Optional[Dict[str, AgentIntegration]] = None,
    auto_detect: bool = True,
) -> Dict[str, AgentIntegration]:
    """
    Get integrations that are both enabled and detected in the project.

    Args:
        root: Project root directory
        config_overrides: Optional user-defined integrations from config
        auto_detect: If True, only return integrations detected in the project

    Returns:
        Dictionary of active integrations
    """
    all_integrations = get_all_integrations(config_overrides, enabled_only=True)

    if not auto_detect:
        return all_integrations

    # Filter by detection
    detected_keys = detect_frameworks(root)
    return {k: v for k, v in all_integrations.items() if k in detected_keys}
