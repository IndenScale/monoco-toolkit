"""
Universal Interceptor for Agent Hooks (ACL - Anti-Corruption Layer).

This module provides runtime protocol translation between different Agent platforms
(Claude Code, Gemini CLI) and the Monoco unified hook protocol.

Usage:
    python -m monoco.features.hooks.universal_interceptor <hook_script_path>

The interceptor:
1. Auto-detects the Agent platform from input format
2. Translates agent-specific input to Monoco unified format
3. Executes the actual hook script
4. Translates the output back to agent-specific format
"""

import json
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class AgentProvider(Enum):
    """Supported Agent providers."""
    CLAUDE_CODE = "claude-code"
    GEMINI_CLI = "gemini-cli"
    UNKNOWN = "unknown"


@dataclass
class UnifiedDecision:
    """
    Unified decision model for hook responses.

    This is the internal format used by Monoco, independent of any specific agent.
    """
    decision: str  # "allow", "deny", "ask"
    reason: str = ""
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision": self.decision,
            "reason": self.reason,
            "message": self.message,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UnifiedDecision":
        """Create from dictionary."""
        return cls(
            decision=data.get("decision", "ask"),
            reason=data.get("reason", ""),
            message=data.get("message", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class UnifiedHookInput:
    """
    Unified hook input model.

    This normalizes input from different agent platforms into a common format.
    """
    event: str  # Monoco event name (e.g., "before-tool", "before-agent")
    tool: Optional[str] = None  # Tool name (for tool-related events)
    input_data: dict[str, Any] = field(default_factory=dict)  # Tool/agent input
    env: dict[str, str] = field(default_factory=dict)  # Environment variables
    metadata: dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event": self.event,
            "tool": self.tool,
            "input": self.input_data,
            "env": self.env,
            "metadata": self.metadata,
        }


class AgentAdapter(ABC):
    """
    Abstract base class for Agent-specific adapters.

    Adapters handle the translation between agent-specific protocols
    and the Monoco unified protocol.
    """

    def __init__(self, provider: AgentProvider):
        self.provider = provider

    @abstractmethod
    def detect(self, raw_input: str) -> bool:
        """
        Detect if this adapter should be used based on input format.

        Args:
            raw_input: Raw JSON string from stdin

        Returns:
            True if this adapter should handle the input format
        """
        pass

    @abstractmethod
    def translate_input(self, raw_input: str) -> UnifiedHookInput:
        """
        Translate agent-specific input to unified format.

        Args:
            raw_input: Raw JSON string from stdin

        Returns:
            UnifiedHookInput
        """
        pass

    @abstractmethod
    def translate_output(self, decision: UnifiedDecision) -> str:
        """
        Translate unified decision to agent-specific output.

        Args:
            decision: Unified decision

        Returns:
            JSON string for agent-specific output
        """
        pass


class ClaudeAdapter(AgentAdapter):
    """
    Adapter for Claude Code agent.

    Event Mapping (Claude -> Monoco):
        - PreToolUse -> before-tool
        - PostToolUse -> after-tool
        - UserPromptSubmit -> before-agent
        - Stop -> after-agent
        - SessionStart -> session-start
        - SessionEnd -> session-end

    Decision Mapping:
        - Claude "permissionDecision" -> Monoco "decision"
        - Values: "allow", "deny", "ask"
    """

    # Event name mapping: Claude -> Monoco
    EVENT_MAP = {
        "PreToolUse": "before-tool",
        "PostToolUse": "after-tool",
        "UserPromptSubmit": "before-agent",
        "Stop": "after-agent",
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
    }

    # Reverse mapping: Monoco -> Claude
    REVERSE_EVENT_MAP = {v: k for k, v in EVENT_MAP.items()}

    def __init__(self):
        super().__init__(AgentProvider.CLAUDE_CODE)

    def detect(self, raw_input: str) -> bool:
        """Detect if input is in Claude Code format."""
        try:
            data = json.loads(raw_input)
            # Try both old and new field names
            event = data.get("hook_event_name") or data.get("event", "")
            # Claude Code uses specific event names
            return event in self.EVENT_MAP
        except json.JSONDecodeError:
            return False

    def translate_input(self, raw_input: str) -> UnifiedHookInput:
        """
        Translate Claude Code input to unified format.

        Claude Code input format:
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            ...
        }
        """
        try:
            data = json.loads(raw_input)
        except json.JSONDecodeError:
            data = {}

        # Use real Claude Code field names (hook_event_name, tool_name, tool_input)
        claude_event = data.get("hook_event_name") or data.get("event", "")
        monoco_event = self.EVENT_MAP.get(claude_event, claude_event.lower())

        return UnifiedHookInput(
            event=monoco_event,
            tool=data.get("tool_name") or data.get("tool"),
            input_data=data.get("tool_input") or data.get("input", {}),
            env=dict(os.environ),
            metadata={k: v for k, v in data.items() if k not in ("hook_event_name", "event", "tool_name", "tool", "tool_input", "input")},
        )

    def translate_output(self, decision: UnifiedDecision) -> str:
        """
        Translate unified decision to Claude Code output format.

        Claude Code output format:
        {
            "permissionDecision": "allow" | "deny" | "ask",
            "reason": "...",
            "message": "..."
        }
        """
        output = {
            "permissionDecision": decision.decision,
            "reason": decision.reason,
            "message": decision.message,
        }
        return json.dumps(output)


class GeminiAdapter(AgentAdapter):
    """
    Adapter for Gemini CLI agent.

    Event Mapping (Gemini -> Monoco):
        - BeforeTool -> before-tool
        - AfterTool -> after-tool
        - BeforeAgent -> before-agent
        - AfterAgent -> after-agent
        - SessionStart -> session-start
        - SessionEnd -> session-end

    Decision Mapping:
        - Gemini "decision" -> Monoco "decision"
        - Values: "allow", "deny", "ask"
    """

    # Event name mapping: Gemini -> Monoco
    EVENT_MAP = {
        "BeforeTool": "before-tool",
        "AfterTool": "after-tool",
        "BeforeAgent": "before-agent",
        "AfterAgent": "after-agent",
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
    }

    # Reverse mapping: Monoco -> Gemini
    REVERSE_EVENT_MAP = {v: k for k, v in EVENT_MAP.items()}

    def __init__(self):
        super().__init__(AgentProvider.GEMINI_CLI)

    def detect(self, raw_input: str) -> bool:
        """Detect if input is in Gemini CLI format."""
        try:
            data = json.loads(raw_input)
            event = data.get("event", "")
            # Gemini CLI uses specific event names
            return event in self.EVENT_MAP
        except json.JSONDecodeError:
            return False

    def translate_input(self, raw_input: str) -> UnifiedHookInput:
        """
        Translate Gemini CLI input to unified format.

        Gemini CLI input format:
        {
            "event": "BeforeTool",
            "tool": "Bash",
            "input": {"command": "ls -la"},
            ...
        }
        """
        try:
            data = json.loads(raw_input)
        except json.JSONDecodeError:
            data = {}

        gemini_event = data.get("event", "")
        monoco_event = self.EVENT_MAP.get(gemini_event, gemini_event.lower())

        return UnifiedHookInput(
            event=monoco_event,
            tool=data.get("tool"),
            input_data=data.get("input", {}),
            env=dict(os.environ),
            metadata={k: v for k, v in data.items() if k not in ("event", "tool", "input")},
        )

    def translate_output(self, decision: UnifiedDecision) -> str:
        """
        Translate unified decision to Gemini CLI output format.

        Gemini CLI output format:
        {
            "decision": "allow" | "deny" | "ask",
            "reason": "...",
            "message": "..."
        }
        """
        output = {
            "decision": decision.decision,
            "reason": decision.reason,
            "message": decision.message,
        }
        return json.dumps(output)


class UniversalInterceptor:
    """
    Universal interceptor for agent hooks.

    This is the main entry point for the ACL runtime. It:
    1. Auto-detects the agent platform
    2. Translates input from agent-specific to unified format
    3. Executes the hook script with unified input
    4. Translates output back to agent-specific format
    """

    def __init__(self):
        self.adapters: list[AgentAdapter] = [
            ClaudeAdapter(),
            GeminiAdapter(),
        ]
        self.adapter: Optional[AgentAdapter] = None

    def detect_adapter(self, raw_input: str) -> AgentAdapter:
        """
        Auto-detect the appropriate adapter based on input format.

        Args:
            raw_input: Raw JSON string from stdin

        Returns:
            The detected adapter

        Raises:
            RuntimeError: If no adapter can be detected
        """
        for adapter in self.adapters:
            if adapter.detect(raw_input):
                return adapter

        raise RuntimeError(
            "Could not detect agent input format. "
            "Expected Claude Code or Gemini CLI event format."
        )

    def run(self, hook_script_path: str, is_debug: bool = False, stdin_data: Optional[str] = None) -> int:
        """
        Run the interceptor.

        Args:
            hook_script_path: Path to the actual hook script to execute
            is_debug: Whether debug mode is enabled for this hook
            stdin_data: Optional stdin data (if already read by caller)

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        # 1. Read raw input from stdin (or use provided data)
        raw_input = stdin_data if stdin_data is not None else sys.stdin.read()

        # 2. Detect adapter based on input format
        try:
            adapter = self.detect_adapter(raw_input)
        except RuntimeError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 1

        # 3. Translate input to unified format
        unified_input = adapter.translate_input(raw_input)

        # 4. Execute the hook script
        try:
            unified_output = self._execute_hook(
                hook_script_path, unified_input, adapter.provider.value, is_debug
            )
        except subprocess.CalledProcessError as e:
            # Script failed - return deny decision
            unified_output = UnifiedDecision(
                decision="deny",
                reason=f"Hook script failed: {e}",
                message="The hook script encountered an error.",
            )
        except Exception as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 1

        # 5. Translate output to agent-specific format
        agent_output = adapter.translate_output(unified_output)

        # 6. Print output for the agent
        print(agent_output)
        return 0

    def _execute_hook(
        self, script_path: str, unified_input: UnifiedHookInput, provider: str, is_debug: bool = False
    ) -> UnifiedDecision:
        """
        Execute the hook script with unified input.

        Args:
            script_path: Path to the hook script
            unified_input: Unified input data
            provider: The detected provider name

        Returns:
            Unified decision from the script
        """
        script_path = Path(script_path)
        if not script_path.exists():
            # If script doesn't exist, allow by default
            return UnifiedDecision(decision="allow")

        # Prepare environment
        env = os.environ.copy()
        env["MONOCO_HOOK_EVENT"] = unified_input.event
        env["MONOCO_HOOK_PROVIDER"] = provider
        env["MONOCO_HOOK_TYPE"] = "agent"

        # Add tool info if available
        if unified_input.tool:
            env["MONOCO_HOOK_TOOL"] = unified_input.tool

        # Propagate debug flag if set
        if os.environ.get("MONOCO_HOOK_DEBUG") or is_debug:
            env["MONOCO_HOOK_DEBUG"] = "1"
            env["MONOCO_HOOK_IS_DEBUG"] = "true"

        # Execute the script
        input_json = json.dumps(unified_input.to_dict())

        result = subprocess.run(
            [str(script_path)],
            input=input_json,
            capture_output=True,
            text=True,
            env=env,
            timeout=300,  # 5 minute timeout
        )

        # Parse output
        if result.returncode == 0 and result.stdout.strip():
            try:
                output_data = json.loads(result.stdout.strip())
                return UnifiedDecision.from_dict(output_data)
            except json.JSONDecodeError:
                # Non-JSON output - treat as allow with message
                return UnifiedDecision(
                    decision="allow",
                    message=result.stdout.strip(),
                )
        elif result.returncode != 0:
            # Script failed - deny
            return UnifiedDecision(
                decision="deny",
                reason=f"Hook script exited with code {result.returncode}",
                message=result.stderr.strip() or "Hook script failed",
            )
        else:
            # No output - allow by default
            return UnifiedDecision(decision="allow")


def main() -> int:
    """
    Main entry point for the universal interceptor.

    Usage:
        python -m monoco.features.hooks.universal_interceptor <hook_script_path>
    """
    if len(sys.argv) < 2:
        print("Usage: universal_interceptor <hook_script_path>", file=sys.stderr)
        return 1

    hook_script_path = sys.argv[1]
    interceptor = UniversalInterceptor()
    return interceptor.run(hook_script_path)


if __name__ == "__main__":
    sys.exit(main())
