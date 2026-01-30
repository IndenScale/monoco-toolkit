"""Tests for hook context."""

import pytest
from datetime import datetime
from pathlib import Path

from monoco.core.hooks.context import (
    HookContext,
    IssueInfo,
    GitInfo,
)


class TestIssueInfo:
    """Tests for IssueInfo dataclass."""

    def test_issue_info_creation(self):
        info = IssueInfo(
            id="FEAT-0120",
            status="open",
            stage="doing",
            title="Test Issue",
            branch_name="feat/feat-0120-test",
            is_merged=False,
        )
        assert info.id == "FEAT-0120"
        assert info.status == "open"
        assert info.branch_name == "feat/feat-0120-test"

    def test_issue_info_from_metadata(self):
        """Test creating IssueInfo from metadata object."""
        # Create a mock metadata object
        class MockMetadata:
            id = "FEAT-0120"
            status = "open"
            stage = "doing"
            title = "Test Issue"
            isolation = None

        metadata = MockMetadata()
        info = IssueInfo.from_metadata(metadata)
        
        assert info.id == "FEAT-0120"
        assert info.status == "open"
        assert info.branch_name is None


class TestGitInfo:
    """Tests for GitInfo dataclass."""

    def test_git_info_creation(self, tmp_path):
        info = GitInfo(
            project_root=tmp_path,
            current_branch="main",
            has_uncommitted_changes=False,
            default_branch="main",
        )
        assert info.project_root == tmp_path
        assert info.current_branch == "main"
        assert info.default_branch == "main"


class TestHookContext:
    """Tests for HookContext dataclass."""

    def test_hook_context_creation(self):
        context = HookContext(
            session_id="session-123",
            role_name="reviewer",
            session_status="running",
            created_at=datetime.now(),
        )
        assert context.session_id == "session-123"
        assert context.role_name == "reviewer"
        assert context.extra == {}

    def test_hook_context_with_issue_and_git(self, tmp_path):
        issue = IssueInfo(id="FEAT-0120", status="open")
        git = GitInfo(project_root=tmp_path, current_branch="main")
        
        context = HookContext(
            session_id="session-123",
            role_name="reviewer",
            session_status="running",
            created_at=datetime.now(),
            issue=issue,
            git=git,
            extra={"custom_key": "custom_value"},
        )
        
        assert context.issue.id == "FEAT-0120"
        assert context.git.project_root == tmp_path
        assert context.extra["custom_key"] == "custom_value"
