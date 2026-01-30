"""Tests for hook base classes."""

import pytest
from monoco.core.hooks.base import (
    SessionLifecycleHook,
    HookResult,
    HookStatus,
)
from monoco.core.hooks.context import HookContext


class TestHookResult:
    """Tests for HookResult dataclass."""

    def test_success_factory(self):
        result = HookResult.success("Test message", {"key": "value"})
        assert result.status == HookStatus.SUCCESS
        assert result.message == "Test message"
        assert result.details == {"key": "value"}

    def test_failure_factory(self):
        result = HookResult.failure("Error occurred")
        assert result.status == HookStatus.FAILURE
        assert result.message == "Error occurred"
        assert result.details is None

    def test_skipped_factory(self):
        result = HookResult.skipped("Not applicable")
        assert result.status == HookStatus.SKIPPED
        assert result.message == "Not applicable"

    def test_warning_factory(self):
        result = HookResult.warning("Warning message")
        assert result.status == HookStatus.WARNING
        assert result.message == "Warning message"


class TestSessionLifecycleHook:
    """Tests for SessionLifecycleHook abstract base class."""

    def test_hook_initialization_with_defaults(self):
        """Test hook initialization with default parameters."""
        
        class TestHook(SessionLifecycleHook):
            def on_session_start(self, context: HookContext) -> HookResult:
                return HookResult.success()

            def on_session_end(self, context: HookContext) -> HookResult:
                return HookResult.success()

        hook = TestHook()
        assert hook.name == "TestHook"
        assert hook.config == {}
        assert hook.enabled is True
        assert hook.is_enabled() is True

    def test_hook_initialization_with_custom_name(self):
        """Test hook initialization with custom name."""
        
        class TestHook(SessionLifecycleHook):
            def on_session_start(self, context: HookContext) -> HookResult:
                return HookResult.success()

            def on_session_end(self, context: HookContext) -> HookResult:
                return HookResult.success()

        hook = TestHook(name="custom_name", config={"enabled": False})
        assert hook.name == "custom_name"
        assert hook.enabled is False
        assert hook.is_enabled() is False

    def test_hook_execution(self):
        """Test hook method execution."""
        
        class TestHook(SessionLifecycleHook):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.start_called = False
                self.end_called = False

            def on_session_start(self, context: HookContext) -> HookResult:
                self.start_called = True
                return HookResult.success("Started")

            def on_session_end(self, context: HookContext) -> HookResult:
                self.end_called = True
                return HookResult.success("Ended")

        hook = TestHook()
        # Create a minimal context
        context = HookContext(
            session_id="test-123",
            role_name="tester",
            session_status="running",
            created_at=None,
        )

        start_result = hook.on_session_start(context)
        end_result = hook.on_session_end(context)

        assert hook.start_called is True
        assert hook.end_called is True
        assert start_result.status == HookStatus.SUCCESS
        assert end_result.status == HookStatus.SUCCESS
