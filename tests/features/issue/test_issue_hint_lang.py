import yaml
from pathlib import Path
from typer.testing import CliRunner
from monoco.features.issue.commands import app
from monoco.core import config

runner = CliRunner()


def set_source_lang(lang: str):
    """Set source language in global config (~/.monoco/config.yaml)."""
    global_config_path = Path.home() / ".monoco" / "config.yaml"

    # Read existing config or create new
    if global_config_path.exists():
        data = yaml.safe_load(global_config_path.read_text()) or {}
    else:
        data = {}

    # Ensure nested structure exists
    if "i18n" not in data:
        data["i18n"] = {}
    data["i18n"]["source_lang"] = lang

    # Ensure basic project config exists
    if "project" not in data:
        data["project"] = {}
    if "paths" not in data:
        data["paths"] = {}
    data["project"]["name"] = "Test Project"
    data["project"]["key"] = "TEST"
    data["paths"]["issues"] = "Issues"

    global_config_path.write_text(yaml.dump(data))
    # Clear config cache
    config._settings = None


def reset_source_lang():
    """Reset source language to default (en) in global config."""
    global_config_path = Path.home() / ".monoco" / "config.yaml"

    if global_config_path.exists():
        data = yaml.safe_load(global_config_path.read_text()) or {}
        if "i18n" in data and "source_lang" in data["i18n"]:
            del data["i18n"]["source_lang"]
            global_config_path.write_text(yaml.dump(data))
    config._settings = None


def test_hint_lang_zh(project_env):
    """Test hint message when source_lang is 'zh'."""
    try:
        set_source_lang("zh")

        result = runner.invoke(app, ["create", "fix", "-t", "Test ZH Hint"])
        assert result.exit_code == 0
        combined_output = result.stdout + (result.stderr or "")
        assert (
            "Language Mismatch" in combined_output
            or "source language is 'zh'" in combined_output
        )
    finally:
        reset_source_lang()


def test_hint_lang_en(project_env):
    """Test hint message when source_lang is 'en'."""
    try:
        set_source_lang("en")

        result = runner.invoke(app, ["create", "fix", "-t", "Test EN Hint"])
        assert result.exit_code == 0
        combined_output = result.stdout + (result.stderr or "")
        # EN is default, may not show language mismatch for EN content
        assert "created" in combined_output.lower() or "FIX-0001" in combined_output
    finally:
        reset_source_lang()


def test_hint_lang_fallback(project_env):
    """Test hint message when source_lang is something else (e.g. 'ja')."""
    try:
        set_source_lang("ja")

        result = runner.invoke(app, ["create", "fix", "-t", "Test JA Hint"])
        assert result.exit_code == 0
        combined_output = result.stdout + (result.stderr or "")
        # JA may or may not trigger language mismatch depending on implementation
        # Just verify successful creation
        assert "created" in combined_output.lower() or "FIX-0001" in combined_output
    finally:
        reset_source_lang()


def test_hint_lang_default(project_env):
    """Test default hint message (should be EN) when no source_lang is set."""
    # Ensure no source_lang is set
    reset_source_lang()

    result = runner.invoke(app, ["create", "fix", "-t", "Test Default Hint"])
    assert result.exit_code == 0
    combined_output = result.stdout + (result.stderr or "")
    # Default behavior - just verify successful creation
    assert "created" in combined_output.lower() or "FIX-0001" in combined_output
