"""
Agent Engine Adapters for Monoco Scheduler.

This module provides a unified interface for different AI agent execution engines,
allowing the Worker to seamlessly switch between Gemini, Claude, and future engines.
"""

from abc import ABC, abstractmethod
from typing import List


class EngineAdapter(ABC):
    """
    Abstract base class for agent engine adapters.

    Each adapter is responsible for:
    1. Constructing the correct CLI command for its engine
    2. Handling engine-specific error scenarios
    3. Providing metadata about the engine's capabilities
    """

    @abstractmethod
    def build_command(self, prompt: str) -> List[str]:
        """
        Build the CLI command to execute the agent with the given prompt.

        Args:
            prompt: The instruction/context to send to the agent

        Returns:
            List of command arguments (e.g., ["gemini", "-y", "prompt text"])
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the canonical name of this engine."""
        pass

    @property
    def supports_yolo_mode(self) -> bool:
        """Whether this engine supports auto-approval mode."""
        return False


class GeminiAdapter(EngineAdapter):
    """
    Adapter for Google Gemini CLI.

    Command format: gemini -p <prompt> -y
    The -y flag enables "YOLO mode" (auto-approval of actions).
    """

    def build_command(self, prompt: str) -> List[str]:
        # Based on Gemini CLI help: -p <prompt> for non-interactive
        return ["gemini", "-p", prompt, "-y"]

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def supports_yolo_mode(self) -> bool:
        return True


class ClaudeAdapter(EngineAdapter):
    """
    Adapter for Anthropic Claude CLI.

    Command format: claude -p <prompt>
    The -p/--print flag enables non-interactive mode.
    """

    def build_command(self, prompt: str) -> List[str]:
        # Based on Claude CLI help: -p <prompt> is NOT standard, usually -p means print/non-interactive.
        # But for one-shot execution, we do passing prompt as argument with -p flag.
        return ["claude", "-p", prompt]

    @property
    def name(self) -> str:
        return "claude"

    @property
    def supports_yolo_mode(self) -> bool:
        # Claude uses -p for non-interactive mode, similar concept
        return True


class QwenAdapter(EngineAdapter):
    """
    Adapter for Qwen Code CLI.

    Command format: qwen -p <prompt> -y
    """

    def build_command(self, prompt: str) -> List[str]:
        # Assuming Qwen follows similar patterns (based on user feedback)
        return ["qwen", "-p", prompt, "-y"]

    @property
    def name(self) -> str:
        return "qwen"

    @property
    def supports_yolo_mode(self) -> bool:
        return True


class KimiAdapter(EngineAdapter):
    """
    Adapter for Kimi CLI (Moonshot AI).

    Command format: kimi -p <prompt> --print
    Note: --print implicitly adds --yolo.
    """

    def build_command(self, prompt: str) -> List[str]:
        # Based on Kimi CLI help: -p, --prompt TEXT.
        # Also using --print for non-interactive mode (which enables yolo).
        return ["kimi", "-p", prompt, "--print"]

    @property
    def name(self) -> str:
        return "kimi"

    @property
    def supports_yolo_mode(self) -> bool:
        return True


class EngineFactory:
    """
    Factory for creating engine adapter instances.

    Usage:
        adapter = EngineFactory.create("gemini")
        command = adapter.build_command("Write a test")
    """

    _adapters = {
        "gemini": GeminiAdapter,
        "claude": ClaudeAdapter,
        "qwen": QwenAdapter,
        "kimi": KimiAdapter,
    }

    @classmethod
    def create(cls, engine_name: str) -> EngineAdapter:
        """
        Create an adapter instance for the specified engine.

        Args:
            engine_name: Name of the engine (e.g., "gemini", "claude")

        Returns:
            An instance of the appropriate EngineAdapter

        Raises:
            ValueError: If the engine is not supported
        """
        adapter_class = cls._adapters.get(engine_name.lower())
        if not adapter_class:
            supported = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Unsupported engine: '{engine_name}'. "
                f"Supported engines: {supported}"
            )
        return adapter_class()

    @classmethod
    def supported_engines(cls) -> List[str]:
        """Return a list of all supported engine names."""
        return list(cls._adapters.keys())
