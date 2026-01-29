from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from monoco.features.issue.commands import app
from monoco.features.issue import core
from monoco.features.issue.models import IssueType

runner = CliRunner()


def test_start_command_default_branch(issues_root):
    """Test that start command defaults to creating a branch."""
    # Setup: Create an issue
    meta, _ = core.create_issue_file(
        issues_root, IssueType.FEATURE, "Test Issue Branch"
    )

    # Mock update_issue to return a valid issue to avoid real logic if needed,
    # but actual core logic is likely fine if we mock isolation.
    # However, commands.py calls core.update_issue first, then start_issue_isolation.

    with patch("monoco.features.issue.core.start_issue_isolation") as mock_isolation:
        # Mock return value of start_issue_isolation
        mock_issue = MagicMock()
        mock_issue.isolation.ref = "feat/test-branch"
        mock_isolation.return_value = mock_issue

        # Invoke command
        result = runner.invoke(app, ["start", meta.id, "--root", str(issues_root)])

        assert result.exit_code == 0

        # Verify isolation was called with "branch"
        mock_isolation.assert_called_once()
        args, _ = mock_isolation.call_args
        # args: (issues_root, issue_id, type, project_root)
        assert args[1] == meta.id
        assert args[2] == "branch"


def test_start_command_no_branch(issues_root):
    """Test that --no-branch disables branch creation."""
    meta, _ = core.create_issue_file(
        issues_root, IssueType.FEATURE, "Test Issue No Branch"
    )

    with patch("monoco.features.issue.core.start_issue_isolation") as mock_isolation:
        # Invoke command with --no-branch
        result = runner.invoke(
            app, ["start", meta.id, "--no-branch", "--root", str(issues_root)]
        )

        assert result.exit_code == 0

        # Verify isolation was NOT called
        mock_isolation.assert_not_called()

        # Verify output contains "isolation": {"type": "direct"} or similar logic verification
        # But OutputManager prints structured data, we might not capture it easily without mocking OutputManager
        # or checking stdout str.
        # Check standard output for implicit confirmation if needed.


def test_start_command_direct_flag(issues_root):
    """Test that --direct flag disables branch creation (equivalent to --no-branch)."""
    meta, _ = core.create_issue_file(
        issues_root, IssueType.FEATURE, "Test Issue Direct"
    )

    with patch("monoco.features.issue.core.start_issue_isolation") as mock_isolation:
        # Invoke command with --direct
        result = runner.invoke(
            app, ["start", meta.id, "--direct", "--root", str(issues_root)]
        )

        assert result.exit_code == 0

        # Verify isolation was NOT called
        mock_isolation.assert_not_called()
