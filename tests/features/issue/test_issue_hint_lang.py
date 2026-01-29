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
    assert "Agent Hint: 请使用中文填写 Issue 内容。" in result.stdout


def test_hint_lang_en(project_env):
    """Test hint message when source_lang is 'en'."""
    set_source_lang(project_env, "en")

    result = runner.invoke(app, ["create", "fix", "-t", "Test EN Hint"])
    assert result.exit_code == 0
    assert "Agent Hint: Please fill the ticket content in English." in result.stdout


def test_hint_lang_fallback(project_env):
    """Test hint message when source_lang is something else (e.g., 'ja')."""
    set_source_lang(project_env, "ja")

    result = runner.invoke(app, ["create", "fix", "-t", "Test JA Hint"])
    assert result.exit_code == 0
    assert "Agent Hint: Please fill the ticket content in JA." in result.stdout


def test_hint_lang_default(project_env):
    """Test default hint message (should be EN) when no source_lang is set."""
    workspace_path = project_env / ".monoco" / "workspace.yaml"
    workspace_path.write_text("paths:\n  issues: Issues\n")
    config._settings = None

    result = runner.invoke(app, ["create", "fix", "-t", "Test Default Hint"])
    assert result.exit_code == 0
    assert "Agent Hint: Please fill the ticket content in English." in result.stdout
