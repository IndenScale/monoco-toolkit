"""Tests for Universal Hooks manager."""

import pytest
from pathlib import Path
import tempfile
import os

from monoco.features.hooks.manager import (
    UniversalHookManager,
    ValidationResult,
    HookDispatcher,
)
from monoco.features.hooks.models import (
    HookType,
    HookMetadata,
    ParsedHook,
    GitEvent,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result(self):
        """Should create valid result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_add_error(self):
        """Should add error and set is_valid to False."""
        result = ValidationResult(is_valid=True)
        result.add_error("Something went wrong")

        assert result.is_valid is False
        assert "Something went wrong" in result.errors

    def test_add_warning(self):
        """Should add warning without changing is_valid."""
        result = ValidationResult(is_valid=True)
        result.add_warning("This is a warning")

        assert result.is_valid is True
        assert "This is a warning" in result.warnings


class TestHookDispatcher:
    """Tests for HookDispatcher abstract class."""

    def test_dispatcher_key_for_git(self):
        """Should create correct key for git dispatcher."""
        class TestDispatcher(HookDispatcher):
            def can_execute(self, hook):
                return True
            def execute(self, hook, context=None):
                return True

        dispatcher = TestDispatcher(HookType.GIT)
        assert dispatcher.key == "git"

    def test_dispatcher_key_for_agent(self):
        """Should create correct key for agent dispatcher."""
        class TestDispatcher(HookDispatcher):
            def can_execute(self, hook):
                return True
            def execute(self, hook, context=None):
                return True

        dispatcher = TestDispatcher(HookType.AGENT, "claude-code")
        assert dispatcher.key == "agent:claude-code"


class TestUniversalHookManagerScan:
    """Tests for UniversalHookManager.scan method."""

    def test_scan_empty_directory(self):
        """Should return empty dict for empty directory."""
        manager = UniversalHookManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            groups = manager.scan(tmpdir)

        assert groups == {}

    def test_scan_single_hook(self):
        """Should scan single hook file."""
        manager = UniversalHookManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            hook_file = Path(tmpdir) / "test.sh"
            hook_file.write_text('''#!/bin/bash
# ---
# type: git
# event: pre-commit
# ---
''')
            groups = manager.scan(tmpdir)

        assert "git" in groups
        assert len(groups["git"].hooks) == 1
        assert groups["git"].hook_type == HookType.GIT

    def test_scan_groups_by_type(self):
        """Should group hooks by type."""
        manager = UniversalHookManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "git.sh").write_text('''#!/bin/bash
# ---
# type: git
# event: pre-commit
# ---
''')
            (Path(tmpdir) / "agent.sh").write_text('''#!/bin/bash
# ---
# type: agent
# provider: test
# event: before-tool
# ---
''')

            groups = manager.scan(tmpdir)

        assert "git" in groups
        assert "agent:test" in groups
        assert groups["git"].hook_type == HookType.GIT
        assert groups["agent:test"].hook_type == HookType.AGENT

    def test_scan_sorts_by_priority(self):
        """Should sort hooks by priority within groups."""
        manager = UniversalHookManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "high.sh").write_text('''#!/bin/bash
# ---
# type: git
# event: pre-commit
# priority: 100
# ---
''')
            (Path(tmpdir) / "low.sh").write_text('''#!/bin/bash
# ---
# type: git
# event: pre-commit
# priority: 10
# ---
''')
            (Path(tmpdir) / "med.sh").write_text('''#!/bin/bash
# ---
# type: git
# event: pre-commit
# priority: 50
# ---
''')

            groups = manager.scan(tmpdir)

        priorities = [h.metadata.priority for h in groups["git"].hooks]
        assert priorities == [10, 50, 100]


class TestUniversalHookManagerValidate:
    """Tests for UniversalHookManager.validate method."""

    def test_validate_valid_git_hook(self):
        """Should validate valid git hook."""
        manager = UniversalHookManager()
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
        )

        result = manager.validate(metadata)

        assert result.is_valid is True
        assert result.errors == []

    def test_validate_valid_agent_hook(self):
        """Should validate valid agent hook."""
        manager = UniversalHookManager()
        metadata = HookMetadata(
            type=HookType.AGENT,
            event="before-tool",
            provider="claude-code",
        )

        result = manager.validate(metadata)

        assert result.is_valid is True

    def test_validate_invalid_event(self):
        """Should catch validation errors during metadata construction."""
        # Pydantic validates event at construction time, so invalid events
        # raise ValidationError which is caught by the parser.
        # This test verifies that invalid events are properly rejected.
        with pytest.raises(Exception) as exc_info:
            HookMetadata(
                type=HookType.GIT,
                event="invalid-event",
            )
        assert "Invalid event" in str(exc_info.value)

    def test_validate_with_script_path(self):
        """Should validate script file when path provided."""
        manager = UniversalHookManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write('''#!/bin/bash
# ---
# type: git
# event: pre-commit
# ---
''')
            temp_path = Path(f.name)

        try:
            parsed = manager.parser.parse_file(temp_path)
            result = manager.validate(parsed)

            # Should pass basic validation
            assert result.is_valid is True
        finally:
            os.unlink(temp_path)

    def test_validate_with_nonexistent_script(self):
        """Should report error for nonexistent script."""
        manager = UniversalHookManager()
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
        )
        parsed = ParsedHook(
            metadata=metadata,
            script_path=Path("/nonexistent/script.sh"),
            content="",
        )

        result = manager.validate(parsed)

        assert result.is_valid is False
        assert any("does not exist" in e for e in result.errors)


class TestUniversalHookManagerDispatchers:
    """Tests for dispatcher registration."""

    def test_register_dispatcher(self):
        """Should register dispatcher."""
        manager = UniversalHookManager()

        class TestDispatcher(HookDispatcher):
            def can_execute(self, hook):
                return True
            def execute(self, hook, context=None):
                return True

        dispatcher = TestDispatcher(HookType.GIT)
        manager.register_dispatcher(HookType.GIT, dispatcher)

        assert manager.get_dispatcher(HookType.GIT) is dispatcher

    def test_register_agent_dispatcher(self):
        """Should register agent dispatcher with provider."""
        manager = UniversalHookManager()

        class TestDispatcher(HookDispatcher):
            def can_execute(self, hook):
                return True
            def execute(self, hook, context=None):
                return True

        dispatcher = TestDispatcher(HookType.AGENT, "claude-code")
        manager.register_dispatcher(HookType.AGENT, dispatcher)

        assert manager.get_dispatcher(HookType.AGENT, "claude-code") is dispatcher

    def test_unregister_dispatcher(self):
        """Should unregister dispatcher."""
        manager = UniversalHookManager()

        class TestDispatcher(HookDispatcher):
            def can_execute(self, hook):
                return True
            def execute(self, hook, context=None):
                return True

        dispatcher = TestDispatcher(HookType.GIT)
        manager.register_dispatcher(HookType.GIT, dispatcher)
        assert manager.get_dispatcher(HookType.GIT) is not None

        result = manager.unregister_dispatcher(HookType.GIT)
        assert result is True
        assert manager.get_dispatcher(HookType.GIT) is None

    def test_list_dispatchers(self):
        """Should list all registered dispatchers."""
        manager = UniversalHookManager()

        class TestDispatcher(HookDispatcher):
            def can_execute(self, hook):
                return True
            def execute(self, hook, context=None):
                return True

        manager.register_dispatcher(HookType.GIT, TestDispatcher(HookType.GIT))
        manager.register_dispatcher(HookType.AGENT, TestDispatcher(HookType.AGENT, "test"))

        dispatchers = manager.list_dispatchers()

        assert len(dispatchers) == 2
        assert "git" in dispatchers
        assert "agent:test" in dispatchers


class TestUniversalHookManagerCustomValidation:
    """Tests for custom validation hooks."""

    def test_add_validation_hook(self):
        """Should add custom validation function."""
        manager = UniversalHookManager()

        def custom_validator(metadata):
            if metadata.priority < 50:
                return "Priority must be at least 50"
            return None

        manager.add_validation_hook(custom_validator)

        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
            priority=10,
        )
        result = manager.validate(metadata)

        assert result.is_valid is False
        assert "Priority must be at least 50" in result.errors

    def test_multiple_validation_hooks(self):
        """Should run multiple validation hooks."""
        manager = UniversalHookManager()

        manager.add_validation_hook(lambda m: "Error 1" if m.priority == 10 else None)
        manager.add_validation_hook(lambda m: "Error 2" if m.event == "pre-commit" else None)

        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
            priority=10,
        )
        result = manager.validate(metadata)

        assert result.is_valid is False
        assert "Error 1" in result.errors
        assert "Error 2" in result.errors


class TestUniversalHookManagerErrorHandling:
    """Tests for error handling."""

    def test_get_parsing_errors(self):
        """Should return parsing errors from last scan."""
        manager = UniversalHookManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an invalid hook file
            (Path(tmpdir) / "invalid.sh").write_text('''#!/bin/bash
# ---
# type: invalid_type
# event: pre-commit
# ---
''')
            groups = manager.scan(tmpdir)

        errors = manager.get_parsing_errors()
        assert len(errors) > 0

    def test_clear_parsing_errors(self):
        """Should clear parsing errors."""
        manager = UniversalHookManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "invalid.sh").write_text('''#!/bin/bash
# ---
# type: invalid
# ---
''')
            manager.scan(tmpdir)

        assert len(manager.get_parsing_errors()) > 0

        manager.clear_parsing_errors()
        assert len(manager.get_parsing_errors()) == 0
