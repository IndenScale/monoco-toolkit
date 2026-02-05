"""
Git service for Issue operations.

Provides atomic commit functionality for issue file changes,
ensuring task state transitions are properly tracked in git history.
"""

import logging
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass

from monoco.core import git

logger = logging.getLogger("monoco.features.issue.git_service")


@dataclass
class CommitResult:
    """Result of a commit operation."""

    success: bool
    commit_hash: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class IssueGitService:
    """
    Service for handling git operations related to Issue files.

    Responsibilities:
    - Detect if current directory is in a git repository
    - Stage specific issue files
    - Generate atomic commit messages for issue transitions
    - Handle graceful degradation when not in a git repo
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._is_git_repo: Optional[bool] = None

    def is_git_repository(self) -> bool:
        """Check if the project root is inside a git repository."""
        if self._is_git_repo is None:
            self._is_git_repo = git.is_git_repo(self.project_root)
        return self._is_git_repo

    def commit_issue_change(
        self,
        issue_id: str,
        action: str,
        issue_file_path: Path,
        old_file_path: Optional[Path] = None,
        no_commit: bool = False,
    ) -> CommitResult:
        """
        Atomically commit an issue file change.

        Args:
            issue_id: The issue ID (e.g., "FEAT-0115")
            action: The action being performed (e.g., "close", "start", "open")
            issue_file_path: Current path to the issue file
            old_file_path: Previous path if the file was moved (e.g., status change)
            no_commit: If True, skip the commit operation

        Returns:
            CommitResult with success status and commit details
        """
        if no_commit:
            return CommitResult(success=True, message="Skipped (no-commit flag)")

        if not self.is_git_repository():
            logger.info("Not in a git repository, skipping auto-commit")
            return CommitResult(success=True, message="Skipped (not a git repo)")

        try:
            # Stage the changes
            self._stage_issue_files(issue_file_path, old_file_path)

            # Generate and execute commit
            commit_message = self._generate_commit_message(issue_id, action)
            commit_hash = git.git_commit(self.project_root, commit_message)

            return CommitResult(
                success=True,
                commit_hash=commit_hash,
                message=commit_message,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to commit issue change: {error_msg}")
            return CommitResult(success=False, error=error_msg)

    def _stage_issue_files(
        self, current_path: Path, old_path: Optional[Path] = None
    ) -> None:
        """
        Stage issue file changes.

        If old_path is provided (file was moved), handles the rename properly:
        - Stages deletion of old file
        - Stages addition of new file
        """
        files_to_stage: List[str] = []

        # Handle the old file path if file was moved (e.g., open -> closed)
        if old_path and old_path.exists():
            # File was moved, need to stage the deletion
            try:
                rel_old_path = old_path.relative_to(self.project_root)
                files_to_stage.append(str(rel_old_path))
            except ValueError:
                # old_path is not relative to project_root, use absolute
                files_to_stage.append(str(old_path))

        # Handle the current file path
        if current_path.exists():
            try:
                rel_path = current_path.relative_to(self.project_root)
                files_to_stage.append(str(rel_path))
            except ValueError:
                # current_path is not relative to project_root, use absolute
                files_to_stage.append(str(current_path))

        if files_to_stage:
            git.git_add(self.project_root, files_to_stage)

    def _generate_commit_message(self, issue_id: str, action: str) -> str:
        """
        Generate a standardized commit message for issue transitions.

        Format: chore(issue): <action> <issue_id>

        Examples:
            chore(issue): close FIX-0020
            chore(issue): start FEAT-0115
            chore(issue): open FEAT-0115
            chore(issue): submit FEAT-0115
        """
        return f"chore(issue): {action} {issue_id}"

    def get_commit_history(
        self, issue_id: str, max_count: int = 10
    ) -> List[Tuple[str, str]]:
        """
        Get commit history for a specific issue.

        Returns:
            List of (commit_hash, subject) tuples
        """
        if not self.is_git_repository():
            return []

        try:
            commits = git.search_commits_by_message(self.project_root, issue_id)
            return [(c["hash"], c["subject"]) for c in commits[:max_count]]
        except Exception:
            return []


def should_auto_commit(config) -> bool:
    """
    Check if auto-commit should be enabled based on configuration.

    Checks for:
    1. Explicit disable in config: issue.auto_commit = false
    2. Environment variable: MONOCO_NO_AUTO_COMMIT=1
    """
    import os

    # Check environment variable first
    if os.environ.get("MONOCO_NO_AUTO_COMMIT", "0") == "1":
        return False

    # Check config (if issue config has auto_commit setting)
    try:
        if hasattr(config, "issue") and hasattr(config.issue, "auto_commit"):
            return config.issue.auto_commit
    except Exception:
        pass

    # Default to enabled
    return True
