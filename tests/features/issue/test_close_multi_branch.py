"""
Tests for multi-branch conflict handling during issue close (CHORE-0036).

Ensures that `monoco issue close` correctly handles the case where an Issue file
exists in both main and feature branches by using the feature branch version.
"""

import pytest
import subprocess
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from monoco.features.issue.commands import app
from monoco.core import git

runner = CliRunner()


class TestMultiBranchIssueClose:
    """Test multi-branch conflict handling for issue close."""

    def _create_ready_issue_with_isolation(self, project_env):
        """Create an issue file directly with isolation info for review stage."""
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

    def _setup_branch_with_issue_and_changes(self, project_env):
        """Create feature branch with modified issue file and code changes."""
        # Create feature branch
        subprocess.run(["git", "checkout", "-b", "feat/feat-0001-test-feature"], cwd=project_env, check=True, capture_output=True)
        
        # Modify the issue file in feature branch (different content)
        issues_dir = project_env / "Issues" / "Features" / "open"
        issue_file = issues_dir / "FEAT-0001-test-feature.md"
        
        modified_content = """---
id: FEAT-0001
uid: test001
type: feature
status: open
stage: review
title: Test Feature Updated
created_at: '2026-01-01T00:00:00'
updated_at: '2026-01-02T00:00:00'
parent: EPIC-0001
dependencies: []
related: []
domains: []
tags:
  - '#EPIC-0001'
  - '#FEAT-0001'
files:
  - feature_code.py
  - another_file.py
isolation:
  type: branch
  ref: feat/feat-0001-test-feature
---

## FEAT-0001: Test Feature Updated

## Objective
Test objective modified in feature branch.

## Acceptance Criteria
- [x] Criteria met
- [x] Additional criteria met

## Technical Tasks
- [x] Task 1 completed
- [x] Task 2 completed

## Review Comments
Review passed with updates.
"""
        issue_file.write_text(modified_content)
        
        # Make some code changes
        feature_file = project_env / "feature_code.py"
        feature_file.write_text("# Feature code")
        another_file = project_env / "another_file.py"
        another_file.write_text("# Another file")
        
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Update issue and add feature code"], cwd=project_env, check=True, capture_output=True)
        
        # Go back to main
        subprocess.run(["git", "checkout", "main"], cwd=project_env, check=True, capture_output=True)

    def test_close_with_multi_branch_issue_uses_feature_version(self, project_env):
        """Test that close uses feature branch version when issue exists in both branches."""
        self._create_ready_issue_with_isolation(project_env)
        self._setup_branch_with_issue_and_changes(project_env)

        # Verify: main branch has old version
        issue_file = project_env / "Issues" / "Features" / "open" / "FEAT-0001-test-feature.md"
        main_content = issue_file.read_text()
        assert "Test Feature\n" in main_content  # Old title (without "Updated")
        
        # Verify: feature branch has new version
        subprocess.run(["git", "checkout", "feat/feat-0001-test-feature"], cwd=project_env, check=True, capture_output=True)
        feature_content = issue_file.read_text()
        assert "Test Feature Updated" in feature_content  # New title
        
        # Go back to main for close
        subprocess.run(["git", "checkout", "main"], cwd=project_env, check=True, capture_output=True)

        # Close should succeed and use feature branch version
        result = runner.invoke(app, [
            "close", "FEAT-0001",
            "--solution", "implemented",
            "--no-prune"
        ])

        # Should succeed
        assert result.exit_code == 0, f"Close failed: {result.stdout}"
        
        # Verify the feature branch version is used (title updated)
        # After close, issue file is moved to closed directory
        closed_issue_file = project_env / "Issues" / "Features" / "closed" / "FEAT-0001-test-feature.md"
        updated_content = closed_issue_file.read_text()
        assert "Test Feature Updated" in updated_content, "Should use feature branch version of issue file"
        
        # Verify the files field is updated (has both files from feature branch)
        assert "another_file.py" in updated_content, "Should have updated files list from feature branch"
        
        # Verify the code files are merged
        assert (project_env / "feature_code.py").exists(), "Feature code should be merged"
        assert (project_env / "another_file.py").exists(), "Another file should be merged"

    def test_close_with_multi_branch_shows_resolution_message(self, project_env):
        """Test that close shows a message when resolving multi-branch conflict."""
        self._create_ready_issue_with_isolation(project_env)
        self._setup_branch_with_issue_and_changes(project_env)

        # Close should show resolution message
        result = runner.invoke(app, [
            "close", "FEAT-0001",
            "--solution", "implemented",
            "--no-prune"
        ])

        # Should succeed
        assert result.exit_code == 0, f"Close failed: {result.stdout}"
        
        # Should show resolution message
        assert "Resolved" in result.stdout or "synced from feature branch" in result.stdout

    def test_close_single_branch_no_conflict(self, project_env):
        """Test that close works normally when issue only exists in main."""
        self._create_ready_issue_with_isolation(project_env)
        
        # Create feature branch but don't modify issue file
        subprocess.run(["git", "checkout", "-b", "feat/feat-0001-test-feature"], cwd=project_env, check=True, capture_output=True)
        feature_file = project_env / "feature_code.py"
        feature_file.write_text("# Feature code")
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add feature code"], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=project_env, check=True, capture_output=True)

        # Close should succeed without conflict
        result = runner.invoke(app, [
            "close", "FEAT-0001",
            "--solution", "implemented",
            "--no-prune"
        ])

        assert result.exit_code == 0, f"Close failed: {result.stdout}"
        
        # Verify the code file is merged
        assert (project_env / "feature_code.py").exists(), "Feature code should be merged"


class TestMultiBranchWithChineseFilename:
    """Test multi-branch handling with Chinese filenames (CHORE-0036)."""

    def _create_issue_with_chinese_title(self, project_env):
        """Create an issue with Chinese title."""
        # Create epic first
        result = runner.invoke(app, ["create", "epic", "-t", "Test Epic"])
        assert result.exit_code == 0

        issues_dir = project_env / "Issues" / "Features" / "open"
        issues_dir.mkdir(parents=True, exist_ok=True)
        
        # Issue with Chinese content
        issue_content = """---
id: FEAT-0002
uid: test002
type: feature
status: open
stage: review
title: 中文功能测试
created_at: '2026-01-01T00:00:00'
updated_at: '2026-01-01T00:00:00'
parent: EPIC-0001
dependencies: []
related: []
domains: []
tags:
  - '#EPIC-0001'
  - '#FEAT-0002'
files:
  - chinese_file.py
isolation:
  type: branch
  ref: feat/feat-0002
---

## FEAT-0002: 中文功能测试

## Objective
测试中文文件名处理。

## Acceptance Criteria
- [x] 标准已满足

## Technical Tasks
- [x] 任务完成

## Review Comments
Review passed.
"""
        issue_file = issues_dir / "FEAT-0002-中文功能测试.md"
        issue_file.write_text(issue_content)
        
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add Chinese issue file"], cwd=project_env, check=True, capture_output=True)

    def _setup_branch_with_chinese_changes(self, project_env):
        """Create feature branch with modified Chinese issue."""
        subprocess.run(["git", "checkout", "-b", "feat/feat-0002"], cwd=project_env, check=True, capture_output=True)
        
        issues_dir = project_env / "Issues" / "Features" / "open"
        issue_file = issues_dir / "FEAT-0002-中文功能测试.md"
        
        modified_content = """---
id: FEAT-0002
uid: test002
type: feature
status: open
stage: review
title: 中文功能测试已更新
created_at: '2026-01-01T00:00:00'
updated_at: '2026-01-02T00:00:00'
parent: EPIC-0001
dependencies: []
related: []
domains: []
tags:
  - '#EPIC-0001'
  - '#FEAT-0002'
files:
  - chinese_file.py
isolation:
  type: branch
  ref: feat/feat-0002
---

## FEAT-0002: 中文功能测试已更新

## Objective
测试中文文件名处理 - 已更新。

## Acceptance Criteria
- [x] 标准已满足
- [x] 额外标准

## Technical Tasks
- [x] 任务完成

## Review Comments
Review passed.
"""
        issue_file.write_text(modified_content)
        
        chinese_file = project_env / "chinese_file.py"
        chinese_file.write_text("# 中文注释")
        
        subprocess.run(["git", "add", "."], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Update Chinese issue"], cwd=project_env, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=project_env, check=True, capture_output=True)

    def test_close_with_chinese_filename(self, project_env):
        """Test that close handles Chinese filenames correctly."""
        self._create_issue_with_chinese_title(project_env)
        self._setup_branch_with_chinese_changes(project_env)

        # Close should succeed with Chinese filename
        result = runner.invoke(app, [
            "close", "FEAT-0002",
            "--solution", "implemented",
            "--no-prune"
        ])

        assert result.exit_code == 0, f"Close failed: {result.stdout}"
        
        # Verify the feature branch version is used
        # After close, issue file is moved to closed directory
        closed_issue_file = project_env / "Issues" / "Features" / "closed" / "FEAT-0002-中文功能测试.md"
        updated_content = closed_issue_file.read_text()
        assert "中文功能测试已更新" in updated_content, "Should use feature branch version"
        
        # Verify the code file is merged
        assert (project_env / "chinese_file.py").exists(), "Chinese file should be merged"
