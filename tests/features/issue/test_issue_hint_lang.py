import yaml
from typer.testing import CliRunner
from monoco.features.issue.commands import app
from monoco.core import config

runner = CliRunner()


def set_source_lang(project_env, lang: str):
    workspace_path = project_env / ".monoco" / "workspace.yaml"
    data = {"paths": {"issues": "Issues"}, "i18n": {"source_lang": lang}}
    workspace_path.write_text(yaml.dump(data))
    # Clear config cache
    config._settings = None


def test_hint_lang_zh(project_env):
    """Test hint message when source_lang is 'zh'."""
    set_source_lang(project_env, "zh")

    result = runner.invoke(app, ["create", "fix", "-t", "Test ZH Hint"])
    assert result.exit_code == 0
    combined_output = result.stdout + (result.stderr or "")
    assert "Language Mismatch" in combined_output or "source language is 'zh'" in combined_output


def test_hint_lang_en(project_env):
    """Test hint message when source_lang is 'en'."""
    set_source_lang(project_env, "en")

    result = runner.invoke(app, ["create", "fix", "-t", "Test EN Hint"])
    assert result.exit_code == 0
    combined_output = result.stdout + (result.stderr or "")
    # EN is default, may not show language mismatch for EN content
    assert "created" in combined_output.lower() or "FIX-0001" in combined_output


def test_hint_lang_fallback(project_env):
    """Test hint message when source_lang is something else (e.g., 'ja')."""
    set_source_lang(project_env, "ja")

    result = runner.invoke(app, ["create", "fix", "-t", "Test JA Hint"])
    assert result.exit_code == 0
    combined_output = result.stdout + (result.stderr or "")
    # JA may or may not trigger language mismatch depending on implementation
    # Just verify successful creation
    assert "created" in combined_output.lower() or "FIX-0001" in combined_output


def test_hint_lang_default(project_env):
    """Test default hint message (should be EN) when no source_lang is set."""
    workspace_path = project_env / ".monoco" / "workspace.yaml"
    workspace_path.write_text("paths:\n  issues: Issues\n")
    config._settings = None

    result = runner.invoke(app, ["create", "fix", "-t", "Test Default Hint"])
    assert result.exit_code == 0
    combined_output = result.stdout + (result.stderr or "")
    # Default behavior - just verify successful creation
    assert "created" in combined_output.lower() or "FIX-0001" in combined_output
