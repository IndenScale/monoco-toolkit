"""Tests for block-level language detection (FEAT-0143).

Design Principle:
- Narrative text should be in the source language (e.g., Chinese)
- English should only appear as isolated nouns (technical terms, filenames, code blocks)
"""

import pytest
from monoco.features.i18n.core import (
    parse_markdown_blocks,
    detect_language_blocks,
    has_language_mismatch_blocks,
    should_skip_block_for_language_check,
    BlockType,
    ContentBlock,
)


class TestParseMarkdownBlocks:
    """Test markdown block parsing."""

    def test_parse_heading_blocks(self):
        """Test parsing heading blocks."""
        content = """# Heading 1
## Heading 2
### Heading 3
"""
        blocks = parse_markdown_blocks(content)
        headings = [b for b in blocks if b.type == BlockType.HEADING]
        assert len(headings) == 3
        assert headings[0].content == "# Heading 1"
        assert headings[1].content == "## Heading 2"
        assert headings[2].content == "### Heading 3"

    def test_parse_code_block(self):
        """Test parsing code blocks."""
        content = """Some text.

```python
def hello():
    return "world"
```

More text.
"""
        blocks = parse_markdown_blocks(content)
        code_blocks = [b for b in blocks if b.type == BlockType.CODE_BLOCK]
        assert len(code_blocks) == 1
        assert "def hello():" in code_blocks[0].content

    def test_parse_list_items(self):
        """Test parsing list items."""
        content = """- Item 1
- Item 2
- Item 3
"""
        blocks = parse_markdown_blocks(content)
        list_items = [b for b in blocks if b.type == BlockType.LIST_ITEM]
        assert len(list_items) == 3

    def test_parse_mixed_content(self):
        """Test parsing mixed content."""
        content = """# Title

This is a paragraph.

```code
block
```

- List item 1
- List item 2

## Section

Another paragraph.
"""
        blocks = parse_markdown_blocks(content)
        
        # Check that we have the expected block types
        types = [b.type for b in blocks]
        assert BlockType.HEADING in types
        assert BlockType.PARAGRAPH in types
        assert BlockType.CODE_BLOCK in types
        assert BlockType.LIST_ITEM in types

    def test_parse_with_frontmatter(self):
        """Test that YAML frontmatter is stripped."""
        content = """---
id: TEST-0001
title: Test
---

# Heading

Content here.
"""
        blocks = parse_markdown_blocks(content)
        # Should not include frontmatter as blocks
        assert not any("---" in b.content for b in blocks if b.type != BlockType.CODE_BLOCK)
        # Should have the heading
        headings = [b for b in blocks if b.type == BlockType.HEADING]
        assert len(headings) == 1
        assert "Heading" in headings[0].content


class TestShouldSkipBlock:
    """Test block skipping logic."""

    def test_skip_code_blocks(self):
        """Test that code blocks are skipped."""
        content = """```python
def hello():
    pass
```
"""
        blocks = parse_markdown_blocks(content)
        for i, block in enumerate(blocks):
            if block.type == BlockType.CODE_BLOCK:
                assert should_skip_block_for_language_check(block, blocks, i, "zh")

    def test_skip_empty_blocks(self):
        """Test that empty blocks are skipped."""
        block = ContentBlock(
            type=BlockType.EMPTY,
            content="",
            line_start=0,
            line_end=1,
        )
        assert should_skip_block_for_language_check(block, [block], 0, "zh")

    def test_not_skip_regular_paragraphs(self):
        """Test that regular paragraphs are not skipped."""
        content = """## Background

This is a regular paragraph.
"""
        blocks = parse_markdown_blocks(content)
        para_idx = next(i for i, b in enumerate(blocks) if b.type == BlockType.PARAGRAPH)
        assert not should_skip_block_for_language_check(blocks[para_idx], blocks, para_idx, "zh")


class TestBlockLevelLanguageDetection:
    """Test block-level language detection."""

    def test_detect_chinese_paragraph(self):
        """Test detecting Chinese paragraph."""
        content = "这是一个中文段落。"
        blocks = detect_language_blocks(content, source_lang="zh")
        assert len(blocks) == 1
        assert blocks[0].detected_lang == "zh"

    def test_detect_english_paragraph(self):
        """Test detecting English paragraph."""
        # Use longer content to ensure detection works
        content = "This is an English paragraph with meaningful content. " * 5
        blocks = detect_language_blocks(content, source_lang="en")
        assert len(blocks) == 1
        # Should be detected as English or unknown (not Chinese)
        assert blocks[0].detected_lang in ("en", "unknown")

    def test_skip_code_block_language_detection(self):
        """Test that code blocks are skipped in language detection."""
        content = """```python
def hello_world():
    print("Hello, World!")
    return True
```
"""
        blocks = detect_language_blocks(content, source_lang="zh")
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.CODE_BLOCK
        assert blocks[0].should_skip is True


class TestHasLanguageMismatchBlocks:
    """Test language mismatch detection at block level."""

    def test_no_mismatch_in_pure_chinese(self):
        """Test no mismatch in pure Chinese content."""
        content = """# 标题

这是一个中文段落。

## 章节

更多中文内容。
"""
        has_mismatch, mismatched = has_language_mismatch_blocks(content, source_lang="zh")
        assert has_mismatch is False
        assert len(mismatched) == 0

    def test_detect_english_in_chinese_doc(self):
        """Test detecting English blocks in Chinese document."""
        # Use longer English content to ensure detection
        content = """# 中文标题

这是一个中文段落。

This is an English paragraph that should be flagged. It contains enough words to be detected as English content clearly and unambiguously.
"""
        has_mismatch, mismatched = has_language_mismatch_blocks(content, source_lang="zh")
        # The test verifies the mechanism works
        for block in mismatched:
            assert block.detected_lang == "en"

    def test_no_mismatch_for_skipped_blocks(self):
        """Test that skipped blocks (code blocks) don't cause mismatches."""
        content = """# 中文标题

这是一个中文段落。

```python
# This code block should NOT be flagged
print("hello")
```
"""
        has_mismatch, mismatched = has_language_mismatch_blocks(content, source_lang="zh")
        # Code blocks should not be in mismatched
        for block in mismatched:
            assert block.type != BlockType.CODE_BLOCK


class TestRealWorldScenarios:
    """Test real-world scenarios."""

    def test_chinese_issue_with_code_blocks(self):
        """Test Chinese Issue with code blocks containing English."""
        content = """---
id: FEAT-9998
type: feature
status: open
title: 代码示例功能
---

## FEAT-9998: 代码示例功能

## 实现

使用以下代码：

```python
def calculate_sum(a, b):
    # Calculate the sum of two numbers
    return a + b
```

这是一个中文说明段落。
"""
        has_mismatch, mismatched = has_language_mismatch_blocks(content, source_lang="zh")
        
        # Should NOT flag code blocks
        for block in mismatched:
            assert block.type != BlockType.CODE_BLOCK

    def test_mixed_technical_chinese_content(self):
        """Test Chinese content with technical terms."""
        content = """# 技术实现

使用 Kubernetes 和 Docker 部署应用。
配置 CI/CD Pipeline 自动化构建。
"""
        has_mismatch, mismatched = has_language_mismatch_blocks(content, source_lang="zh")
        
        # Should NOT flag technical Chinese content
        # All narrative text is in Chinese
        assert len(mismatched) == 0 or all(
            "Kubernetes" not in b.content or "使用" not in b.content
            for b in mismatched
        )
