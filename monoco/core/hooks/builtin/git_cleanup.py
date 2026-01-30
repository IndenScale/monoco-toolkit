"""
GitCleanupHook - Performs git cleanup operations when a session ends.

This hook ensures that:
1. Current branch is switched back to main (if safe)
2. Feature branches are deleted if the associated issue is completed/merged
"""

import logging
from typing import Optional

from ..base import SessionLifecycleHook, HookResult, HookStatus
from ..context import HookContext

logger = logging.getLogger("monoco.core.hooks.git_cleanup")


class GitCleanupHook(SessionLifecycleHook):
    """
    Hook for cleaning up git state when a session ends.
    
    Configuration options:
        - auto_switch_to_main: Whether to automatically switch to main branch (default: True)
        - auto_delete_merged_branches: Whether to delete merged feature branches (default: True)
        - main_branch: Name of the main branch (default: "main", fallback: "master")
        - require_clean_worktree: Whether to require clean worktree before operations (default: True)
    """

    def __init__(self, name: Optional[str] = None, config: Optional[dict] = None):
        super().__init__(name=name or "git_cleanup", config=config)
        
        # Configuration with defaults
        self.auto_switch_to_main = self.config.get("auto_switch_to_main", True)
        self.auto_delete_merged_branches = self.config.get("auto_delete_merged_branches", True)
        self.main_branch = self.config.get("main_branch", "main")
        self.require_clean_worktree = self.config.get("require_clean_worktree", True)

    def on_session_start(self, context: HookContext) -> HookResult:
        """
        Called when session starts.
        
        No action needed at session start for git cleanup.
        """
        return HookResult.success("Git cleanup hook initialized")

    def on_session_end(self, context: HookContext) -> HookResult:
        """
        Called when session ends.
        
        Performs cleanup operations:
        1. Check current git state
        2. Switch to main branch if needed and safe
        3. Delete feature branch if issue is completed
        """
        if not context.git:
            return HookResult.skipped("No git context available")
        
        project_root = context.git.project_root
        
        try:
            from monoco.core import git
            
            # Check if we're in a git repo
            if not git.is_git_repo(project_root):
                return HookResult.skipped("Not a git repository")
            
            # Get current state
            current_branch = git.get_current_branch(project_root)
            default_branch = self._get_default_branch(project_root)
            
            # Check for uncommitted changes
            has_changes = len(git.get_git_status(project_root)) > 0
            
            results = []
            
            # Step 1: Switch to main branch if needed
            if self.auto_switch_to_main and current_branch != default_branch:
                switch_result = self._switch_to_main(
                    project_root, current_branch, default_branch, has_changes
                )
                results.append(switch_result)
                
                if switch_result.status == HookStatus.SUCCESS:
                    current_branch = default_branch
            
            # Step 2: Delete feature branch if issue is completed
            if self.auto_delete_merged_branches and context.issue:
                delete_result = self._cleanup_feature_branch(
                    project_root, context.issue, default_branch, current_branch
                )
                if delete_result:
                    results.append(delete_result)
            
            # Combine results
            failures = [r for r in results if r.status == HookStatus.FAILURE]
            warnings = [r for r in results if r.status == HookStatus.WARNING]
            
            if failures:
                return HookResult.failure(
                    f"Git cleanup completed with {len(failures)} failures",
                    {"results": [r.message for r in results]}
                )
            elif warnings:
                return HookResult.warning(
                    f"Git cleanup completed with {len(warnings)} warnings",
                    {"results": [r.message for r in results]}
                )
            else:
                return HookResult.success(
                    "Git cleanup completed successfully",
                    {"results": [r.message for r in results]}
                )
                
        except Exception as e:
            logger.error(f"Git cleanup failed: {e}")
            return HookResult.failure(f"Git cleanup failed: {e}")

    def _get_default_branch(self, project_root) -> str:
        """Determine the default branch (main or master)."""
        from monoco.core import git
        
        if git.branch_exists(project_root, self.main_branch):
            return self.main_branch
        elif git.branch_exists(project_root, "master"):
            return "master"
        return self.main_branch

    def _switch_to_main(
        self, 
        project_root, 
        current_branch: str, 
        default_branch: str,
        has_changes: bool
    ) -> HookResult:
        """
        Switch to the main branch if safe to do so.
        
        Args:
            project_root: The project root path
            current_branch: Current branch name
            default_branch: Target branch name (main/master)
            has_changes: Whether there are uncommitted changes
            
        Returns:
            HookResult indicating success/failure
        """
        from monoco.core import git
        
        # Safety check: uncommitted changes
        if has_changes and self.require_clean_worktree:
            return HookResult.warning(
                f"Cannot switch from '{current_branch}' to '{default_branch}': "
                f"uncommitted changes exist. Please commit or stash changes."
            )
        
        # Check if default branch exists
        if not git.branch_exists(project_root, default_branch):
            return HookResult.warning(
                f"Cannot switch to '{default_branch}': branch does not exist"
            )
        
        try:
            git.checkout_branch(project_root, default_branch)
            return HookResult.success(
                f"Switched from '{current_branch}' to '{default_branch}'"
            )
        except Exception as e:
            return HookResult.failure(
                f"Failed to switch to '{default_branch}': {e}"
            )

    def _cleanup_feature_branch(
        self,
        project_root,
        issue,
        default_branch: str,
        current_branch: str
    ) -> Optional[HookResult]:
        """
        Clean up the feature branch associated with an issue.
        
        Args:
            project_root: The project root path
            issue: The IssueInfo object
            default_branch: The default branch name
            current_branch: Current branch name
            
        Returns:
            HookResult or None if no action needed
        """
        from monoco.core import git
        
        # Get the branch name from issue
        branch_name = issue.branch_name
        if not branch_name:
            # Try to infer from convention: feat/<issue_id>-*
            # This is a fallback if isolation metadata is not set
            return None
        
        # Check if branch exists
        if not git.branch_exists(project_root, branch_name):
            return None
        
        # Safety: don't delete the branch we're currently on
        if current_branch == branch_name:
            return HookResult.warning(
                f"Cannot delete branch '{branch_name}': currently checked out"
            )
        
        # Check if issue is completed/closed
        is_completed = issue.status in ("closed", "done", "merged")
        
        if not is_completed:
            return HookResult.skipped(
                f"Branch '{branch_name}' not deleted: issue status is '{issue.status}'"
            )
        
        # Check if branch is merged into default branch
        try:
            is_merged = self._is_branch_merged(project_root, branch_name, default_branch)
        except Exception:
            is_merged = False
        
        if not is_merged:
            return HookResult.warning(
                f"Branch '{branch_name}' not deleted: not merged into '{default_branch}'"
            )
        
        # Safe to delete
        try:
            git.delete_branch(project_root, branch_name, force=False)
            return HookResult.success(
                f"Deleted merged branch '{branch_name}'"
            )
        except Exception as e:
            return HookResult.failure(
                f"Failed to delete branch '{branch_name}': {e}"
            )

    def _is_branch_merged(
        self, 
        project_root, 
        branch: str, 
        target: str
    ) -> bool:
        """
        Check if a branch is merged into the target branch.
        
        Args:
            project_root: The project root path
            branch: The branch to check
            target: The target branch to check against
            
        Returns:
            True if branch is merged into target
        """
        from monoco.core import git
        
        # Use git merge-base to check if branch is ancestor of target
        code, stdout, _ = git._run_git(
            ["merge-base", "--is-ancestor", branch, target],
            project_root
        )
        
        # Exit code 0 means branch is ancestor of target (merged)
        return code == 0
