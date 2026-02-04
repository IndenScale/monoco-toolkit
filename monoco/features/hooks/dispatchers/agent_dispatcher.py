"""
Agent Hooks Dispatcher for Universal Hooks system.

Manages distribution and execution of Agent-specific hooks
(e.g., for Claude Code, Gemini CLI).
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from ..manager import HookDispatcher
from ..models import HookType, ParsedHook


class AgentHookDispatcher(HookDispatcher):
    """
    Dispatcher for Agent lifecycle hooks.

    Responsible for:
    - Distributing hook scripts to agent-specific directories (e.g., .claude/hooks/)
    - Managing provider-specific hook conventions
    """

    def __init__(self, provider: str):
        """
        Initialize the Agent hook dispatcher.

        Args:
            provider: The agent provider (e.g., 'claude-code')
        """
        super().__init__(HookType.AGENT, provider=provider)

    def can_execute(self, hook: ParsedHook) -> bool:
        """Check if this dispatcher can execute the given hook."""
        return (
            hook.metadata.type == HookType.AGENT
            and hook.metadata.provider == self.provider
        )

    def execute(self, hook: ParsedHook, context: Optional[dict] = None) -> bool:
        """
        Execute an agent hook directly.
        
        Most agent hooks are executed by the agent framework itself
        after being distributed. Direct execution is used for testing.
        """
        # TODO: Implement direct execution if needed
        return True

    def install(self, hook: ParsedHook, project_root: Path) -> bool:
        """
        Distribute hook script to agent-specific directory.

        Args:
            hook: The parsed hook to install
            project_root: The project root directory

        Returns:
            True if installation succeeded
        """
        target_dir = self._get_target_dir(project_root)
        if not target_dir:
            return False

        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / hook.script_path.name

        try:
            shutil.copy2(hook.script_path, target_path)
            os.chmod(target_path, 0o755)
            return True
        except Exception:
            return False

    def uninstall(self, hook_name: str, project_root: Path) -> bool:
        """Remove a hook script from agent-specific directory."""
        target_dir = self._get_target_dir(project_root)
        if not target_dir:
            return False

        target_path = target_dir / hook_name
        if target_path.exists():
            target_path.unlink()
        return True

    def _get_target_dir(self, project_root: Path) -> Optional[Path]:
        """Get the distribution directory based on provider."""
        if self.provider == "claude-code":
            return project_root / ".claude" / "hooks"
        elif self.provider == "gemini-cli":
            return project_root / ".gemini" / "hooks"
        # Add other providers as needed
        return None
