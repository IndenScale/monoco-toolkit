"""
Tests for sync-files uncommitted changes detection (CHORE-0036).

Ensures that `monoco issue sync-files` raises an error when there are
uncommitted changes in the working directory.
"""

import pytest
import subprocess
from pathlib import Path
from typer.testing import CliRunner
from monoco.features.issue.commands import app
from monoco.features.issue import core

runner = CliRunner()


class TestSyncFilesUncommitted:
    """Test sync-files uncommitted changes detection."""

    def _create_ready_issue(self, project_env):
        """Create an issue file ready for testing."""
        issues_dir = project_env / "Issues" / "Features" / "open"
        issues_dir.mkdir(parents=True, exist_ok=True)
        
        issue_content = """---
id: FEAT-0001
uid: test001
type: feature
status: open
stage: doing
title: Test Feature
created_at: '2026-01-01T00:00:00'
updated_at: '2026-01-01T00:00:00'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
  - '#EPIC-0000'
  - '#FEAT-0001'
files: []
isolation:
  type: branch
  ref: feat/feat-0001-test-feature
---

## FEAT-0001: Test Feature

## Objective
Test.

## Acceptance Criteria
- [ ] Criteria

## Technical Tasks
- [ ] Task

## Review Comments
"""
        issue_file = issues_dir / "FEAT-0001-test-feature.md"
        issue_file.write_text(issue_content)
        
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add issue"], cwd=project_env, check=True, capture_output=True)

    def _create_feature_branch(self, project_env):
        """Create feature branch."""
        subprocess.run(["git", "checkout", "-b", "feat/feat-0001-test-feature"], 
                      cwd=project_env, check=True, capture_output=True)

    def test_sync_files_rejects_uncommitted_changes(self, project_env):
        """Test that sync-files raises error when there are uncommitted changes."""
        self._create_ready_issue(project_env)
        self._create_feature_branch(project_env)

        # Create an uncommitted file
        uncommitted_file = project_env / "uncommitted.py"
        uncommitted_file.write_text("# Uncommitted code")
        # Don't commit it!

        # sync-files should raise error
        with pytest.raises(RuntimeError) as exc_info:
            core.sync_issue_files(
                project_env / "Issues",
                "FEAT-0001",
                project_env
            )
        
        assert "Uncommitted changes detected" in str(exc_info.value)
        assert "uncommitted.py" in str(exc_info.value)
        assert "git add" in str(exc_info.value)
        assert "git checkout" in str(exc_info.value)
        assert ".gitignore" in str(exc_info.value)

    def test_sync_files_accepts_committed_changes(self, project_env):
        """Test that sync-files works when all changes are committed."""
        self._create_ready_issue(project_env)
        self._create_feature_branch(project_env)

        # Create and commit a file
        committed_file = project_env / "committed.py"
        committed_file.write_text("# Committed code")
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add committed file"], 
                      cwd=project_env, check=True, capture_output=True)

        # sync-files should work
        changed_files = core.sync_issue_files(
            project_env / "Issues",
            "FEAT-0001",
            project_env
        )
        
        # Should return the committed file
        assert "committed.py" in changed_files

    def test_sync_files_rejects_untracked_files(self, project_env):
        """Test that sync-files raises error for untracked files."""
        self._create_ready_issue(project_env)
        self._create_feature_branch(project_env)

        # Create an untracked file (not added to git)
        untracked_file = project_env / "untracked.py"
        untracked_file.write_text("# Untracked code")
        # Don't add or commit!

        # sync-files should raise error
        with pytest.raises(RuntimeError) as exc_info:
            core.sync_issue_files(
                project_env / "Issues",
                "FEAT-0001",
                project_env
            )
        
        assert "Uncommitted changes detected" in str(exc_info.value)
        assert "untracked.py" in str(exc_info.value)

    def test_has_uncommitted_changes_helper(self, project_env):
        """Test the _has_uncommitted_changes helper function."""
        self._create_ready_issue(project_env)
        self._create_feature_branch(project_env)

        # Initially no changes
        has_changes, files = core._has_uncommitted_changes(project_env)
        assert not has_changes
        assert files == []

        # Create uncommitted file
        uncommitted_file = project_env / "test.py"
        uncommitted_file.write_text("# test")
        
        has_changes, files = core._has_uncommitted_changes(project_env)
        assert has_changes
        assert "test.py" in files

    def test_sync_files_rejects_staged_but_uncommitted(self, project_env):
        """Test that sync-files raises error for staged but uncommitted files."""
        self._create_ready_issue(project_env)
        self._create_feature_branch(project_env)

        # Create and stage a file, but don't commit
        staged_file = project_env / "staged.py"
        staged_file.write_text("# Staged code")
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        # Don't commit!

        # sync-files should raise error
        with pytest.raises(RuntimeError) as exc_info:
            core.sync_issue_files(
                project_env / "Issues",
                "FEAT-0001",
                project_env
            )
        
        assert "Uncommitted changes detected" in str(exc_info.value)
        assert "staged.py" in str(exc_info.value)
