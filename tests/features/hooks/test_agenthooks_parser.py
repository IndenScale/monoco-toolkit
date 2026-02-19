"""Tests for Agenthooks parser."""

import pytest
from pathlib import Path
import tempfile
import os

from monoco.features.hooks.agenthooks_parser import (
    AgenthooksParser,
    AgenthooksConfig,
    AgenthooksMatcher,
    convert_agenthooks_to_parsed_hook,
)
from monoco.features.hooks.models import HookType, normalize_agent_event


class TestAgenthooksMatcher:
    """Tests for AgenthooksMatcher."""

    def test_empty_matcher_always_matches(self):
        """Empty matcher should always match."""
        matcher = AgenthooksMatcher()
        assert matcher.matches() is True
        assert matcher.matches("Shell", {"command": "ls"}) is True

    def test_tool_matcher(self):
        """Tool matcher should match tool names."""
        matcher = AgenthooksMatcher(tool="Shell")
        assert matcher.matches("Shell", {}) is True
        assert matcher.matches("WriteFile", {}) is False

    def test_tool_regex_matcher(self):
        """Tool matcher should support regex."""
        matcher = AgenthooksMatcher(tool="Shell|Bash")
        assert matcher.matches("Shell", {}) is True
        assert matcher.matches("Bash", {}) is True
        assert matcher.matches("WriteFile", {}) is False

    def test_pattern_matcher(self):
        """Pattern matcher should match in tool input."""
        matcher = AgenthooksMatcher(pattern="rm -rf")
        assert matcher.matches(None, {"command": "rm -rf /"}) is True
        assert matcher.matches(None, {"command": "ls -la"}) is False

    def test_combined_matcher(self):
        """Combined tool and pattern matcher."""
        matcher = AgenthooksMatcher(tool="Shell", pattern="rm -rf")
        assert matcher.matches("Shell", {"command": "rm -rf /"}) is True
        assert matcher.matches("Shell", {"command": "ls -la"}) is False
        assert matcher.matches("WriteFile", {"command": "rm -rf"}) is False


class TestAgenthooksConfig:
    """Tests for AgenthooksConfig."""

    def test_basic_config(self):
        """Should create basic config."""
        config = AgenthooksConfig(
            name="test-hook",
            description="Test hook",
            trigger="pre-tool-call",
        )
        assert config.name == "test-hook"
        assert config.description == "Test hook"
        assert config.trigger == "pre-tool-call"
        assert config.timeout == 30000
        assert config.async_mode is False
        assert config.priority == 100

    def test_config_with_matcher(self):
        """Should create config with matcher."""
        matcher = AgenthooksMatcher(tool="Shell", pattern="rm -rf")
        config = AgenthooksConfig(
            name="block-dangerous",
            description="Block dangerous commands",
            trigger="pre-tool-call",
            matcher=matcher,
        )
        assert config.matcher is not None
        assert config.matcher.tool == "Shell"
        assert config.matcher.pattern == "rm -rf"

    def test_to_hook_metadata(self):
        """Should convert to HookMetadata."""
        config = AgenthooksConfig(
            name="test-hook",
            description="Test hook",
            trigger="pre-tool-call",
            priority=999,
        )
        metadata = config.to_hook_metadata()
        assert metadata.type == HookType.AGENT
        assert metadata.event == "before-tool"  # normalized
        assert metadata.priority == 999
        assert metadata.provider == "agenthooks"
        assert metadata.extra["agenthooks_name"] == "test-hook"
        assert metadata.extra["agenthooks_timeout"] == 30000


class TestAgenthooksParser:
    """Tests for AgenthooksParser."""

    def test_parse_basic_hook_md(self):
        """Should parse basic HOOK.md."""
        content = '''---
name: test-hook
description: A test hook
trigger: pre-tool-call
---

# Test Hook

This is a test hook.
'''
        parser = AgenthooksParser()
        config = parser.parse_hook_md_content(Path("test/HOOK.md"), content)

        assert config is not None
        assert config.name == "test-hook"
        assert config.description == "A test hook"
        assert config.trigger == "pre-tool-call"

    def test_parse_hook_md_with_matcher(self):
        """Should parse HOOK.md with matcher."""
        content = '''---
name: block-dangerous
description: Block dangerous commands
trigger: pre-tool-call
matcher:
  tool: Shell
  pattern: "rm -rf /|mkfs"
timeout: 5000
async: false
priority: 999
---

# Block Dangerous Commands
'''
        parser = AgenthooksParser()
        config = parser.parse_hook_md_content(Path("test/HOOK.md"), content)

        assert config is not None
        assert config.name == "block-dangerous"
        assert config.matcher is not None
        assert config.matcher.tool == "Shell"
        assert config.matcher.pattern == "rm -rf /|mkfs"
        assert config.timeout == 5000
        assert config.async_mode is False
        assert config.priority == 999

    def test_parse_hook_md_missing_name(self):
        """Should fail if name is missing."""
        content = '''---
description: A test hook
trigger: pre-tool-call
---
'''
        parser = AgenthooksParser()
        config = parser.parse_hook_md_content(Path("test/HOOK.md"), content)

        assert config is None
        assert len(parser.get_errors()) > 0

    def test_parse_hook_md_missing_trigger(self):
        """Should fail if trigger is missing."""
        content = '''---
name: test-hook
description: A test hook
---
'''
        parser = AgenthooksParser()
        config = parser.parse_hook_md_content(Path("test/HOOK.md"), content)

        assert config is None
        assert len(parser.get_errors()) > 0

    def test_discover_hooks(self):
        """Should discover hooks in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create hook directories
            hook1_dir = tmpdir_path / "hook1"
            hook1_dir.mkdir()
            (hook1_dir / "HOOK.md").write_text('''---
name: hook1
description: First hook
trigger: pre-tool-call
priority: 10
---
''')

            hook2_dir = tmpdir_path / "hook2"
            hook2_dir.mkdir()
            (hook2_dir / "HOOK.md").write_text('''---
name: hook2
description: Second hook
trigger: post-tool-call
priority: 20
---
''')

            # Create scripts directory for hook1
            scripts_dir = hook1_dir / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "run.sh").write_text("#!/bin/bash\necho test")

            parser = AgenthooksParser()
            configs = parser.discover_hooks(tmpdir_path)

            assert len(configs) == 2
            # Should be sorted by priority (higher first)
            assert configs[0].name == "hook2"
            assert configs[1].name == "hook1"

    def test_discover_hooks_empty_directory(self):
        """Should return empty list for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = AgenthooksParser()
            configs = parser.discover_hooks(Path(tmpdir))
            assert configs == []

    def test_discover_hooks_nonexistent_directory(self):
        """Should return empty list for nonexistent directory."""
        parser = AgenthooksParser()
        configs = parser.discover_hooks(Path("/nonexistent/path"))
        assert configs == []


class TestConvertAgenthooksToParsedHook:
    """Tests for convert_agenthooks_to_parsed_hook."""

    def test_convert_valid_hook(self):
        """Should convert valid config to ParsedHook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hook_dir = Path(tmpdir)
            scripts_dir = hook_dir / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "run.sh").write_text("#!/bin/bash\necho test")

            config = AgenthooksConfig(
                name="test-hook",
                description="Test hook",
                trigger="pre-tool-call",
            )

            parsed = convert_agenthooks_to_parsed_hook(config, hook_dir)

            assert parsed is not None
            assert parsed.script_path == scripts_dir / "run.sh"
            assert parsed.metadata.type == HookType.AGENT
            assert "test" in parsed.content

    def test_convert_missing_script(self):
        """Should return None if script doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hook_dir = Path(tmpdir)

            config = AgenthooksConfig(
                name="test-hook",
                description="Test hook",
                trigger="pre-tool-call",
            )

            parsed = convert_agenthooks_to_parsed_hook(config, hook_dir)
            assert parsed is None


class TestNormalizeAgentEvent:
    """Tests for normalize_agent_event function."""

    def test_standard_agenthooks_events(self):
        """Should normalize standard agenthooks events."""
        assert normalize_agent_event("pre-session") == "session-start"
        assert normalize_agent_event("post-session") == "session-end"
        assert normalize_agent_event("pre-tool-call") == "before-tool"
        assert normalize_agent_event("post-tool-call") == "after-tool"
        assert normalize_agent_event("pre-agent-turn") == "before-agent"
        assert normalize_agent_event("post-agent-turn") == "after-agent"

    def test_legacy_events(self):
        """Should normalize legacy events."""
        assert normalize_agent_event("session_start") == "session-start"
        assert normalize_agent_event("before_tool") == "before-tool"
        assert normalize_agent_event("after_agent") == "after-agent"

    def test_already_normalized(self):
        """Should return already normalized events."""
        assert normalize_agent_event("session-start") == "session-start"
        assert normalize_agent_event("before-tool") == "before-tool"

    def test_unknown_events(self):
        """Should return unknown events as-is."""
        assert normalize_agent_event("custom-event") == "custom-event"
