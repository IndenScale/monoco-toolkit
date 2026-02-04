"""
Unit tests for FieldWatcher and YAMLFrontMatterExtractor.
"""

import pytest
from pathlib import Path

from monoco.core.automation.field_watcher import (
    FieldCondition,
    FieldWatcher,
    YAMLFrontMatterExtractor,
)
from monoco.core.watcher.base import ChangeType, FieldChange


class TestYAMLFrontMatterExtractor:
    """Test suite for YAMLFrontMatterExtractor."""
    
    def test_extract_frontmatter(self):
        """Can extract YAML front matter from markdown."""
        content = """---
id: FEAT-0123
status: open
stage: doing
title: Test Issue
---

# Content here
"""
        
        frontmatter = YAMLFrontMatterExtractor.extract(content)
        
        assert frontmatter is not None
        assert frontmatter["id"] == "FEAT-0123"
        assert frontmatter["status"] == "open"
        assert frontmatter["stage"] == "doing"
        assert frontmatter["title"] == "Test Issue"
    
    def test_extract_no_frontmatter(self):
        """Returns None for content without front matter."""
        content = """# Just a heading

Some content
"""
        
        frontmatter = YAMLFrontMatterExtractor.extract(content)
        
        assert frontmatter is None
    
    def test_get_field(self):
        """Can get specific field from front matter."""
        content = """---
id: FEAT-0123
status: open
---

Content
"""
        
        status = YAMLFrontMatterExtractor.get_field(content, "status")
        missing = YAMLFrontMatterExtractor.get_field(content, "missing")
        
        assert status == "open"
        assert missing is None
    
    def test_detect_changes(self):
        """Can detect field changes between versions."""
        old_content = """---
id: FEAT-0123
status: open
stage: backlog
---

Content
"""
        new_content = """---
id: FEAT-0123
status: open
stage: doing
---

Content
"""
        
        changes = YAMLFrontMatterExtractor.detect_changes(old_content, new_content)
        
        assert len(changes) == 1
        assert changes[0].field_name == "stage"
        assert changes[0].old_value == "backlog"
        assert changes[0].new_value == "doing"
        assert changes[0].change_type == ChangeType.MODIFIED
    
    def test_detect_changes_with_tracked_fields(self):
        """Can detect changes only in tracked fields."""
        old_content = """---
id: FEAT-0123
status: open
stage: backlog
assignee: alice
---

Content
"""
        new_content = """---
id: FEAT-0123
status: open
stage: doing
assignee: bob
---

Content
"""
        
        changes = YAMLFrontMatterExtractor.detect_changes(
            old_content,
            new_content,
            tracked_fields=["stage"],
        )
        
        assert len(changes) == 1
        assert changes[0].field_name == "stage"
    
    def test_detect_field_created(self):
        """Detects when a field is added."""
        old_content = """---
id: FEAT-0123
---

Content
"""
        new_content = """---
id: FEAT-0123
status: open
---

Content
"""
        
        changes = YAMLFrontMatterExtractor.detect_changes(old_content, new_content)
        
        assert len(changes) == 1
        assert changes[0].field_name == "status"
        assert changes[0].old_value is None
        assert changes[0].new_value == "open"
        assert changes[0].change_type == ChangeType.CREATED
    
    def test_detect_field_deleted(self):
        """Detects when a field is removed."""
        old_content = """---
id: FEAT-0123
status: open
---

Content
"""
        new_content = """---
id: FEAT-0123
---

Content
"""
        
        changes = YAMLFrontMatterExtractor.detect_changes(old_content, new_content)
        
        assert len(changes) == 1
        assert changes[0].field_name == "status"
        assert changes[0].old_value == "open"
        assert changes[0].new_value is None
        assert changes[0].change_type == ChangeType.DELETED


class TestFieldCondition:
    """Test suite for FieldCondition."""
    
    def test_evaluate_eq(self):
        """Can evaluate equality condition."""
        condition = FieldCondition("status", "eq", "open")
        
        assert condition.evaluate({"status": "open"}) is True
        assert condition.evaluate({"status": "closed"}) is False
    
    def test_evaluate_ne(self):
        """Can evaluate not-equal condition."""
        condition = FieldCondition("status", "ne", "open")
        
        assert condition.evaluate({"status": "closed"}) is True
        assert condition.evaluate({"status": "open"}) is False
    
    def test_evaluate_gt(self):
        """Can evaluate greater-than condition."""
        condition = FieldCondition("count", "gt", 5)
        
        assert condition.evaluate({"count": 10}) is True
        assert condition.evaluate({"count": 3}) is False
    
    def test_evaluate_in(self):
        """Can evaluate in condition."""
        condition = FieldCondition("status", "in", ["open", "doing"])
        
        assert condition.evaluate({"status": "open"}) is True
        assert condition.evaluate({"status": "closed"}) is False
    
    def test_evaluate_contains(self):
        """Can evaluate contains condition."""
        condition = FieldCondition("tags", "contains", "urgent")
        
        assert condition.evaluate({"tags": ["urgent", "bug"]}) is True
        assert condition.evaluate({"tags": ["feature"]}) is False
    
    def test_evaluate_exists(self):
        """Can evaluate exists condition."""
        condition = FieldCondition("assignee", "exists", None)
        
        assert condition.evaluate({"assignee": "alice"}) is True
        assert condition.evaluate({"status": "open"}) is False


class TestFieldWatcher:
    """Test suite for FieldWatcher."""
    
    def test_field_watcher_creation(self):
        """FieldWatcher can be created."""
        watcher = FieldWatcher(tracked_fields=["status", "stage"])
        
        assert watcher.tracked_fields == ["status", "stage"]
    
    def test_check_file_new(self):
        """FieldWatcher detects new file."""
        watcher = FieldWatcher(tracked_fields=["status", "stage"])
        
        content = """---
id: FEAT-0123
status: open
stage: doing
---

Content
"""
        
        changes = watcher.check_file("/test.md", content)
        
        # First check reports all fields as CREATED (no previous values)
        assert len(changes) == 2
        assert all(c.change_type == ChangeType.CREATED for c in changes)
        
        # Cache should be populated
        cached = watcher.get_cached_fields("/test.md")
        assert cached["status"] == "open"
        assert cached["stage"] == "doing"
    
    def test_check_file_modified(self):
        """FieldWatcher detects field changes."""
        watcher = FieldWatcher(tracked_fields=["status", "stage"])
        
        content1 = """---
id: FEAT-0123
status: open
stage: backlog
---

Content
"""
        content2 = """---
id: FEAT-0123
status: open
stage: doing
---

Content
"""
        
        # First check
        watcher.check_file("/test.md", content1)
        
        # Second check with changes
        changes = watcher.check_file("/test.md", content2)
        
        assert len(changes) == 1
        assert changes[0].field_name == "stage"
        assert changes[0].old_value == "backlog"
        assert changes[0].new_value == "doing"
    
    def test_add_condition(self):
        """Conditions can be added to watcher."""
        watcher = FieldWatcher()
        condition = FieldCondition("status", "eq", "open")
        
        watcher.add_condition(condition)
        
        assert len(watcher._conditions) == 1
    
    def test_add_callback(self):
        """Callbacks can be added to watcher."""
        watcher = FieldWatcher()
        callback = lambda path, cond, fields: None
        
        watcher.add_callback(callback)
        
        assert len(watcher._condition_callbacks) == 1
    
    def test_clear_cache(self):
        """Cache can be cleared."""
        watcher = FieldWatcher(tracked_fields=["status"])
        
        content = """---
status: open
---
"""
        watcher.check_file("/test.md", content)
        
        assert watcher.get_cached_fields("/test.md") is not None
        
        watcher.clear_cache("/test.md")
        
        assert watcher.get_cached_fields("/test.md") is None
    
    def test_clear_all_cache(self):
        """All cache can be cleared."""
        watcher = FieldWatcher(tracked_fields=["status"])
        
        content = """---
status: open
---
"""
        watcher.check_file("/test1.md", content)
        watcher.check_file("/test2.md", content)
        
        watcher.clear_cache()
        
        assert watcher.get_cached_fields("/test1.md") is None
        assert watcher.get_cached_fields("/test2.md") is None
    
    def test_get_stats(self):
        """FieldWatcher provides statistics."""
        watcher = FieldWatcher(tracked_fields=["status", "stage"])
        
        content = """---
status: open
stage: doing
---
"""
        watcher.check_file("/test.md", content)
        
        stats = watcher.get_stats()
        
        assert stats["tracked_files"] == 1
        assert stats["tracked_fields"] == ["status", "stage"]
        assert stats["conditions"] == 0
