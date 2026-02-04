"""
Agent Hooks Dispatcher for Universal Hooks system.

Manages distribution and execution of Agent-specific hooks
(e.g., for Claude Code, Gemini CLI) using the ACL (Anti-Corruption Layer) pattern.

Instead of directly copying hook scripts, this dispatcher injects configurations
into agent-specific settings files (e.g., .claude/settings.json) that invoke
the Universal Interceptor for protocol translation.
"""

import json
import os
from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional

from ..manager import HookDispatcher
from ..models import AgentEvent, HookType, ParsedHook


class AgentHookDispatcher(HookDispatcher):
    """
    Base dispatcher for Agent lifecycle hooks with ACL support.

    Responsible for:
    - Injecting hook configurations into agent-specific settings files
    - Managing provider-specific hook conventions and protocol translation
    - Auto-detecting agent environments via environment variables

    The ACL pattern ensures that hooks written for the Monoco unified protocol
can work across different agent platforms without modification.
    """

    # Environment variable names for auto-detection
    ENV_CLAUDE_CODE_REMOTE = "CLAUDE_CODE_REMOTE"
    ENV_GEMINI_ENV_FILE = "GEMINI_ENV_FILE"

    # Settings file paths (relative to project root)
    CLAUDE_SETTINGS_PATH = ".claude/settings.json"
    GEMINI_SETTINGS_PATH = ".gemini/settings.json"

    def __init__(self, provider: str):
        """
        Initialize the Agent hook dispatcher.

        Args:
            provider: The agent provider (e.g., 'claude-code', 'gemini-cli')
        """
        super().__init__(HookType.AGENT, provider=provider)

    @abstractmethod
    def get_settings_path(self, project_root: Path) -> Optional[Path]:
        """Get the path to the agent's settings file."""
        pass

    @abstractmethod
    def translate_event(self, monoco_event: str) -> str:
        """
        Translate Monoco event name to agent-specific event name.

        Args:
            monoco_event: Event name in Monoco unified protocol

        Returns:
            Agent-specific event name
        """
        pass

    @abstractmethod
    def generate_hook_config(self, hook: ParsedHook) -> dict[str, Any]:
        """
        Generate agent-specific hook configuration.

        Args:
            hook: The parsed hook to generate config for

        Returns:
            Agent-specific hook configuration dictionary
        """
        pass

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
        after being configured. Direct execution is used for testing.
        """
        # TODO: Implement direct execution via Universal Interceptor if needed
        return True

    def is_available(self, project_root: Path) -> bool:
        """
        Check if this agent environment is available.

        Returns True if either:
        1. The agent's settings directory exists
        2. The corresponding environment variable is set

        Args:
            project_root: The project root directory

        Returns:
            True if this agent is available
        """
        settings_path = self.get_settings_path(project_root)
        if settings_path and settings_path.exists():
            return True

        # Check environment variables
        if self.provider == "claude-code":
            return os.environ.get(self.ENV_CLAUDE_CODE_REMOTE) is not None
        elif self.provider == "gemini-cli":
            return os.environ.get(self.ENV_GEMINI_ENV_FILE) is not None

        return False

    def install(self, hook: ParsedHook, project_root: Path) -> bool:
        """
        Install a hook by injecting configuration into agent settings.

        Args:
            hook: The parsed hook to install
            project_root: The project root directory

        Returns:
            True if installation succeeded
        """
        settings_path = self.get_settings_path(project_root)
        if not settings_path:
            return False

        try:
            # Load existing settings or create new
            settings = self._load_settings(settings_path)

            # Generate hook configuration
            hook_config = self.generate_hook_config(hook)

            # Inject into settings
            self._inject_hook_config(settings, hook_config, hook)

            # Save settings
            self._save_settings(settings_path, settings)

            return True
        except Exception:
            return False

    def uninstall(self, hook_name: str, project_root: Path) -> bool:
        """
        Remove a hook configuration from agent settings.

        Args:
            hook_name: The name/identifier of the hook to remove
            project_root: The project root directory

        Returns:
            True if uninstallation succeeded
        """
        settings_path = self.get_settings_path(project_root)
        if not settings_path or not settings_path.exists():
            return True  # Already uninstalled

        try:
            settings = self._load_settings(settings_path)

            # Remove hook configurations that match the name
            self._remove_hook_config(settings, hook_name)

            # Save settings
            self._save_settings(settings_path, settings)

            return True
        except Exception:
            return False

    def sync(
        self,
        hooks: list[ParsedHook],
        project_root: Path,
    ) -> dict[str, bool]:
        """
        Synchronize all agent hooks with the settings file.

        Args:
            hooks: List of parsed hooks to sync
            project_root: The project root directory

        Returns:
            Dictionary mapping hook names to success status
        """
        results = {}

        settings_path = self.get_settings_path(project_root)
        if not settings_path:
            return results

        try:
            # Load or create settings
            settings = self._load_settings(settings_path)

            # Clear existing Monoco-managed hooks
            self._clear_monoco_hooks(settings)

            # Install current hooks
            for hook in hooks:
                if not self.can_execute(hook):
                    continue

                hook_config = self.generate_hook_config(hook)
                self._inject_hook_config(settings, hook_config, hook)
                results[hook.script_path.name] = True

            # Save settings
            self._save_settings(settings_path, settings)

        except Exception as e:
            for hook in hooks:
                if self.can_execute(hook):
                    results[hook.script_path.name] = False

        return results

    def _load_settings(self, settings_path: Path) -> dict[str, Any]:
        """Load settings from file or return empty dict."""
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_settings(self, settings_path: Path, settings: dict[str, Any]) -> None:
        """Save settings to file."""
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

    def _inject_hook_config(
        self,
        settings: dict[str, Any],
        hook_config: dict[str, Any],
        hook: ParsedHook,
    ) -> None:
        """
        Inject hook configuration into settings.

        Args:
            settings: The settings dictionary to modify
            hook_config: The hook configuration to inject
            hook: The parsed hook for metadata
        """
        if "hooks" not in settings:
            settings["hooks"] = {}

        agent_event = self.translate_event(hook.metadata.event)

        if agent_event not in settings["hooks"]:
            settings["hooks"][agent_event] = []

        # Add marker to identify as Monoco-managed
        hook_config["_monoco_managed"] = True
        hook_config["_monoco_hook_id"] = hook.script_path.stem

        settings["hooks"][agent_event].append(hook_config)

    def _remove_hook_config(self, settings: dict[str, Any], hook_name: str) -> None:
        """
        Remove hook configuration from settings.

        Args:
            settings: The settings dictionary to modify
            hook_name: The name/identifier of the hook to remove
        """
        if "hooks" not in settings:
            return

        for event, configs in list(settings["hooks"].items()):
            if isinstance(configs, list):
                settings["hooks"][event] = [
                    c for c in configs
                    if not (c.get("_monoco_managed") and c.get("_monoco_hook_id") == hook_name)
                ]

    def _clear_monoco_hooks(self, settings: dict[str, Any]) -> None:
        """Remove all Monoco-managed hooks from settings."""
        if "hooks" not in settings:
            return

        for event, configs in list(settings["hooks"].items()):
            if isinstance(configs, list):
                settings["hooks"][event] = [
                    c for c in configs if not c.get("_monoco_managed")
                ]


class ClaudeCodeDispatcher(AgentHookDispatcher):
    """
    Dispatcher for Claude Code agent hooks.

    Injects hook configurations into `.claude/settings.json`.

    Event Mapping (Monoco -> Claude):
        - session-start -> SessionStart
        - before-tool -> PreToolUse
        - after-tool -> PostToolUse
        - before-agent -> UserPromptSubmit
        - after-agent -> Stop
        - session-end -> SessionEnd
    """

    # Event mapping from Monoco unified protocol to Claude Code
    EVENT_MAP = {
        "session-start": "SessionStart",
        "before-tool": "PreToolUse",
        "after-tool": "PostToolUse",
        "before-agent": "UserPromptSubmit",
        "after-agent": "Stop",
        "session-end": "SessionEnd",
    }

    def __init__(self):
        """Initialize the Claude Code dispatcher."""
        super().__init__(provider="claude-code")

    def get_settings_path(self, project_root: Path) -> Optional[Path]:
        """Get the path to Claude Code's settings file."""
        return project_root / self.CLAUDE_SETTINGS_PATH

    def translate_event(self, monoco_event: str) -> str:
        """Translate Monoco event to Claude Code event name."""
        return self.EVENT_MAP.get(monoco_event, monoco_event)

    def generate_hook_config(self, hook: ParsedHook) -> dict[str, Any]:
        """
        Generate Claude Code hook configuration.

        Claude Code uses a matcher-based configuration:
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": "monoco hook run agent before-tool"
                }
            ]
        }
        """
        agent_event = self.translate_event(hook.metadata.event)

        # Build the command that invokes the Universal Interceptor
        # The interceptor will handle protocol translation
        command = f"monoco hook run agent {hook.metadata.event}"

        config: dict[str, Any] = {
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                }
            ]
        }

        # Add matcher if specified in metadata
        if hook.metadata.matcher:
            # For Claude Code, matcher can be a tool name or pattern
            config["matcher"] = hook.metadata.matcher[0] if hook.metadata.matcher else "*"

        return config


class GeminiDispatcher(AgentHookDispatcher):
    """
    Dispatcher for Gemini CLI agent hooks.

    Injects hook configurations into `.gemini/settings.json`.

    Event Mapping (Monoco -> Gemini):
        - session-start -> SessionStart
        - before-tool -> BeforeTool
        - after-tool -> AfterTool
        - before-agent -> BeforeAgent
        - after-agent -> AfterAgent
        - session-end -> SessionEnd
    """

    # Event mapping from Monoco unified protocol to Gemini CLI
    EVENT_MAP = {
        "session-start": "SessionStart",
        "before-tool": "BeforeTool",
        "after-tool": "AfterTool",
        "before-agent": "BeforeAgent",
        "after-agent": "AfterAgent",
        "session-end": "SessionEnd",
    }

    def __init__(self):
        """Initialize the Gemini CLI dispatcher."""
        super().__init__(provider="gemini-cli")

    def get_settings_path(self, project_root: Path) -> Optional[Path]:
        """Get the path to Gemini CLI's settings file."""
        return project_root / self.GEMINI_SETTINGS_PATH

    def translate_event(self, monoco_event: str) -> str:
        """Translate Monoco event to Gemini CLI event name."""
        return self.EVENT_MAP.get(monoco_event, monoco_event)

    def generate_hook_config(self, hook: ParsedHook) -> dict[str, Any]:
        """
        Generate Gemini CLI hook configuration.

        Gemini uses a similar matcher-based configuration:
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": "monoco hook run agent before-tool"
                }
            ]
        }
        """
        agent_event = self.translate_event(hook.metadata.event)

        # Build the command that invokes the Universal Interceptor
        command = f"monoco hook run agent {hook.metadata.event}"

        config: dict[str, Any] = {
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                }
            ]
        }

        # Add matcher if specified in metadata
        if hook.metadata.matcher:
            config["matcher"] = hook.metadata.matcher[0] if hook.metadata.matcher else "*"

        return config


def create_agent_dispatchers() -> list[AgentHookDispatcher]:
    """
    Factory function to create all available agent dispatchers.

    Returns:
        List of configured agent dispatchers
    """
    return [
        ClaudeCodeDispatcher(),
        GeminiDispatcher(),
    ]


def get_dispatcher_for_provider(provider: str) -> Optional[AgentHookDispatcher]:
    """
    Get the appropriate dispatcher for a provider.

    Args:
        provider: The provider name (e.g., 'claude-code', 'gemini-cli')

    Returns:
        The dispatcher instance or None if not found
    """
    dispatchers = {
        "claude-code": ClaudeCodeDispatcher,
        "gemini-cli": GeminiDispatcher,
    }

    dispatcher_class = dispatchers.get(provider)
    if dispatcher_class:
        return dispatcher_class()
    return None
