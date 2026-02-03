"""
Unit tests for Agent Engine Adapters.

Tests the engine adapters from monoco.core.scheduler.
"""

import pytest
from monoco.core.scheduler import (
    GeminiAdapter,
    ClaudeAdapter,
    QwenAdapter,
    EngineFactory,
)


class TestGeminiAdapter:
    """Test suite for GeminiAdapter."""

    def test_build_command(self):
        adapter = GeminiAdapter()
        prompt = "Write a test for the User model"
        command = adapter.build_command(prompt)

        assert command == ["gemini", "-p", "Write a test for the User model", "-y"]

    def test_name(self):
        adapter = GeminiAdapter()
        assert adapter.name == "gemini"

    def test_supports_yolo_mode(self):
        adapter = GeminiAdapter()
        assert adapter.supports_yolo_mode is True


class TestClaudeAdapter:
    """Test suite for ClaudeAdapter."""

    def test_build_command(self):
        adapter = ClaudeAdapter()
        prompt = "Refactor the authentication module"
        command = adapter.build_command(prompt)

        assert command == ["claude", "-p", "Refactor the authentication module"]

    def test_name(self):
        adapter = ClaudeAdapter()
        assert adapter.name == "claude"

    def test_supports_yolo_mode(self):
        adapter = ClaudeAdapter()
        assert adapter.supports_yolo_mode is True


class TestQwenAdapter:
    """Test suite for QwenAdapter."""

    def test_build_command(self):
        adapter = QwenAdapter()
        prompt = "Implement user authentication"
        command = adapter.build_command(prompt)

        assert command == ["qwen", "-p", "Implement user authentication", "-y"]

    def test_name(self):
        adapter = QwenAdapter()
        assert adapter.name == "qwen"

    def test_supports_yolo_mode(self):
        adapter = QwenAdapter()
        assert adapter.supports_yolo_mode is True


class TestEngineFactory:
    """Test suite for EngineFactory."""

    def test_create_gemini_adapter(self):
        adapter = EngineFactory.create("gemini")
        assert isinstance(adapter, GeminiAdapter)
        assert adapter.name == "gemini"

    def test_create_claude_adapter(self):
        adapter = EngineFactory.create("claude")
        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.name == "claude"

    def test_create_qwen_adapter(self):
        adapter = EngineFactory.create("qwen")
        assert isinstance(adapter, QwenAdapter)
        assert adapter.name == "qwen"

    def test_create_case_insensitive(self):
        """Factory should handle case-insensitive engine names."""
        adapter_upper = EngineFactory.create("GEMINI")
        adapter_mixed = EngineFactory.create("GeMiNi")

        assert isinstance(adapter_upper, GeminiAdapter)
        assert isinstance(adapter_mixed, GeminiAdapter)

    def test_create_unsupported_engine(self):
        """Factory should raise ValueError for unsupported engines."""
        with pytest.raises(ValueError) as exc_info:
            EngineFactory.create("gpt4")

        assert "Unsupported engine: 'gpt4'" in str(exc_info.value)
        assert "gemini, claude" in str(exc_info.value)

    def test_supported_engines(self):
        """Factory should return list of supported engines."""
        engines = EngineFactory.supported_engines()

        assert "gemini" in engines
        assert "claude" in engines
        assert "qwen" in engines
        assert len(engines) >= 3


class TestEngineAdapterInterface:
    """Test that all adapters conform to the EngineAdapter interface."""

    @pytest.mark.parametrize(
        "adapter_class",
        [GeminiAdapter, ClaudeAdapter, QwenAdapter],
    )
    def test_adapter_implements_interface(self, adapter_class):
        """All adapters should implement the EngineAdapter interface."""
        adapter = adapter_class()

        # Check required methods exist
        assert hasattr(adapter, "build_command")
        assert hasattr(adapter, "name")
        assert hasattr(adapter, "supports_yolo_mode")

        # Check method signatures
        assert callable(adapter.build_command)
        assert isinstance(adapter.name, str)
        assert isinstance(adapter.supports_yolo_mode, bool)

    @pytest.mark.parametrize(
        "adapter_class",
        [GeminiAdapter, ClaudeAdapter, QwenAdapter],
    )
    def test_build_command_returns_list(self, adapter_class):
        """build_command should always return a list of strings."""
        adapter = adapter_class()
        command = adapter.build_command("test prompt")

        assert isinstance(command, list)
        assert all(isinstance(arg, str) for arg in command)
        assert len(command) >= 2  # At least [engine, prompt]
