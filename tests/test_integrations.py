"""
Tests for Core Integration Registry.
"""

import pytest
from pathlib import Path
from monoco.core.integrations import (
    AgentIntegration,
    DEFAULT_INTEGRATIONS,
    get_integration,
    get_all_integrations,
    detect_frameworks,
    get_active_integrations,
)


def test_default_integrations_structure():
    """Test that all default integrations have required fields."""
    assert len(DEFAULT_INTEGRATIONS) >= 5  # cursor, claude, gemini, qwen, agent
    
    for key, integration in DEFAULT_INTEGRATIONS.items():
        assert integration.key == key
        assert integration.name
        assert integration.system_prompt_file
        assert integration.skill_root_dir
        assert integration.enabled is True


def test_get_integration_default():
    """Test getting integration from defaults."""
    cursor = get_integration("cursor")
    assert cursor is not None
    assert cursor.key == "cursor"
    assert cursor.system_prompt_file == ".cursorrules"
    assert cursor.skill_root_dir == ".cursor/skills/"


def test_get_integration_with_override():
    """Test that config overrides take precedence."""
    custom_cursor = AgentIntegration(
        key="cursor",
        name="Custom Cursor",
        system_prompt_file="custom.rules",
        skill_root_dir="custom/skills/",
    )
    
    overrides = {"cursor": custom_cursor}
    result = get_integration("cursor", overrides)
    
    assert result.name == "Custom Cursor"
    assert result.system_prompt_file == "custom.rules"


def test_get_integration_not_found():
    """Test getting non-existent integration."""
    result = get_integration("nonexistent")
    assert result is None


def test_get_all_integrations_default():
    """Test getting all integrations without overrides."""
    all_integrations = get_all_integrations()
    assert len(all_integrations) >= 5
    assert "cursor" in all_integrations
    assert "gemini" in all_integrations


def test_get_all_integrations_with_overrides():
    """Test merging default and custom integrations."""
    custom = AgentIntegration(
        key="custom",
        name="Custom Framework",
        system_prompt_file="CUSTOM.md",
        skill_root_dir=".custom/skills/",
    )
    
    overrides = {"custom": custom}
    all_integrations = get_all_integrations(overrides)
    
    assert "custom" in all_integrations
    assert "cursor" in all_integrations  # Defaults still present


def test_get_all_integrations_enabled_filter():
    """Test filtering by enabled status."""
    disabled = AgentIntegration(
        key="disabled",
        name="Disabled Framework",
        system_prompt_file="DISABLED.md",
        skill_root_dir=".disabled/skills/",
        enabled=False,
    )
    
    overrides = {"disabled": disabled}
    
    # With enabled_only=True (default)
    enabled_integrations = get_all_integrations(overrides, enabled_only=True)
    assert "disabled" not in enabled_integrations
    
    # With enabled_only=False
    all_integrations = get_all_integrations(overrides, enabled_only=False)
    assert "disabled" in all_integrations


def test_detect_frameworks(tmp_path):
    """Test framework detection based on file existence."""
    # Create characteristic files
    (tmp_path / ".cursorrules").touch()
    (tmp_path / "GEMINI.md").touch()
    (tmp_path / ".qwen" / "skills").mkdir(parents=True)
    
    detected = detect_frameworks(tmp_path)
    
    assert "cursor" in detected
    assert "gemini" in detected
    assert "qwen" in detected
    assert "claude" not in detected  # No Claude files


def test_detect_frameworks_empty(tmp_path):
    """Test detection in empty directory."""
    detected = detect_frameworks(tmp_path)
    assert detected == []


def test_get_active_integrations(tmp_path):
    """Test getting active integrations with auto-detection."""
    # Create some framework files
    (tmp_path / ".cursorrules").touch()
    (tmp_path / "GEMINI.md").touch()
    
    # Get active integrations (auto-detect enabled)
    active = get_active_integrations(tmp_path, auto_detect=True)
    
    assert "cursor" in active
    assert "gemini" in active
    assert "claude" not in active  # Not detected
    
    # Get all enabled integrations (auto-detect disabled)
    all_enabled = get_active_integrations(tmp_path, auto_detect=False)
    assert len(all_enabled) >= 5  # All defaults


def test_get_active_integrations_with_overrides(tmp_path):
    """Test active integrations with custom config."""
    (tmp_path / ".cursorrules").touch()
    
    # Override cursor integration
    custom_cursor = AgentIntegration(
        key="cursor",
        name="Custom Cursor",
        system_prompt_file=".cursorrules",
        skill_root_dir=".cursor/skills/",
    )
    
    overrides = {"cursor": custom_cursor}
    active = get_active_integrations(tmp_path, overrides, auto_detect=True)
    
    assert "cursor" in active
    assert active["cursor"].name == "Custom Cursor"
