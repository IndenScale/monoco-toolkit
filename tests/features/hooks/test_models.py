"""Tests for Universal Hooks models."""

import pytest
from pathlib import Path

from monoco.features.hooks.universal_models import (
    HookType,
    GitEvent,
    AgentEvent,
    IDEEvent,
    HookMetadata,
    ParsedHook,
    HookGroup,
)


class TestHookType:
    """Tests for HookType enum."""

    def test_hook_type_values(self):
        """HookType enum should have expected values."""
        assert HookType.GIT.value == "git"
        assert HookType.IDE.value == "ide"
        assert HookType.AGENT.value == "agent"

    def test_hook_type_from_string(self):
        """Should be able to create HookType from string."""
        assert HookType("git") == HookType.GIT
        assert HookType("ide") == HookType.IDE
        assert HookType("agent") == HookType.AGENT


class TestGitEvent:
    """Tests for GitEvent enum."""

    def test_git_event_values(self):
        """GitEvent enum should have expected values."""
        assert GitEvent.PRE_COMMIT.value == "pre-commit"
        assert GitEvent.PREPARE_COMMIT_MSG.value == "prepare-commit-msg"
        assert GitEvent.COMMIT_MSG.value == "commit-msg"
        assert GitEvent.POST_MERGE.value == "post-merge"
        assert GitEvent.PRE_PUSH.value == "pre-push"
        assert GitEvent.POST_CHECKOUT.value == "post-checkout"
        assert GitEvent.PRE_REBASE.value == "pre-rebase"


class TestAgentEvent:
    """Tests for AgentEvent enum."""

    def test_agent_event_values(self):
        """AgentEvent enum should have expected values."""
        assert AgentEvent.SESSION_START.value == "session-start"
        assert AgentEvent.BEFORE_TOOL.value == "before-tool"
        assert AgentEvent.AFTER_TOOL.value == "after-tool"
        assert AgentEvent.BEFORE_AGENT.value == "before-agent"
        assert AgentEvent.AFTER_AGENT.value == "after-agent"
        assert AgentEvent.SESSION_END.value == "session-end"


class TestIDEEvent:
    """Tests for IDEEvent enum."""

    def test_ide_event_values(self):
        """IDEEvent enum should have expected values."""
        assert IDEEvent.ON_SAVE.value == "on-save"
        assert IDEEvent.ON_OPEN.value == "on-open"
        assert IDEEvent.ON_CLOSE.value == "on-close"
        assert IDEEvent.ON_BUILD.value == "on-build"


class TestHookMetadata:
    """Tests for HookMetadata model."""

    def test_valid_git_hook(self):
        """Should create valid git hook metadata."""
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
            priority=10,
            description="Test git hook",
        )
        assert metadata.type == HookType.GIT
        assert metadata.event == "pre-commit"
        assert metadata.priority == 10
        assert metadata.description == "Test git hook"
        assert metadata.provider is None

    def test_valid_agent_hook(self):
        """Should create valid agent hook metadata with provider."""
        metadata = HookMetadata(
            type=HookType.AGENT,
            event="before-tool",
            provider="claude-code",
            priority=5,
            description="Test agent hook",
        )
        assert metadata.type == HookType.AGENT
        assert metadata.provider == "claude-code"

    def test_valid_ide_hook(self):
        """Should create valid ide hook metadata with provider."""
        metadata = HookMetadata(
            type=HookType.IDE,
            event="on-save",
            provider="vscode",
            priority=20,
            description="Test IDE hook",
        )
        assert metadata.type == HookType.IDE
        assert metadata.provider == "vscode"

    def test_agent_hook_requires_provider(self):
        """Agent hook should require provider field."""
        with pytest.raises(ValueError, match="provider.*required"):
            HookMetadata(
                type=HookType.AGENT,
                event="before-tool",
            )

    def test_ide_hook_requires_provider(self):
        """IDE hook should require provider field."""
        with pytest.raises(ValueError, match="provider.*required"):
            HookMetadata(
                type=HookType.IDE,
                event="on-save",
            )

    def test_git_hook_does_not_require_provider(self):
        """Git hook should not require provider field."""
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
        )
        assert metadata.provider is None

    def test_invalid_event_for_git(self):
        """Should reject invalid event for git type."""
        with pytest.raises(ValueError, match="Invalid event"):
            HookMetadata(
                type=HookType.GIT,
                event="invalid-event",
            )

    def test_invalid_event_for_agent(self):
        """Should reject invalid event for agent type."""
        with pytest.raises(ValueError, match="Invalid event"):
            HookMetadata(
                type=HookType.AGENT,
                event="pre-commit",  # git event
                provider="claude-code",
            )

    def test_invalid_event_for_ide(self):
        """Should reject invalid event for ide type."""
        with pytest.raises(ValueError, match="Invalid event"):
            HookMetadata(
                type=HookType.IDE,
                event="before-tool",  # agent event
                provider="vscode",
            )

    def test_matcher_as_string(self):
        """Should convert string matcher to list."""
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
            matcher="*.py",
        )
        assert metadata.matcher == ["*.py"]

    def test_matcher_as_list(self):
        """Should accept list of matchers."""
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
            matcher=["*.py", "*.js"],
        )
        assert metadata.matcher == ["*.py", "*.js"]

    def test_default_priority(self):
        """Should use default priority of 100."""
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
        )
        assert metadata.priority == 100

    def test_priority_range(self):
        """Priority should be within valid range."""
        with pytest.raises(ValueError, match="priority"):
            HookMetadata(
                type=HookType.GIT,
                event="pre-commit",
                priority=-1,
            )

        with pytest.raises(ValueError, match="priority"):
            HookMetadata(
                type=HookType.GIT,
                event="pre-commit",
                priority=1001,
            )

    def test_get_key_for_git(self):
        """get_key should return 'git' for git hooks."""
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
        )
        assert metadata.get_key() == "git"

    def test_get_key_for_agent(self):
        """get_key should return 'agent:{provider}' for agent hooks."""
        metadata = HookMetadata(
            type=HookType.AGENT,
            event="before-tool",
            provider="claude-code",
        )
        assert metadata.get_key() == "agent:claude-code"

    def test_get_key_for_ide(self):
        """get_key should return 'ide:{provider}' for ide hooks."""
        metadata = HookMetadata(
            type=HookType.IDE,
            event="on-save",
            provider="vscode",
        )
        assert metadata.get_key() == "ide:vscode"

    def test_extra_metadata(self):
        """Should allow extra metadata fields."""
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
            extra={"custom_field": "value", "another": 123},
        )
        assert metadata.extra["custom_field"] == "value"
        assert metadata.extra["another"] == 123

    def test_immutability(self):
        """HookMetadata should be immutable."""
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
        )
        with pytest.raises(Exception):  # frozen model raises various exceptions
            metadata.priority = 50


class TestParsedHook:
    """Tests for ParsedHook model."""

    def test_create_parsed_hook(self):
        """Should create ParsedHook from metadata and content."""
        metadata = HookMetadata(
            type=HookType.GIT,
            event="pre-commit",
        )
        parsed = ParsedHook(
            metadata=metadata,
            script_path=Path("/tmp/test.sh"),
            content="#!/bin/sh\necho hello",
            front_matter_start_line=1,
            front_matter_end_line=5,
        )
        assert parsed.metadata == metadata
        assert parsed.script_path == Path("/tmp/test.sh")
        assert parsed.content == "#!/bin/sh\necho hello"
        assert parsed.front_matter_start_line == 1
        assert parsed.front_matter_end_line == 5


class TestHookGroup:
    """Tests for HookGroup model."""

    def test_create_hook_group(self):
        """Should create HookGroup with key and type."""
        group = HookGroup(
            key="git",
            hook_type=HookType.GIT,
        )
        assert group.key == "git"
        assert group.hook_type == HookType.GIT
        assert group.provider is None
        assert group.hooks == []

    def test_create_hook_group_with_provider(self):
        """Should create HookGroup with provider."""
        group = HookGroup(
            key="agent:claude-code",
            hook_type=HookType.AGENT,
            provider="claude-code",
        )
        assert group.key == "agent:claude-code"
        assert group.provider == "claude-code"

    def test_add_hook_sorts_by_priority(self):
        """add_hook should sort hooks by priority."""
        group = HookGroup(key="git", hook_type=HookType.GIT)

        hook1 = ParsedHook(
            metadata=HookMetadata(type=HookType.GIT, event="pre-commit", priority=50),
            script_path=Path("/tmp/hook1.sh"),
            content="",
        )
        hook2 = ParsedHook(
            metadata=HookMetadata(type=HookType.GIT, event="pre-commit", priority=10),
            script_path=Path("/tmp/hook2.sh"),
            content="",
        )
        hook3 = ParsedHook(
            metadata=HookMetadata(type=HookType.GIT, event="pre-commit", priority=100),
            script_path=Path("/tmp/hook3.sh"),
            content="",
        )

        group.add_hook(hook1)
        group.add_hook(hook2)
        group.add_hook(hook3)

        priorities = [h.metadata.priority for h in group.hooks]
        assert priorities == [10, 50, 100]

    def test_get_prioritized_hooks(self):
        """get_prioritized_hooks should return sorted hooks."""
        group = HookGroup(key="git", hook_type=HookType.GIT)

        for priority in [30, 10, 20]:
            hook = ParsedHook(
                metadata=HookMetadata(type=HookType.GIT, event="pre-commit", priority=priority),
                script_path=Path(f"/tmp/hook{priority}.sh"),
                content="",
            )
            group.add_hook(hook)

        hooks = group.get_prioritized_hooks()
        priorities = [h.metadata.priority for h in hooks]
        assert priorities == [10, 20, 30]
