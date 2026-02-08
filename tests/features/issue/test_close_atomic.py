"""
Tests for atomic close operation (FIX-0007).

Ensures that `monoco issue close` is an atomic operation:
- All steps successful -> commit all changes
- Any step fails -> rollback all changes, mainline stays clean
"""

import pytest
import subprocess
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from monoco.features.issue.commands import app
from monoco.core import git

runner = CliRunner()


class TestAtomicClose:
    """Test atomic transaction behavior for issue close."""

    def _create_ready_issue(self, project_env):
        """Create an issue file directly that passes validation for review stage."""
        # Create epic first
        result = runner.invoke(app, ["create", "epic", "-t", "Test Epic"])
        assert result.exit_code == 0

        # Create the feature issue file directly with proper content
        issues_dir = project_env / "Issues" / "Features" / "open"
        issues_dir.mkdir(parents=True, exist_ok=True)
        
        issue_content = """---
id: FEAT-0001
uid: test001
type: feature
status: open
stage: review
title: Test Feature
created_at: '2026-01-01T00:00:00'
updated_at: '2026-01-01T00:00:00'
parent: EPIC-0001
dependencies: []
related: []
domains: []
tags:
  - '#EPIC-0001'
  - '#FEAT-0001'
files:
  - feature_code.py
isolation:
  type: branch
  ref: feat/feat-0001-test-feature
---

## FEAT-0001: Test Feature

## Objective
Test objective.

## Acceptance Criteria
- [x] Criteria met

## Technical Tasks
- [x] Task 1 completed

## Review Comments
Review passed.
"""
        issue_file = issues_dir / "FEAT-0001-test-feature.md"
        issue_file.write_text(issue_content)
        
        # Commit the issue file
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add issue file"], cwd=project_env, check=True, capture_output=True)

    def _setup_branch_with_changes(self, project_env):
        """Create feature branch with changes."""
        # Create feature branch
        subprocess.run(["git", "checkout", "-b", "feat/feat-0001-test-feature"], cwd=project_env, check=True, capture_output=True)
        
        # Make some changes
        feature_file = project_env / "feature_code.py"
        feature_file.write_text("# Feature code")
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add feature code"], cwd=project_env, check=True, capture_output=True)
        
        # Go back to main
        subprocess.run(["git", "checkout", "main"], cwd=project_env, check=True, capture_output=True)

    def test_close_atomic_rollback_on_update_failure(self, project_env):
        """Test that atomic merge commit is rolled back when update_issue fails."""
        self._create_ready_issue(project_env)
        self._setup_branch_with_changes(project_env)

        # Get initial HEAD
        initial_head = git.get_current_head(project_env)

        # Mock update_issue to simulate failure after merge
        with patch("monoco.features.issue.commands.core.update_issue") as mock_update:
            mock_update.side_effect = Exception("Simulated update failure: 'str' object has no attribute 'value'")

            # Attempt to close - should fail and rollback
            result = runner.invoke(app, [
                "close", "FEAT-0001",
                "--solution", "implemented"
            ])

            # Should exit with error
            assert result.exit_code == 1
            combined_output = result.stdout + (result.stderr or "")
            assert ("Update Error" in combined_output or
                    "Simulated update failure" in combined_output or
                    "Rolled back" in combined_output)

        # Verify HEAD is back to initial (rollback occurred)
        current_head = git.get_current_head(project_env)
        assert current_head == initial_head, f"Expected rollback to {initial_head[:7]}, but at {current_head[:7]}"

        # Verify the atomic merge commit was rolled back
        # (feature_code.py should not exist on main)
        assert not (project_env / "feature_code.py").exists(), "Feature code should have been rolled back"

    def test_close_success_no_rollback(self, project_env):
        """Test successful close does not rollback."""
        self._create_ready_issue(project_env)
        self._setup_branch_with_changes(project_env)

        # Get initial HEAD
        initial_head = git.get_current_head(project_env)

        # Close should succeed
        result = runner.invoke(app, [
            "close", "FEAT-0001",
            "--solution", "implemented"
        ])

        # Should succeed
        assert result.exit_code == 0, f"Close failed: {result.stdout}"

        # Verify HEAD changed (new commits were made)
        current_head = git.get_current_head(project_env)
        assert current_head != initial_head, "HEAD should have changed after successful close"

        # Verify the feature code was merged
        assert (project_env / "feature_code.py").exists(), "Feature code should exist after successful close"

    def test_close_atomic_rollback_on_prune_failure(self, project_env):
        """Test that all changes are rolled back when prune fails."""
        self._create_ready_issue(project_env)
        self._setup_branch_with_changes(project_env)

        # Get initial HEAD
        initial_head = git.get_current_head(project_env)

        # Mock the entire prune section by mocking the console.print to trigger error
        # Actually, let's mock the prune_issue_resources and force the error to happen
        with patch("monoco.features.issue.commands.core.prune_issue_resources") as mock_prune:
            mock_prune.side_effect = Exception("Simulated prune failure")

            # Attempt to close - should fail and rollback
            result = runner.invoke(app, [
                "close", "FEAT-0001",
                "--solution", "implemented"
            ])

            # Should exit with error - check for rollback message since that's what we care about
            assert result.exit_code == 1
            # The error might be caught at different stages, but rollback should always happen
            assert "Rolled back" in result.stdout or "rollback" in result.stdout.lower() or "Simulated prune failure" in result.stdout

        # Verify HEAD is back to initial (rollback occurred)
        current_head = git.get_current_head(project_env)
        assert current_head == initial_head, f"Expected rollback to {initial_head[:7]}, but at {current_head[:7]}"

    def test_close_rollback_message_displayed(self, project_env):
        """Test that rollback message is displayed to user on failure."""
        self._create_ready_issue(project_env)
        self._setup_branch_with_changes(project_env)

        # Mock update_issue to simulate failure
        with patch("monoco.features.issue.commands.core.update_issue") as mock_update:
            mock_update.side_effect = Exception("Simulated failure")

            # Attempt to close
            result = runner.invoke(app, [
                "close", "FEAT-0001",
                "--solution", "implemented"
            ])

            # Should show rollback message
            assert "Rolled back" in result.stdout or "rollback" in result.stdout.lower()


class TestGitHelpers:
    """Test git helper functions for atomic operations."""

    def test_get_current_head(self, project_env):
        """Test get_current_head returns valid commit hash."""
        head = git.get_current_head(project_env)
        assert len(head) == 40  # SHA-1 hash length
        assert all(c in "0123456789abcdef" for c in head.lower())

    def test_git_reset_hard(self, project_env):
        """Test git_reset_hard correctly resets to specified commit."""
        # Create a file and commit it
        test_file = project_env / "test_reset.txt"
        test_file.write_text("version 1")
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add test file"], cwd=project_env, check=True, capture_output=True)

        # Record this commit
        first_commit = git.get_current_head(project_env)

        # Make another commit
        test_file.write_text("version 2")
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Update test file"], cwd=project_env, check=True, capture_output=True)

        # Verify we're at new commit
        second_commit = git.get_current_head(project_env)
        assert second_commit != first_commit

        # Reset to first commit
        git.git_reset_hard(project_env, first_commit)

        # Verify we're back at first commit
        current = git.get_current_head(project_env)
        assert current == first_commit
        assert test_file.read_text() == "version 1"
