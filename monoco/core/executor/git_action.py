"""
Git Actions - Actions for git operations.

Part of Layer 3 (Action Executor) in the event automation framework.
Provides actions for git commit and push operations.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from monoco.core.scheduler import AgentEvent
from monoco.core.router import Action, ActionResult

logger = logging.getLogger(__name__)


class GitResult:
    """Result of a git command execution."""
    
    def __init__(
        self,
        returncode: int,
        stdout: str,
        stderr: str,
    ):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
    
    @property
    def success(self) -> bool:
        return self.returncode == 0


class GitCommitAction(Action):
    """
    Action that performs git commit.
    
    This action stages files and creates a git commit with a message.
    
    Example:
        >>> action = GitCommitAction(
        ...     message="Auto-commit: {issue_id}",
        ...     files=["*.py"],
        ...     add_all=False,
        ... )
        >>> result = await action(event)
    """
    
    def __init__(
        self,
        message: str,
        files: Optional[List[str]] = None,
        add_all: bool = False,
        working_dir: Optional[Path] = None,
        timeout: int = 30,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self.message = message
        self.files = files or []
        self.add_all = add_all
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout
        self._last_result: Optional[GitResult] = None
    
    @property
    def name(self) -> str:
        return "GitCommitAction"
    
    async def can_execute(self, event: AgentEvent) -> bool:
        """Check if we're in a git repository."""
        git_dir = self.working_dir / ".git"
        return git_dir.exists()
    
    async def execute(self, event: AgentEvent) -> ActionResult:
        """Perform git commit."""
        # Format message with event data
        formatted_message = self._format_message(event)
        
        logger.info(f"Performing git commit: {formatted_message[:50]}...")
        
        try:
            # Stage files
            if self.add_all:
                await self._run_git_command(["git", "add", "-A"])
            elif self.files:
                for file_pattern in self.files:
                    await self._run_git_command(["git", "add", file_pattern])
            
            # Check if there are changes to commit
            status_result = await self._run_git_command(
                ["git", "status", "--porcelain"]
            )
            
            if not status_result.stdout.strip():
                logger.info("No changes to commit")
                return ActionResult.success_result(
                    output={"committed": False, "reason": "no_changes"},
                )
            
            # Commit
            commit_result = await self._run_git_command(
                ["git", "commit", "-m", formatted_message]
            )
            self._last_result = commit_result
            
            if commit_result.success:
                # Get commit hash
                hash_result = await self._run_git_command(
                    ["git", "rev-parse", "HEAD"]
                )
                commit_hash = hash_result.stdout.strip()
                
                return ActionResult.success_result(
                    output={
                        "committed": True,
                        "commit_hash": commit_hash,
                        "message": formatted_message,
                    },
                )
            else:
                return ActionResult.failure_result(
                    error=f"Git commit failed: {commit_result.stderr}",
                )
        
        except Exception as e:
            logger.error(f"Git commit failed: {e}")
            return ActionResult.failure_result(error=str(e))
    
    def _format_message(self, event: AgentEvent) -> str:
        """Format commit message with event data."""
        try:
            return self.message.format(**event.payload)
        except (KeyError, ValueError):
            # If formatting fails, return original message
            return self.message
    
    async def _run_git_command(self, cmd: List[str]) -> GitResult:
        """Execute a git command."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir,
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            raise RuntimeError(f"Git command timed out: {' '.join(cmd)}")
        
        return GitResult(
            returncode=process.returncode,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get action statistics."""
        stats = super().get_stats()
        stats.update({
            "working_dir": str(self.working_dir),
            "message_template": self.message,
        })
        return stats


class GitPushAction(Action):
    """
    Action that performs git push.
    
    This action pushes commits to a remote repository.
    
    Example:
        >>> action = GitPushAction(
        ...     remote="origin",
        ...     branch="main",
        ... )
        >>> result = await action(event)
    """
    
    def __init__(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        working_dir: Optional[Path] = None,
        timeout: int = 60,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self.remote = remote
        self.branch = branch
        self.force = force
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout
        self._last_result: Optional[GitResult] = None
    
    @property
    def name(self) -> str:
        return "GitPushAction"
    
    async def can_execute(self, event: AgentEvent) -> bool:
        """Check if we're in a git repository with a remote."""
        git_dir = self.working_dir / ".git"
        if not git_dir.exists():
            return False
        
        # Check if remote exists
        try:
            result = await self._run_git_command(
                ["git", "remote", "get-url", self.remote]
            )
            return result.success
        except Exception:
            return False
    
    async def execute(self, event: AgentEvent) -> ActionResult:
        """Perform git push."""
        # Determine branch
        branch = self.branch
        if not branch:
            # Get current branch
            result = await self._run_git_command(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"]
            )
            if result.success:
                branch = result.stdout.strip()
            else:
                return ActionResult.failure_result(
                    error="Could not determine current branch"
                )
        
        logger.info(f"Pushing to {self.remote}/{branch}")
        
        try:
            # Build command
            cmd = ["git", "push", self.remote, branch]
            if self.force:
                cmd.append("--force-with-lease")
            
            result = await self._run_git_command(cmd)
            self._last_result = result
            
            if result.success:
                return ActionResult.success_result(
                    output={
                        "pushed": True,
                        "remote": self.remote,
                        "branch": branch,
                    },
                )
            else:
                return ActionResult.failure_result(
                    error=f"Git push failed: {result.stderr}",
                )
        
        except Exception as e:
            logger.error(f"Git push failed: {e}")
            return ActionResult.failure_result(error=str(e))
    
    async def _run_git_command(self, cmd: List[str]) -> GitResult:
        """Execute a git command."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir,
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            raise RuntimeError(f"Git command timed out: {' '.join(cmd)}")
        
        return GitResult(
            returncode=process.returncode,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get action statistics."""
        stats = super().get_stats()
        stats.update({
            "working_dir": str(self.working_dir),
            "remote": self.remote,
            "branch": self.branch or "auto",
        })
        return stats
