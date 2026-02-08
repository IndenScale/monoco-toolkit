import pytest
import json
import os
from typer.testing import CliRunner
from monoco.features.issue.commands import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def clean_env():
    """每个测试前清理环境，避免 AGENT_FLAG 污染。"""
    if "AGENT_FLAG" in os.environ:
        del os.environ["AGENT_FLAG"]
    yield
    if "AGENT_FLAG" in os.environ:
        del os.environ["AGENT_FLAG"]


def test_cli_create_issue(project_env):
    """测试 'monoco issue create' 命令。"""
    # 首先创建一个 Epic 作为 Parent
    runner.invoke(app, ["create", "epic", "-t", "Parent Epic"])

    result = runner.invoke(
        app, ["create", "feature", "-t", "CLI Test", "-p", "EPIC-0001"]
    )
    assert result.exit_code == 0
    assert "'id': 'FEAT-0001'" in result.stdout or '"id":"FEAT-0001"' in result.stdout or "FEAT-0001" in result.stdout
    assert "'status': 'created'" in result.stdout or '"status":"created"' in result.stdout or "created" in result.stdout

    # 物理验证文件系统
    issues_dir = project_env / "Issues"
    feature_file = issues_dir / "Features" / "open" / "FEAT-0001-cli-test.md"
    assert feature_file.exists()


def test_cli_list_issues(project_env):
    """测试 'monoco issue list' 命令。"""
    # Epic
    runner.invoke(app, ["create", "epic", "-t", "Parent Epic"])
    # Fix
    runner.invoke(app, ["create", "fix", "-t", "Bug 1", "-p", "EPIC-0001"])
    # Chore
    runner.invoke(app, ["create", "chore", "-t", "Cleanup", "-p", "EPIC-0001"])

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "FIX-0001" in result.stdout
    assert "CHORE-0001" in result.stdout


def test_cli_backlog_push_pull(project_env):
    """测试 backlog 推送和拉取命令。"""
    runner.invoke(app, ["create", "epic", "-t", "Parent Epic"])
    runner.invoke(app, ["create", "feature", "-t", "To Backlog", "-p", "EPIC-0001"])

    # Push
    result = runner.invoke(app, ["backlog", "push", "FEAT-0001"])
    assert result.exit_code == 0
    assert (
        project_env / "Issues" / "Features" / "backlog" / "FEAT-0001-to-backlog.md"
    ).exists()

    # Pull
    result = runner.invoke(app, ["backlog", "pull", "FEAT-0001"])
    assert result.exit_code == 0
    assert (
        project_env / "Issues" / "Features" / "open" / "FEAT-0001-to-backlog.md"
    ).exists()


def test_cli_agent_output(project_env):
    """测试 --json 参数输出。"""
    # 创建任务
    runner.invoke(app, ["create", "epic", "-t", "Agent Task"])

    # 列出任务
    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0

    # 尝试解析 JSON
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert data[0]["id"] == "EPIC-0001"
    assert data[0]["title"] == "Agent Task"


def test_cli_error_handling(project_env):
    """测试错误处理。"""
    # 尝试打开不存在的任务
    result = runner.invoke(app, ["open", "FIX-9999"])
    assert result.exit_code == 1
    # Error messages go to stderr or stdout depending on implementation
    combined_output = result.stdout + (result.stderr or "")
    assert "Error:" in combined_output or "not found" in combined_output.lower()


def test_cli_parent_validation(project_env):
    """测试父任务验证。"""
    # 尝试创建指向不存在父任务的 Feature
    result = runner.invoke(
        app, ["create", "feature", "-t", "Bad Parent", "-p", "EPIC-9999"]
    )
    assert result.exit_code == 1
    combined_output = result.stdout + (result.stderr or "")
    assert "Parent issue EPIC-9999 not found" in combined_output
