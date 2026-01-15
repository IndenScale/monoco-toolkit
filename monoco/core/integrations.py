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
        enabled: Whether this integration is active (default: True)
    """
    key: str = Field(..., description="Unique framework identifier")
    name: str = Field(..., description="Human-readable framework name")
    system_prompt_file: str = Field(..., description="Path to system prompt file (relative to project root)")
    skill_root_dir: str = Field(..., description="Path to skills directory (relative to project root)")
    enabled: bool = Field(default=True, description="Whether this integration is active")


# Default Integration Registry
DEFAULT_INTEGRATIONS: Dict[str, AgentIntegration] = {
    "cursor": AgentIntegration(
        key="cursor",
        name="Cursor",
        system_prompt_file=".cursorrules",
        skill_root_dir=".cursor/skills/",
    ),
    "claude": AgentIntegration(
        key="claude",
        name="Claude Code",
        system_prompt_file="CLAUDE.md",
        skill_root_dir=".claude/skills/",
    ),
    "gemini": AgentIntegration(
        key="gemini",
        name="Gemini CLI",
        system_prompt_file="GEMINI.md",
        skill_root_dir=".gemini/skills/",
    ),
    "qwen": AgentIntegration(
        key="qwen",
        name="Qwen Code",
        system_prompt_file="QWEN.md",
        skill_root_dir=".qwen/skills/",
    ),
    "agent": AgentIntegration(
        key="agent",
        name="Antigravity",
        system_prompt_file="GEMINI.md",
        skill_root_dir=".agent/skills/",
    ),
}


def get_integration(
    name: str,
    config_overrides: Optional[Dict[str, AgentIntegration]] = None
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
    enabled_only: bool = True
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
    auto_detect: bool = True
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
