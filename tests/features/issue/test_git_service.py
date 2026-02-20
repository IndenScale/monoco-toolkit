"""
Tests for IssueGitService - Auto-commit functionality for Issue status/stage updates.

FEAT-0115: Auto-commit issue ticket file on status/stage updates
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from monoco.features.issue.git_service import (
    IssueGitService,
    should_auto_commit,
)
from monoco.features.issue import core
from monoco.core import git


@pytest.fixture
def git_repo_env():
    """
    Provides a temporary initialized Monoco project with git repository.
    Uses ~/.monoco/config.yaml for configuration (backed up and restored after test).
    """
    tmp_dir = tempfile.mkdtemp()
    project_root = Path(tmp_dir)

    # Initialize git repo
    git._run_git(["init"], project_root)
    git._run_git(["config", "user.email", "test@test.com"], project_root)
    git._run_git(["config", "user.name", "Test User"], project_root)

    # Initialize .monoco structure (minimal, only for project marker)
    dot_monoco = project_root / ".monoco"
    dot_monoco.mkdir()

    # Initialize Issues structure
    issues_dir = project_root / "Issues"
    core.init(issues_dir)

    # Create initial commit
    (project_root / "README.md").write_text("# Test Project")
    git.git_add(project_root, ["README.md"])
    git.git_commit(project_root, "Initial commit")

    # Setup global config (~/.monoco/config.yaml) with test settings
    global_config_dir = Path.home() / ".monoco"
    global_config_dir.mkdir(parents=True, exist_ok=True)
    global_config_path = global_config_dir / "config.yaml"

    # Backup original config if exists
    backup_config = None
    if global_config_path.exists():
        backup_config = global_config_path.read_text()

    # Write test config
    test_config = """project:
  name: Test Project
  key: TEST
paths:
  issues: Issues
"""
    global_config_path.write_text(test_config)

    # Change CWD for CLI tests
    old_cwd = os.getcwd()
    os.chdir(tmp_dir)

    # Clear config cache
    from monoco.core import config

    config._settings = None

    yield project_root

    # Restore CWD
    os.chdir(old_cwd)
    shutil.rmtree(tmp_dir)

    # Restore original config or remove test config
    if backup_config is not None:
        global_config_path.write_text(backup_config)
    else:
        global_config_path.unlink(missing_ok=True)

    # Clear config cache again
    config._settings = None


class TestIssueGitService:
    """Test IssueGitService functionality."""

    def test_is_git_repository_positive(self, git_repo_env):
        """Test detection of git repository."""
        service = IssueGitService(git_repo_env)
        assert service.is_git_repository() is True

    def test_is_git_repository_negative(self):
        """Test detection when not in git repository."""
        tmp_dir = tempfile.mkdtemp()
        try:
            service = IssueGitService(Path(tmp_dir))
            assert service.is_git_repository() is False
        finally:
            shutil.rmtree(tmp_dir)

    def test_generate_commit_message(self, git_repo_env):
        """Test commit message generation."""
        service = IssueGitService(git_repo_env)

        # Test various actions
        assert (
            service._generate_commit_message("FEAT-0115", "close")
            == "chore(issue): close FEAT-0115"
        )
        assert (
            service._generate_commit_message("FEAT-0115", "start")
            == "chore(issue): start FEAT-0115"
        )
        assert (
            service._generate_commit_message("FEAT-0115", "open")
            == "chore(issue): open FEAT-0115"
        )
        assert (
            service._generate_commit_message("FIX-0020", "submit")
            == "chore(issue): submit FIX-0020"
        )

    def test_commit_issue_change_success(self, git_repo_env):
        """Test successful commit of issue change."""
        service = IssueGitService(git_repo_env)
        issues_root = git_repo_env / "Issues"

        # Create an issue first
        meta, path = core.create_issue_file(
            issues_root, "feature", "Test Feature", parent="EPIC-0000"
        )

        # Commit the change
        result = service.commit_issue_change(
            issue_id="FEAT-0001",
            action="open",
            issue_file_path=path,
        )

        assert result.success is True
        assert result.commit_hash is not None
        assert result.message == "chore(issue): open FEAT-0001"
        assert result.error is None

        # Verify commit exists
        commits = service.get_commit_history("FEAT-0001")
        assert len(commits) == 1
        assert commits[0][1] == "chore(issue): open FEAT-0001"

    def test_commit_issue_change_no_commit_flag(self, git_repo_env):
        """Test that no_commit flag skips the commit."""
        service = IssueGitService(git_repo_env)
        issues_root = git_repo_env / "Issues"

        # Create an issue
        meta, path = core.create_issue_file(
            issues_root, "feature", "Test Feature", parent="EPIC-0000"
        )

        # Commit with no_commit=True
        result = service.commit_issue_change(
            issue_id="FEAT-0001",
            action="open",
            issue_file_path=path,
            no_commit=True,
        )

        assert result.success is True
        assert result.message == "Skipped (no-commit flag)"
        assert result.commit_hash is None

    def test_commit_issue_change_not_git_repo(self):
        """Test graceful handling when not in git repo."""
        tmp_dir = tempfile.mkdtemp()
        try:
            service = IssueGitService(Path(tmp_dir))

            result = service.commit_issue_change(
                issue_id="FEAT-0001",
                action="open",
                issue_file_path=Path(tmp_dir) / "test.md",
            )

            assert result.success is True
            assert result.message == "Skipped (not a git repo)"
        finally:
            shutil.rmtree(tmp_dir)

    def test_stage_issue_files(self, git_repo_env):
        """Test staging of issue files."""
        service = IssueGitService(git_repo_env)
        issues_root = git_repo_env / "Issues"

        # Create an issue
        meta, path = core.create_issue_file(
            issues_root, "feature", "Test Feature", parent="EPIC-0000"
        )

        # Stage the file
        service._stage_issue_files(path)

        # Check that file is staged
        staged = git.get_git_status(git_repo_env)
        assert any("FEAT-0001" in f for f in staged)


class TestAutoCommitIntegration:
    """Test integration of auto-commit with update_issue."""

    def test_update_issue_auto_commit_on_status_change(self, git_repo_env):
        """Test that update_issue auto-commits on status change (backlog)."""
        issues_root = git_repo_env / "Issues"

        # Create an epic first (as parent)
        core.create_issue_file(issues_root, "epic", "Parent Epic")

        # Create a feature
        meta, path = core.create_issue_file(
            issues_root, "feature", "Test Feature", parent="EPIC-0001"
        )

        # Commit the creation
        git.git_add(git_repo_env, [str(path.relative_to(git_repo_env))])
        git.git_commit(git_repo_env, "Create issue")

        # Update status to backlog (should auto-commit)
        updated = core.update_issue(
            issues_root,
            "FEAT-0001",
            status="backlog",
            project_root=git_repo_env,
        )

        # Verify commit was made
        assert hasattr(updated, "commit_result")
        assert updated.commit_result is not None
        assert updated.commit_result.success is True
        assert "backlog" in updated.commit_result.message

    def test_update_issue_auto_commit_on_stage_change(self, git_repo_env):
        """Test that update_issue auto-commits on stage change."""
        issues_root = git_repo_env / "Issues"

        # Create an epic first
        core.create_issue_file(issues_root, "epic", "Parent Epic")

        # Create a feature
        meta, path = core.create_issue_file(
            issues_root, "feature", "Test Feature", parent="EPIC-0001"
        )

        # Commit the creation
        git.git_add(git_repo_env, [str(path.relative_to(git_repo_env))])
        git.git_commit(git_repo_env, "Create issue")

        # Update stage (should auto-commit)
        updated = core.update_issue(
            issues_root,
            "FEAT-0001",
            stage="doing",
            project_root=git_repo_env,
        )

        # Verify commit was made
        assert hasattr(updated, "commit_result")
        assert updated.commit_result is not None
        assert updated.commit_result.success is True
        assert "doing" in updated.commit_result.message

    def test_update_issue_no_commit_flag(self, git_repo_env):
        """Test that no_commit flag prevents auto-commit."""
        issues_root = git_repo_env / "Issues"

        # Create an epic first
        core.create_issue_file(issues_root, "epic", "Parent Epic")

        # Create a feature
        meta, path = core.create_issue_file(
            issues_root, "feature", "Test Feature", parent="EPIC-0001"
        )

        # Commit the creation
        git.git_add(git_repo_env, [str(path.relative_to(git_repo_env))])
        git.git_commit(git_repo_env, "Create issue")

        # Get commit count before
        code, stdout, _ = git._run_git(["rev-list", "--count", "HEAD"], git_repo_env)
        commits_before = int(stdout.strip())

        # Update with no_commit=True
        updated = core.update_issue(
            issues_root,
            "FEAT-0001",
            stage="doing",
            no_commit=True,
            project_root=git_repo_env,
        )

        # Verify no new commit was made
        code, stdout, _ = git._run_git(["rev-list", "--count", "HEAD"], git_repo_env)
        commits_after = int(stdout.strip())

        assert commits_after == commits_before

    def test_update_issue_not_git_repo(self, project_env):
        """Test graceful handling when not in git repo."""
        issues_root = project_env / "Issues"

        # Create an epic first
        core.create_issue_file(issues_root, "epic", "Parent Epic")

        # Create a feature
        meta, path = core.create_issue_file(
            issues_root, "feature", "Test Feature", parent="EPIC-0001"
        )

        # Update should work even without git
        updated = core.update_issue(
            issues_root,
            "FEAT-0001",
            stage="doing",
            project_root=project_env,
        )

        # Should succeed without error
        assert updated.stage == "doing"


class TestShouldAutoCommit:
    """Test should_auto_commit configuration check."""

    def test_should_auto_commit_default(self):
        """Test default behavior (enabled)."""
        # Use a config without issue.auto_commit attribute
        config = MagicMock()
        config.issue = MagicMock()
        del config.issue.auto_commit  # Remove auto_commit to simulate missing config
        assert should_auto_commit(config) is True

    def test_should_auto_commit_env_var(self):
        """Test MONOCO_NO_AUTO_COMMIT env var."""
        config = MagicMock()

        # Set env var
        old_env = os.environ.get("MONOCO_NO_AUTO_COMMIT")
        os.environ["MONOCO_NO_AUTO_COMMIT"] = "1"
        try:
            assert should_auto_commit(config) is False
        finally:
            if old_env is not None:
                os.environ["MONOCO_NO_AUTO_COMMIT"] = old_env
            else:
                del os.environ["MONOCO_NO_AUTO_COMMIT"]

    def test_should_auto_commit_config_disabled(self):
        """Test config override to disable."""
        config = MagicMock()
        config.issue.auto_commit = False
        assert should_auto_commit(config) is False


class TestCommitScopeRestriction:
    """Test that auto-commit only touches issue files."""

    def test_commit_only_touches_issue_file(self, git_repo_env):
        """Verify that auto-commit only stages the issue file, not other files."""
        service = IssueGitService(git_repo_env)
        issues_root = git_repo_env / "Issues"

        # Create an issue
        meta, path = core.create_issue_file(
            issues_root, "feature", "Test Feature", parent="EPIC-0000"
        )

        # Create a "dirty" business file
        dirty_file = git_repo_env / "src" / "business.py"
        dirty_file.parent.mkdir(parents=True)
        dirty_file.write_text("# Business code")

        # Stage only the issue file
        service._stage_issue_files(path)

        # Check staged files
        code, stdout, _ = git._run_git(
            ["diff", "--cached", "--name-only"], git_repo_env
        )
        staged_files = stdout.strip().split("\n") if stdout.strip() else []

        # Should only have the issue file
        assert any("FEAT-0001" in f for f in staged_files)
        assert not any("business.py" in f for f in staged_files)


class TestCommitMessageFormat:
    """Test commit message format compliance."""

    def test_commit_message_format(self, git_repo_env):
        """Verify commit message follows conventional format."""
        service = IssueGitService(git_repo_env)

        # Test format: chore(issue): <action> <issue_id>
        msg = service._generate_commit_message("FEAT-0115", "close")

        # Should match expected pattern
        assert msg.startswith("chore(issue):")
        assert "FEAT-0115" in msg
        assert "close" in msg

    def test_commit_message_various_actions(self, git_repo_env):
        """Test commit messages for various actions."""
        service = IssueGitService(git_repo_env)

        actions = ["open", "close", "start", "submit", "backlog", "doing", "review"]
        for action in actions:
            msg = service._generate_commit_message("FEAT-0115", action)
            assert msg == f"chore(issue): {action} FEAT-0115"
