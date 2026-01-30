"""Tests for hook registry."""

import pytest
from datetime import datetime
from pathlib import Path

from monoco.core.hooks.registry import HookRegistry, get_registry, reset_registry
from monoco.core.hooks.base import SessionLifecycleHook, HookResult, HookStatus
from monoco.core.hooks.context import HookContext


class MockHook(SessionLifecycleHook):
    """Mock hook for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_called = False
        self.end_called = False

    def on_session_start(self, context: HookContext) -> HookResult:
        self.start_called = True
        return HookResult.success(f"{self.name} started")

    def on_session_end(self, context: HookContext) -> HookResult:
        self.end_called = True
        return HookResult.success(f"{self.name} ended")


class FailingHook(SessionLifecycleHook):
    """Hook that fails for testing error handling."""
    
    def __init__(self, fail_start=False, fail_end=False, **kwargs):
        super().__init__(**kwargs)
        self.fail_start = fail_start
        self.fail_end = fail_end

    def on_session_start(self, context: HookContext) -> HookResult:
        if self.fail_start:
            return HookResult.failure("Start failed")
        return HookResult.success()

    def on_session_end(self, context: HookContext) -> HookResult:
        if self.fail_end:
            raise RuntimeError("End crashed")
        return HookResult.success()


class TestHookRegistry:
    """Tests for HookRegistry."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_registry()

    def test_register_hook_instance(self):
        registry = HookRegistry()
        hook = MockHook(name="test_hook")
        
        registry.register(hook)
        
        hooks = registry.get_hooks()
        assert len(hooks) == 1
        assert hooks[0].name == "test_hook"

    def test_register_hook_class(self):
        registry = HookRegistry()
        
        registry.register_class(MockHook, name="class_hook", config={"enabled": True})
        
        hooks = registry.get_hooks()
        assert len(hooks) == 1
        assert hooks[0].name == "class_hook"
        assert isinstance(hooks[0], MockHook)

    def test_unregister_hook(self):
        registry = HookRegistry()
        hook = MockHook(name="removable")
        
        registry.register(hook)
        assert len(registry.get_hooks()) == 1
        
        result = registry.unregister("removable")
        assert result is True
        assert len(registry.get_hooks()) == 0
        
        # Unregister non-existent hook
        result = registry.unregister("nonexistent")
        assert result is False

    def test_get_hooks_filtered_by_enabled(self):
        registry = HookRegistry()
        
        enabled_hook = MockHook(name="enabled", config={"enabled": True})
        disabled_hook = MockHook(name="disabled", config={"enabled": False})
        
        registry.register(enabled_hook)
        registry.register(disabled_hook)
        
        all_hooks = registry.get_hooks(enabled_only=False)
        enabled_hooks = registry.get_hooks(enabled_only=True)
        
        assert len(all_hooks) == 2
        assert len(enabled_hooks) == 1
        assert enabled_hooks[0].name == "enabled"

    def test_clear_registry(self):
        registry = HookRegistry()
        registry.register(MockHook(name="hook1"))
        registry.register(MockHook(name="hook2"))
        
        assert len(registry.get_hooks()) == 2
        
        registry.clear()
        
        assert len(registry.get_hooks()) == 0

    def test_execute_on_session_start(self):
        registry = HookRegistry()
        hook1 = MockHook(name="hook1")
        hook2 = MockHook(name="hook2")
        
        registry.register(hook1)
        registry.register(hook2)
        
        context = HookContext(
            session_id="test",
            role_name="tester",
            session_status="running",
            created_at=datetime.now(),
        )
        
        results = registry.execute_on_session_start(context)
        
        assert len(results) == 2
        assert all(r.status == HookStatus.SUCCESS for r in results)
        assert hook1.start_called is True
        assert hook2.start_called is True

    def test_execute_on_session_end(self):
        registry = HookRegistry()
        hook = MockHook(name="hook")
        
        registry.register(hook)
        
        context = HookContext(
            session_id="test",
            role_name="tester",
            session_status="running",
            created_at=datetime.now(),
        )
        
        results = registry.execute_on_session_end(context)
        
        assert len(results) == 1
        assert results[0].status == HookStatus.SUCCESS
        assert hook.end_called is True

    def test_hook_execution_continues_after_failure(self):
        """Test that one hook's failure doesn't stop others."""
        registry = HookRegistry()
        
        failing_hook = FailingHook(name="failing", fail_start=True)
        success_hook = MockHook(name="success")
        
        registry.register(failing_hook)
        registry.register(success_hook)
        
        context = HookContext(
            session_id="test",
            role_name="tester",
            session_status="running",
            created_at=datetime.now(),
        )
        
        results = registry.execute_on_session_start(context)
        
        assert len(results) == 2
        assert results[0].status == HookStatus.FAILURE
        assert results[1].status == HookStatus.SUCCESS
        assert success_hook.start_called is True  # Still called despite previous failure

    def test_hook_execution_handles_exceptions(self):
        """Test that hook exceptions are caught and converted to failure results."""
        registry = HookRegistry()
        
        crashing_hook = FailingHook(name="crashing", fail_end=True)
        
        registry.register(crashing_hook)
        
        context = HookContext(
            session_id="test",
            role_name="tester",
            session_status="running",
            created_at=datetime.now(),
        )
        
        # Should not raise exception
        results = registry.execute_on_session_end(context)
        
        assert len(results) == 1
        assert results[0].status == HookStatus.FAILURE
        assert "End crashed" in results[0].message

    def test_invalid_hook_registration(self):
        """Test that invalid hooks are rejected."""
        registry = HookRegistry()
        
        with pytest.raises(TypeError):
            registry.register("not a hook")
        
        with pytest.raises(TypeError):
            registry.register_class(str)


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def setup_method(self):
        reset_registry()

    def test_get_registry_singleton(self):
        """Test that get_registry returns the same instance."""
        reg1 = get_registry()
        reg2 = get_registry()
        
        assert reg1 is reg2

    def test_reset_registry(self):
        """Test that reset_registry creates a new instance."""
        reg1 = get_registry()
        reg1.register(MockHook(name="test"))
        
        reset_registry()
        
        reg2 = get_registry()
        assert reg1 is not reg2
        assert len(reg2.get_hooks()) == 0
