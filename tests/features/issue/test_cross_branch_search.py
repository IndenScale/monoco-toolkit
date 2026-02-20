"""
Tests for cross-branch issue search functionality (FIX-0006).

This module tests the ability to find issues across git branches,
which is essential for the 'monoco issue close' command to work
correctly when closing issues from feature branches.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from monoco.features.issue.core import (
    find_issue_path_across_branches,
    _find_branches_with_file,
    _search_issue_in_branches,
)


class TestFindBranchesWithFile:
    """Tests for _find_branches_with_file helper function."""

    def test_find_branches_with_file_excludes_current(self, tmp_path):
        """Test that current branch is excluded from results."""
        with patch("monoco.features.issue.core.git._run_git") as mock_run:
            # Mock git branch output - need 3 calls: branch list, check feature/test, check main (excluded)
            mock_run.side_effect = [
                (0, "main\nfeature/test\n", ""),  # branch list
                (1, "", "error"),  # feature/test doesn't have file (git show fails)
            ]
            
            result = _find_branches_with_file(tmp_path, "Issues/Fixes/open/TEST-0001.md", "main")
            
            assert result == []

    def test_find_branches_with_file_finds_other_branches(self, tmp_path):
        """Test finding branches that contain the file."""
        with patch("monoco.features.issue.core.git._run_git") as mock_run:
            mock_run.side_effect = [
                (0, "main\nfeature/test\nfeature/other\n", ""),  # branch list
                (0, "content", ""),  # feature/test has file
                (1, "", "error"),  # feature/other doesn't have file
            ]
            
            result = _find_branches_with_file(tmp_path, "Issues/Fixes/open/TEST-0001.md", "main")
            
            assert result == ["feature/test"]

    def test_find_branches_with_file_git_error(self, tmp_path):
        """Test handling of git command errors."""
        with patch("monoco.features.issue.core.git._run_git") as mock_run:
            mock_run.return_value = (1, "", "error")
            
            result = _find_branches_with_file(tmp_path, "test.md", "main")
            
            assert result == []


class TestSearchIssueInBranches:
    """Tests for _search_issue_in_branches helper function."""

    def test_search_finds_issue_in_single_branch(self, tmp_path):
        """Test finding an issue that exists in exactly one branch."""
        issues_root = tmp_path / "Issues"
        issues_root.mkdir()
        
        # Create directory structure for FIX type
        fixes_dir = issues_root / "Fixes"
        fixes_dir.mkdir()
        (fixes_dir / "open").mkdir()
        
        with patch("monoco.features.issue.core.git._run_git") as mock_run, \
             patch("monoco.features.issue.core.git.git_checkout_files") as mock_checkout:
            # Mock returns (code, stdout, stderr)
            # For each ls-tree call that finds nothing, return (0, "", "")
            # For ls-tree that finds the file, return (0, "filepath\n", "")
            def mock_git_response(args, cwd):
                cmd = ' '.join(args)
                if "branch --format" in cmd:
                    return (0, "main\nfeature/test\n", "")
                elif "ls-tree" in cmd:
                    # Command format: ls-tree -r --name-only main Issues/Fixes/open
                    # Check if it's the main branch and open directory
                    if "main" in cmd and "open" in cmd and "backlog" not in cmd and "closed" not in cmd and "archived" not in cmd:
                        return (0, "Issues/Fixes/open/FIX-0001-test-issue.md\n", "")
                    else:
                        return (0, "", "")
                return (1, "", "error")
            
            mock_run.side_effect = mock_git_response
            mock_checkout.return_value = None
            
            path, branch, conflicting = _search_issue_in_branches(issues_root, "FIX-0001", tmp_path)
            
            # Function returns (path, branch, conflicting_branches) tuple
            assert branch == "main"
            assert path is not None
            assert "FIX-0001" in str(path)
            assert conflicting is None  # No conflict for single branch

    def test_search_not_found(self, tmp_path):
        """Test when issue is not found in any branch."""
        issues_root = tmp_path / "Issues"
        issues_root.mkdir()
        
        fixes_dir = issues_root / "Fixes"
        fixes_dir.mkdir()
        (fixes_dir / "open").mkdir()
        
        with patch("monoco.features.issue.core.git._run_git") as mock_run:
            def mock_git_response(args, cwd):
                cmd = ' '.join(args)
                if "branch --format" in cmd:
                    return (0, "main\n", "")
                elif "ls-tree" in cmd:
                    return (0, "", "")  # All directories empty
                return (1, "", "error")
            
            mock_run.side_effect = mock_git_response
            
            path, branch, conflicting = _search_issue_in_branches(issues_root, "FIX-9999", tmp_path)
            
            assert path is None
            assert branch is None
            assert conflicting is None

    def test_search_conflict_multiple_branches(self, tmp_path):
        """Test error when issue exists in multiple branches."""
        issues_root = tmp_path / "Issues"
        issues_root.mkdir()
        
        fixes_dir = issues_root / "Fixes"
        fixes_dir.mkdir()
        (fixes_dir / "open").mkdir()
        
        with patch("monoco.features.issue.core.git._run_git") as mock_run:
            def mock_git_response(args, cwd):
                cmd = ' '.join(args)
                if "branch --format" in cmd:
                    return (0, "main\nfeature/test\n", "")
                elif "ls-tree" in cmd:
                    if "open" in cmd:  # Both branches have the file in open/
                        return (0, "Issues/Fixes/open/FIX-0001-test.md\n", "")
                    else:
                        return (0, "", "")
                return (1, "", "error")
            
            mock_run.side_effect = mock_git_response
            
            path, branch, conflicting = _search_issue_in_branches(issues_root, "FIX-0001", tmp_path)
            
            # Now returns conflict info instead of raising
            assert conflicting is not None
            assert "main" in conflicting
            assert "feature/test" in conflicting


class TestFindIssuePathAcrossBranches:
    """Tests for the main find_issue_path_across_branches function."""

    def test_local_file_no_git(self, tmp_path):
        """Test finding issue locally when not in a git repo."""
        issues_root = tmp_path / "Issues"
        fixes_dir = issues_root / "Fixes" / "open"
        fixes_dir.mkdir(parents=True)
        
        # Create issue file
        issue_file = fixes_dir / "FIX-0001-test-issue.md"
        issue_file.write_text("---\nid: FIX-0001\n---\n\n## FIX-0001: Test")
        
        with patch("monoco.features.issue.core.git.is_git_repo") as mock_is_git:
            mock_is_git.return_value = False
            
            path, branch, conflicting = find_issue_path_across_branches(issues_root, "FIX-0001", tmp_path)
            
            assert path == issue_file
            assert branch is None
            assert conflicting is None

    def test_local_file_in_git_repo(self, tmp_path):
        """Test finding issue locally when in git repo (golden path)."""
        issues_root = tmp_path / "Issues"
        fixes_dir = issues_root / "Fixes" / "open"
        fixes_dir.mkdir(parents=True)
        
        issue_file = fixes_dir / "FIX-0001-test-issue.md"
        issue_file.write_text("---\nid: FIX-0001\n---\n\n## FIX-0001: Test")
        
        with patch("monoco.features.issue.core.git.is_git_repo") as mock_is_git, \
             patch("monoco.features.issue.core.git.get_current_branch") as mock_branch, \
             patch("monoco.features.issue.core._find_branches_with_file") as mock_find:
            mock_is_git.return_value = True
            mock_branch.return_value = "main"
            mock_find.return_value = []  # No other branches have this file
            
            path, branch, conflicting = find_issue_path_across_branches(issues_root, "FIX-0001", tmp_path)
            
            assert path == issue_file
            assert branch == "main"
            assert conflicting is None

    def test_not_locally_found_in_other_branch(self, tmp_path):
        """Test finding issue in another branch when not present locally."""
        issues_root = tmp_path / "Issues"
        fixes_dir = issues_root / "Fixes" / "open"
        fixes_dir.mkdir(parents=True)
        
        # File doesn't exist locally
        
        with patch("monoco.features.issue.core.git.is_git_repo") as mock_is_git, \
             patch("monoco.features.issue.core._search_issue_in_branches") as mock_search:
            mock_is_git.return_value = True
            mock_search.return_value = (Path("Issues/Fixes/open/FIX-0001-test.md"), "feature/test", None)
            
            path, branch, conflicting = find_issue_path_across_branches(issues_root, "FIX-0001", tmp_path)
            
            assert branch == "feature/test"
            assert conflicting is None

    def test_not_found_anywhere(self, tmp_path):
        """Test when issue is not found anywhere."""
        issues_root = tmp_path / "Issues"
        fixes_dir = issues_root / "Fixes" / "open"
        fixes_dir.mkdir(parents=True)
        
        with patch("monoco.features.issue.core.git.is_git_repo") as mock_is_git, \
             patch("monoco.features.issue.core._search_issue_in_branches") as mock_search:
            mock_is_git.return_value = True
            mock_search.return_value = (None, None, None)
            
            path, branch, conflicting = find_issue_path_across_branches(issues_root, "FIX-9999", tmp_path)
            
            assert path is None
            assert branch is None
            assert conflicting is None


class TestCrossBranchIntegration:
    """Integration-style tests for cross-branch functionality."""

    def test_workspace_issue_not_searched_across_branches(self, tmp_path):
        """Test that workspace issues (with ::) don't trigger branch search."""
        issues_root = tmp_path / "Issues"
        issues_root.mkdir()
        
        with patch("monoco.features.issue.core.git.is_git_repo") as mock_is_git:
            mock_is_git.return_value = True
            
            # Project issues should be handled differently
            path, branch, conflicting = find_issue_path_across_branches(
                issues_root, "other::FEAT-0001", tmp_path
            )
            
            # Should return None since we don't have workspace setup
            # but importantly should not search branches
            assert path is None
            assert branch is None
            assert conflicting is None

    def test_invalid_issue_id(self, tmp_path):
        """Test handling of invalid issue IDs."""
        issues_root = tmp_path / "Issues"
        issues_root.mkdir()
        
        path, branch, conflicting = find_issue_path_across_branches(issues_root, "INVALID", tmp_path)
        
        assert path is None
        assert branch is None
        assert conflicting is None
