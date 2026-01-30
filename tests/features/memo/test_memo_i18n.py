import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from monoco.features.memo.cli import app
from monoco.core.config import MonocoConfig, I18nConfig, PathsConfig

runner = CliRunner()


@pytest.fixture
def mock_config():
    config = MagicMock(spec=MonocoConfig)
    config.i18n = I18nConfig(source_lang="zh")
    config.paths = PathsConfig(root=".", issues="Issues")
    return config


@patch("monoco.features.memo.cli.get_config")
@patch("monoco.features.memo.cli.get_issues_root")
@patch("monoco.features.memo.cli.add_memo")
def test_memo_add_zh_validation_success(mock_add_memo, mock_get_issues_root, mock_get_config, mock_config):
    mock_get_config.return_value = mock_config
    mock_get_issues_root.return_value = "/tmp/Issues"
    mock_add_memo.return_value = "abc123"

    result = runner.invoke(app, ["add", "你好世界"])

    assert result.exit_code == 0
    assert "Memo recorded" in result.stdout
    mock_add_memo.assert_called_once()


@patch("monoco.features.memo.cli.get_config")
@patch("monoco.features.memo.cli.get_issues_root")
@patch("monoco.features.memo.cli.add_memo")
def test_memo_add_zh_validation_failure(mock_add_memo, mock_get_issues_root, mock_get_config, mock_config):
    mock_get_config.return_value = mock_config
    mock_get_issues_root.return_value = "/tmp/Issues"

    result = runner.invoke(app, ["add", "Hello World"])

    assert result.exit_code != 0
    assert "Error: Content language mismatch" in result.stdout
    mock_add_memo.assert_not_called()


@patch("monoco.features.memo.cli.get_config")
@patch("monoco.features.memo.cli.get_issues_root")
@patch("monoco.features.memo.cli.add_memo")
def test_memo_add_zh_validation_bypass_with_force(mock_add_memo, mock_get_issues_root, mock_get_config, mock_config):
    mock_get_config.return_value = mock_config
    mock_get_issues_root.return_value = "/tmp/Issues"
    mock_add_memo.return_value = "abc123"

    result = runner.invoke(app, ["add", "Hello World", "--force"])

    assert result.exit_code == 0
    assert "Memo recorded" in result.stdout
    mock_add_memo.assert_called_once()


@patch("monoco.features.memo.cli.get_config")
@patch("monoco.features.memo.cli.get_issues_root")
@patch("monoco.features.memo.cli.add_memo")
def test_memo_add_en_validation_success(mock_add_memo, mock_get_issues_root, mock_get_config, mock_config):
    # Change source_lang to en
    mock_config.i18n.source_lang = "en"
    mock_get_config.return_value = mock_config
    mock_get_issues_root.return_value = "/tmp/Issues"
    mock_add_memo.return_value = "abc123"

    # In 'en' mode, we currently allow everything (the heuristic returns True)
    result = runner.invoke(app, ["add", "Hello World"])

    assert result.exit_code == 0
    assert "Memo recorded" in result.stdout
    mock_add_memo.assert_called_once()
