"""
Tests for Git path unquoting functionality.

Verifies that _unquote_git_path correctly decodes Git C-quoting format paths
to native Unicode strings.
"""
import pytest
from monoco.features.issue.core import _unquote_git_path


class TestUnquoteGitPath:
    """Test suite for _unquote_git_path function."""

    def test_ascii_path_unchanged(self):
        """Standard ASCII paths without quotes should remain unchanged."""
        assert _unquote_git_path("Issues/Features/open/FEAT-0001-test.md") == \
               "Issues/Features/open/FEAT-0001-test.md"

    def test_simple_path(self):
        """Simple relative paths should remain unchanged."""
        assert _unquote_git_path("src/main.py") == "src/main.py"
        assert _unquote_git_path("README.md") == "README.md"

    def test_chinese_path(self):
        """Chinese characters encoded in octal should be decoded correctly."""
        # \351\207\215 = UTF-8 bytes for '重'
        assert _unquote_git_path('"Issues/FEAT-0012-\\351\\207\\215.md"') == \
               "Issues/FEAT-0012-重.md"

    def test_chinese_multi_character(self):
        """Multiple Chinese characters should all be decoded."""
        # \351\207\215\346\236\204 = 重构
        assert _unquote_git_path('"path-\\351\\207\\215\\346\\236\\204.md"') == \
               "path-重构.md"

    def test_path_with_spaces(self):
        """Spaces escaped as \\040 should be decoded to actual spaces."""
        assert _unquote_git_path('"path\\040with\\040space.md"') == \
               "path with space.md"

    def test_mixed_special_characters(self):
        """Paths with mix of Chinese and spaces."""
        # \351\207\215 (重) + space (\040) + test
        assert _unquote_git_path('"\\351\\207\\215\\040test.md"') == \
               "重 test.md"

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert _unquote_git_path("") == ""

    def test_whitespace_only(self):
        """Whitespace-only string should return empty after strip."""
        assert _unquote_git_path("   ") == ""

    def test_single_quote_not_decoded(self):
        """Single quote should not be treated as C-quoting."""
        assert _unquote_git_path("'single-quoted'") == "'single-quoted'"

    def test_unmatched_quotes(self):
        """Unmatched quotes should not trigger decoding."""
        # Only opening quote
        assert _unquote_git_path('"unmatched') == '"unmatched'
        # Only closing quote
        assert _unquote_git_path('unmatched"') == 'unmatched"'

    def test_empty_quotes(self):
        """Empty quoted string should return empty string."""
        assert _unquote_git_path('""') == ""

    def test_real_world_chinese_issue_title(self):
        """
        Real-world example from FIX-0012 issue.

        Git diff --name-only output for Chinese filenames looks like:
        "Issues/Features/open/FEAT-XXXX-\351\207\215\346\236\204-..."
        """
        git_output = '"Issues/Features/open/FEAT-0165-\\351\\207\\215\\346\\236\\204-memo-inbox-\\344\\270\\272\\344\\277\\241\\345\\217\\267\\351\\230\\237\\345\\210\\227\\346\\250\\241\\345\\236\\213-\\346\\266\\210\\350\\264\\271\\345\\215\\263\\351\\224\\200\\346\\257\\201.md"'

        expected = "Issues/Features/open/FEAT-0165-重构-memo-inbox-为信号队列模型-消费即销毁.md"

        assert _unquote_git_path(git_output) == expected

    def test_already_decoded_path_unchanged(self):
        """Paths already decoded (no quotes) should remain unchanged."""
        assert _unquote_git_path("Issues/Features/open/FEAT-0165-重构.md") == \
               "Issues/Features/open/FEAT-0165-重构.md"

    def test_nested_directory_with_unicode(self):
        """Nested paths with Unicode characters."""
        # \346\226\207\346\241\243 = 文档
        assert _unquote_git_path('"docs/\\346\\226\\207\\346\\241\\243/\\351\\207\\215\\350\\246\\201.md"') == \
               "docs/文档/重要.md"

    def test_hyphen_and_underscore(self):
        """Hyphens and underscores in filenames should work correctly."""
        assert _unquote_git_path('"test-file_name.md"') == "test-file_name.md"
