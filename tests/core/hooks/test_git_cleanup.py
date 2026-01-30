"""Tests for GitCleanupHook."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from monoco.core.hooks.builtin.git_cleanup import GitCleanupHook
from monoco.core.hooks.context import HookContext, IssueInfo, GitInfo
from monoco.core.hooks.base import HookStatus


class TestGitCleanupHook:
    """Tests for GitCleanupHook."""

    def test_hook_initialization_defaults(self):
        hook = GitCleanupHook()
        
        assert hook.name == "git_cleanup"
        assert hook.auto_switch_to_main is True
        assert hook.auto_delete_merged_branches is True
        assert hook.main_branch == "main"
        assert hook.require_clean_worktree is True

    def test_hook_initialization_with_config(self):
        config = {
            "enabled": True,
            "auto_switch_to_main": False,
            "auto_delete_merged_branches": False,
            "main_branch": "master",
            "require_clean_worktree": False,
        }
        hook = GitCleanupHook(config=config)
        
        assert hook.auto_switch_to_main is False
        assert hook.auto_delete_merged_branches is False
        assert hook.main_branch == "master"
        assert hook.require_clean_worktree is False

    def test_on_session_start(self):
        hook = GitCleanupHook()
        context = HookContext(
            session_id="test",
            role_name="reviewer",
            session_status="running",
            created_at=None,
        )
        
        result = hook.on_session_start(context)
        
        assert result.status == HookStatus.SUCCESS
        assert "initialized" in result.message

    def test_on_session_end_no_git_context(self):
        hook = GitCleanupHook()
        context = HookContext(
            session_id="test",
            role_name="reviewer",
            session_status="running",
            created_at=None,
            git=None,
        )
        
        result = hook.on_session_end(context)
        
        assert result.status == HookStatus.SKIPPED
        assert "No git context" in result.message

    @patch("monoco.core.git.is_git_repo")
    def test_on_session_end_not_git_repo(self, mock_is_git_repo):
        mock_is_git_repo.return_value = False
        
        hook = GitCleanupHook()
        git_info = GitInfo(project_root=Path("/fake"), current_branch="main")
        context = HookContext(
            session_id="test",
            role_name="reviewer",
            session_status="running",
            created_at=None,
            git=git_info,
        )
        
        result = hook.on_session_end(context)
        
        assert result.status == HookStatus.SKIPPED
        assert "Not a git repository" in result.message

    @patch("monoco.core.git.branch_exists")
    @patch("monoco.core.git.checkout_branch")
    def test_switch_to_main_success(self, mock_checkout, mock_branch_exists):
        mock_branch_exists.return_value = True
        
        hook = GitCleanupHook()
        result = hook._switch_to_main(
            project_root=Path("/fake"),
            current_branch="feature-branch",
            default_branch="main",
            has_changes=False,
        )
        
        assert result.status == HookStatus.SUCCESS
        mock_checkout.assert_called_once_with(Path("/fake"), "main")

    def test_switch_to_main_with_uncommitted_changes(self):
        hook = GitCleanupHook()
        result = hook._switch_to_main(
            project_root=Path("/fake"),
            current_branch="feature-branch",
            default_branch="main",
            has_changes=True,
        )
        
        assert result.status == HookStatus.WARNING
        assert "uncommitted changes" in result.message

    def test_switch_to_main_disabled(self):
        hook = GitCleanupHook(config={"auto_switch_to_main": False})
        # This scenario is handled at a higher level, but we test the config works
        assert hook.auto_switch_to_main is False

    @patch("monoco.core.git.branch_exists")
    def test_cleanup_feature_branch_not_completed(self, mock_branch_exists):
        mock_branch_exists.return_value = True
        
        hook = GitCleanupHook()
        issue = IssueInfo(
            id="FEAT-0120",
            status="open",  # Not completed
            branch_name="feat/feat-0120",
        )
        
        result = hook._cleanup_feature_branch(
            project_root=Path("/fake"),
            issue=issue,
            default_branch="main",
            current_branch="main",
        )
        
        assert result.status == HookStatus.SKIPPED
        assert "not deleted" in result.message

    @patch("monoco.core.git.branch_exists")
    def test_cleanup_feature_branch_currently_checked_out(self, mock_branch_exists):
        mock_branch_exists.return_value = True
        
        hook = GitCleanupHook()
        issue = IssueInfo(
            id="FEAT-0120",
            status="closed",
            branch_name="feat/feat-0120",
        )
        
        result = hook._cleanup_feature_branch(
            project_root=Path("/fake"),
            issue=issue,
            default_branch="main",
            current_branch="feat/feat-0120",  # Same as feature branch
        )
        
        assert result.status == HookStatus.WARNING
        assert "currently checked out" in result.message

    @patch("monoco.core.git.branch_exists")
    def test_cleanup_feature_branch_not_merged(self, mock_branch_exists):
        mock_branch_exists.return_value = True
        
        hook = GitCleanupHook()
        issue = IssueInfo(
            id="FEAT-0120",
            status="closed",
            branch_name="feat/feat-0120",
        )
        
        # Mock _is_branch_merged to return False
        hook._is_branch_merged = Mock(return_value=False)
        
        result = hook._cleanup_feature_branch(
            project_root=Path("/fake"),
            issue=issue,
            default_branch="main",
            current_branch="main",
        )
        
        assert result.status == HookStatus.WARNING
        assert "not merged" in result.message

    @patch("monoco.core.git.branch_exists")
    @patch("monoco.core.git.delete_branch")
    def test_cleanup_feature_branch_success(self, mock_delete_branch, mock_branch_exists):
        mock_branch_exists.return_value = True
        mock_delete_branch.return_value = None
        
        hook = GitCleanupHook()
        issue = IssueInfo(
            id="FEAT-0120",
            status="closed",
            branch_name="feat/feat-0120",
        )
        
        # Mock _is_branch_merged to return True
        hook._is_branch_merged = Mock(return_value=True)
        
        result = hook._cleanup_feature_branch(
            project_root=Path("/fake"),
            issue=issue,
            default_branch="main",
            current_branch="main",
        )
        
        assert result.status == HookStatus.SUCCESS
        assert "Deleted merged branch" in result.message
        mock_delete_branch.assert_called_once_with(Path("/fake"), "feat/feat-0120", force=False)

    @patch("monoco.core.git._run_git")
    def test_is_branch_merged_true(self, mock_run_git):
        mock_run_git.return_value = (0, "", "")  # Exit code 0 means merged
        
        hook = GitCleanupHook()
        result = hook._is_branch_merged(Path("/fake"), "feature", "main")
        
        assert result is True
        mock_run_git.assert_called_once_with(
            ["merge-base", "--is-ancestor", "feature", "main"],
            Path("/fake")
        )

    @patch("monoco.core.git._run_git")
    def test_is_branch_merged_false(self, mock_run_git):
        mock_run_git.return_value = (1, "", "")  # Exit code 1 means not merged
        
        hook = GitCleanupHook()
        result = hook._is_branch_merged(Path("/fake"), "feature", "main")
        
        assert result is False

    @patch("monoco.core.git.branch_exists")
    def test_get_default_branch_main(self, mock_branch_exists):
        def side_effect(path, branch):
            return branch == "main"
        mock_branch_exists.side_effect = side_effect
        
        hook = GitCleanupHook()
        result = hook._get_default_branch(Path("/fake"))
        
        assert result == "main"

    @patch("monoco.core.git.branch_exists")
    def test_get_default_branch_fallback_to_master(self, mock_branch_exists):
        def side_effect(path, branch):
            return branch == "master"
        mock_branch_exists.side_effect = side_effect
        
        hook = GitCleanupHook()
        result = hook._get_default_branch(Path("/fake"))
        
        assert result == "master"
