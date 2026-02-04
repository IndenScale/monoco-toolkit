"""Tests for Universal Hooks parser."""

import pytest
from pathlib import Path
import tempfile
import os

from monoco.features.hooks.parser import HookParser, ParseError
from monoco.features.hooks.models import HookType, HookMetadata


class TestHookParserCommentStyles:
    """Tests for parsing different comment styles."""

    def test_parse_shell_style_comments(self):
        """Should parse shell-style # comments."""
        parser = HookParser()
        content = '''#!/bin/bash
# ---
# type: git
# event: pre-commit
# priority: 10
# description: Test hook
# ---
echo "Hello World"
'''
        hook = parser.parse_content(Path("test.sh"), content)

        assert hook is not None
        assert hook.metadata.type == HookType.GIT
        assert hook.metadata.event == "pre-commit"
        assert hook.metadata.priority == 10
        assert hook.metadata.description == "Test hook"

    def test_parse_python_style_comments(self):
        """Should parse Python-style # comments."""
        parser = HookParser()
        content = '''#!/usr/bin/env python3
# ---
# type: git
# event: pre-commit
# priority: 20
# ---
print("Hello")
'''
        hook = parser.parse_content(Path("test.py"), content)

        assert hook is not None
        assert hook.metadata.type == HookType.GIT
        assert hook.metadata.event == "pre-commit"

    def test_parse_c_style_comments(self):
        """Should parse C-style // comments."""
        parser = HookParser()
        content = '''#!/usr/bin/env node
// ---
// type: git
// event: pre-commit
// priority: 15
// ---
console.log("Hello");
'''
        hook = parser.parse_content(Path("test.js"), content)

        assert hook is not None
        assert hook.metadata.type == HookType.GIT
        assert hook.metadata.priority == 15

    def test_parse_typescript_comments(self):
        """Should parse TypeScript // comments."""
        parser = HookParser()
        content = '''// ---
// type: agent
// provider: claude-code
// event: before-tool
// ---
console.log("tool running");
'''
        hook = parser.parse_content(Path("test.ts"), content)

        assert hook is not None
        assert hook.metadata.type == HookType.AGENT
        assert hook.metadata.provider == "claude-code"

    def test_parse_lua_style_comments(self):
        """Should parse Lua-style -- comments."""
        parser = HookParser()
        content = '''#!/usr/bin/env lua
-- ---
-- type: git
-- event: pre-push
-- priority: 25
-- ---
print("Hello from Lua")
'''
        hook = parser.parse_content(Path("test.lua"), content)

        assert hook is not None
        assert hook.metadata.type == HookType.GIT
        assert hook.metadata.event == "pre-push"

    def test_parse_sql_style_comments(self):
        """Should parse SQL-style -- comments."""
        parser = HookParser()
        content = '''-- ---
-- type: ide
-- provider: datagrip
-- event: on-save
-- ---
SELECT 1;
'''
        hook = parser.parse_content(Path("test.sql"), content)

        assert hook is not None
        assert hook.metadata.type == HookType.IDE
        assert hook.metadata.provider == "datagrip"

    def test_parse_html_style_comments(self):
        """Should parse HTML-style <!-- --> comments."""
        parser = HookParser()
        content = '''<!-- ---
<!-- type: ide
<!-- provider: vscode
<!-- event: on-save
<!-- ---
<html></html>
'''
        hook = parser.parse_content(Path("test.html"), content)

        assert hook is not None
        assert hook.metadata.type == HookType.IDE
        assert hook.metadata.provider == "vscode"


class TestHookParserMatcher:
    """Tests for parsing matcher field."""

    def test_parse_single_matcher(self):
        """Should parse single matcher as string."""
        parser = HookParser()
        content = '''# ---
# type: git
# event: pre-commit
# matcher: "*.py"
# ---
'''
        hook = parser.parse_content(Path("test.sh"), content)

        assert hook is not None
        assert hook.metadata.matcher == ["*.py"]

    def test_parse_multiple_matchers(self):
        """Should parse multiple matchers as list."""
        parser = HookParser()
        content = '''# ---
# type: git
# event: pre-commit
# matcher:
#   - "*.py"
#   - "*.js"
#   - "*.ts"
# ---
'''
        hook = parser.parse_content(Path("test.sh"), content)

        assert hook is not None
        assert hook.metadata.matcher == ["*.py", "*.js", "*.ts"]


class TestHookParserEdgeCases:
    """Tests for edge cases and error handling."""

    def test_no_front_matter_returns_none(self):
        """Should return None if no front matter found."""
        parser = HookParser()
        content = '''#!/bin/bash
echo "No front matter here"
'''
        hook = parser.parse_content(Path("test.sh"), content)

        assert hook is None

    def test_empty_file_returns_none(self):
        """Should return None for empty file."""
        parser = HookParser()
        hook = parser.parse_content(Path("test.sh"), "")

        assert hook is None
        assert len(parser.get_errors()) == 1

    def test_unclosed_front_matter(self):
        """Should return None for unclosed front matter."""
        parser = HookParser()
        content = '''# ---
# type: git
# event: pre-commit
'''
        hook = parser.parse_content(Path("test.sh"), content)

        assert hook is None

    def test_invalid_yaml(self):
        """Should record error for invalid YAML."""
        parser = HookParser()
        content = '''# ---
# type: git
# event: : invalid yaml here
# ---
'''
        hook = parser.parse_content(Path("test.sh"), content)

        assert hook is None
        errors = parser.get_errors()
        assert len(errors) == 1
        assert "YAML" in errors[0].message or "validation" in errors[0].message.lower()

    def test_missing_required_fields(self):
        """Should record error for missing required fields."""
        parser = HookParser()
        content = '''# ---
# type: git
# ---
'''
        hook = parser.parse_content(Path("test.sh"), content)

        assert hook is None
        errors = parser.get_errors()
        assert len(errors) == 1

    def test_line_numbers_in_errors(self):
        """Should include line numbers in error messages."""
        parser = HookParser()
        content = '''#!/bin/bash
# ---
# type: git
# event: : invalid
# ---
'''
        parser.parse_content(Path("test.sh"), content)

        errors = parser.get_errors()
        assert len(errors) >= 1
        # Line number should be recorded
        assert errors[0].line_number > 0

    def test_detect_from_shebang(self):
        """Should detect comment style from shebang."""
        parser = HookParser()
        content = '''#!/usr/bin/env python3
# ---
# type: git
# event: pre-commit
# ---
'''
        hook = parser.parse_content(Path("script_without_ext"), content)

        assert hook is not None
        assert hook.metadata.type == HookType.GIT

    def test_detect_from_node_shebang(self):
        """Should detect // style from node shebang."""
        parser = HookParser()
        content = '''#!/usr/bin/env node
// ---
// type: git
// event: pre-commit
// ---
'''
        hook = parser.parse_content(Path("script_without_ext"), content)

        assert hook is not None
        assert hook.metadata.type == HookType.GIT


class TestHookParserFileOperations:
    """Tests for file-based parsing operations."""

    def test_parse_file(self):
        """Should parse hook from file."""
        parser = HookParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write('''#!/bin/bash
# ---
# type: git
# event: pre-commit
# priority: 10
# ---
echo "test"
''')
            temp_path = Path(f.name)

        try:
            hook = parser.parse_file(temp_path)

            assert hook is not None
            assert hook.metadata.type == HookType.GIT
            assert hook.metadata.priority == 10
            assert hook.script_path == temp_path
        finally:
            os.unlink(temp_path)

    def test_parse_directory(self):
        """Should parse all hooks in directory."""
        parser = HookParser()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create multiple hook files
            (tmpdir_path / "hook1.sh").write_text('''#!/bin/bash
# ---
# type: git
# event: pre-commit
# ---
''')
            (tmpdir_path / "hook2.py").write_text('''#!/usr/bin/env python3
# ---
# type: git
# event: pre-push
# ---
''')
            (tmpdir_path / "hook3.js").write_text('''// ---
// type: agent
// provider: test
// event: before-tool
// ---
''')
            # Create a hidden file (should be skipped)
            (tmpdir_path / ".hidden.sh").write_text('''#!/bin/bash
# ---
# type: git
# event: pre-commit
# ---
''')

            hooks = parser.parse_directory(tmpdir_path)

            assert len(hooks) == 3
            events = {h.metadata.event for h in hooks}
            assert events == {"pre-commit", "pre-push", "before-tool"}

    def test_parse_nonexistent_directory(self):
        """Should return empty list for nonexistent directory."""
        parser = HookParser()
        hooks = parser.parse_directory(Path("/nonexistent/path"))

        assert hooks == []

    def test_clear_errors(self):
        """Should clear error list."""
        parser = HookParser()
        # Use invalid YAML to trigger a parse error
        parser.parse_content(Path("test.sh"), "# ---\n# type: : invalid yaml\n# ---")

        assert len(parser.get_errors()) >= 1

        parser.clear_errors()
        assert len(parser.get_errors()) == 0


class TestHookParserMetadataFields:
    """Tests for parsing various metadata fields."""

    def test_all_basic_fields(self):
        """Should parse all basic metadata fields."""
        parser = HookParser()
        content = '''# ---
# type: agent
# provider: claude-code
# event: before-tool
# matcher:
#   - "*.py"
# priority: 5
# description: Log tool execution
# ---
'''
        hook = parser.parse_content(Path("test.sh"), content)

        assert hook is not None
        assert hook.metadata.type == HookType.AGENT
        assert hook.metadata.provider == "claude-code"
        assert hook.metadata.event == "before-tool"
        assert hook.metadata.matcher == ["*.py"]
        assert hook.metadata.priority == 5
        assert hook.metadata.description == "Log tool execution"

    def test_extra_fields(self):
        """Should parse extra metadata fields."""
        parser = HookParser()
        content = '''# ---
# type: git
# event: pre-commit
# custom_key: custom_value
# another_key: 123
# ---
'''
        hook = parser.parse_content(Path("test.sh"), content)

        assert hook is not None
        assert hook.metadata.extra.get("custom_key") == "custom_value"
        assert hook.metadata.extra.get("another_key") == 123

    def test_front_matter_line_tracking(self):
        """Should track front matter line positions."""
        parser = HookParser()
        content = '''#!/bin/bash
# Line 2
# ---
# type: git
# event: pre-commit
# ---
# Line 7
echo "test"
'''
        hook = parser.parse_content(Path("test.sh"), content)

        assert hook is not None
        assert hook.front_matter_start_line == 3
        assert hook.front_matter_end_line == 6

