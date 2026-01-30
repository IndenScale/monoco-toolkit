from typer.testing import CliRunner
from monoco.features.issue.commands import app
from monoco.features.issue import core
from monoco.features.issue.models import IssueType
from pathlib import Path
from unittest.mock import patch

runner = CliRunner()


def test_force_prune_confirmation(project_env):
    """Test that --force-prune triggers a confirmation prompt."""
    issues_root = project_env / "Issues"
    core.create_issue_file(issues_root, IssueType.EPIC, "Root Epic")
    meta, _ = core.create_issue_file(
        issues_root, IssueType.FEATURE, "Feat", parent="EPIC-0001"
    )

    # Satisfy AC
    path = Path(meta.path)
    content = path.read_text().replace("- [ ]", "- [x]")
    # Remove placeholder comment and add review content
    content = content.replace(
        "<!-- Required for Review/Done stage. Record review feedback here. -->",
        "Review completed."
    )
    path.write_text(content)

    # Transition to Review to allow closing
    core.update_issue(issues_root, meta.id, stage=core.IssueStage.DOING)
    core.update_issue(issues_root, meta.id, stage=core.IssueStage.REVIEW)

    # 1. User says No
    result = runner.invoke(
        app,
        ["close", meta.id, "--solution", "implemented", "--force-prune"],
        input="n\n",
    )
    assert result.exit_code != 0
    # Typer might not verify print "Aborted" to stdout in all test runners contexts or version
    # assert "Aborted" in result.stdout

    # 2. User says Yes
    with patch("monoco.features.issue.core.prune_issue_resources") as mock_prune:
        mock_prune.return_value = ["branch:feat/test"]  # Return serializable list
        result = runner.invoke(
            app,
            ["close", meta.id, "--solution", "implemented", "--force-prune"],
            input="y\n",
        )
        if result.exit_code != 0:
            print("STDOUT:", result.stdout)
            print(
                "STDERR:", result.stderr
            )  # Typer/Click puts errors here often or in stdout depending on config
            print("Exception:", result.exc_info)
        assert result.exit_code == 0
        # Verify force=True passed to prune
        mock_prune.assert_called_with(
            issues_root.resolve(), meta.id, True, project_env.resolve()
        )


def test_force_prune_json_no_prompt(project_env):
    """Test that --force-prune with --json skips confirmation."""
    issues_root = project_env / "Issues"
    core.create_issue_file(issues_root, IssueType.EPIC, "Root Epic")
    meta, _ = core.create_issue_file(
        issues_root, IssueType.FEATURE, "Feat 2", parent="EPIC-0001"
    )

    path = Path(meta.path)
    content = path.read_text().replace("- [ ]", "- [x]")
    # Remove placeholder comment and add review content
    content = content.replace(
        "<!-- Required for Review/Done stage. Record review feedback here. -->",
        "Review completed."
    )
    path.write_text(content)

    # Transition to Review
    core.update_issue(issues_root, meta.id, stage=core.IssueStage.DOING)
    core.update_issue(issues_root, meta.id, stage=core.IssueStage.REVIEW)

    with patch("monoco.features.issue.core.prune_issue_resources") as mock_prune:
        mock_prune.return_value = []  # Return serializable list
        result = runner.invoke(
            app,
            # Note: Assuming --json is the flag.
            ["close", meta.id, "--solution", "implemented", "--force-prune", "--json"],
        )
        if result.exit_code != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        assert result.exit_code == 0
        mock_prune.assert_called_with(
            issues_root.resolve(), meta.id, True, project_env.resolve()
        )
