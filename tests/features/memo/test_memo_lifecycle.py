import pytest
from pathlib import Path
from monoco.features.memo.core import add_memo, list_memos, delete_memo, get_inbox_path
from monoco.features.memo.models import Memo


def test_memo_lifecycle(tmp_path):
    """Test basic memo CRUD operations."""
    # Set up issues root
    issues_root = tmp_path / "Issues"
    issues_root.mkdir()
    
    # 1. Add some memos
    id1 = add_memo(issues_root, "Note 1")
    id2 = add_memo(issues_root, "Note 2")
    id3 = add_memo(issues_root, "Note 3")
    
    memos = list_memos(issues_root)
    assert len(memos) == 3
    assert any(m.uid == id1 for m in memos)
    assert any(m.uid == id2 for m in memos)
    assert any(m.uid == id3 for m in memos)
    
    # 2. Delete the middle one
    result = delete_memo(issues_root, id2)
    assert result is True
    
    memos = list_memos(issues_root)
    assert len(memos) == 2
    assert any(m.uid == id1 for m in memos)
    assert not any(m.uid == id2 for m in memos)
    assert any(m.uid == id3 for m in memos)
    
    # 3. Delete a non-existent one
    result = delete_memo(issues_root, "nonexistent")
    assert result is False
    assert len(list_memos(issues_root)) == 2
    
    # 4. Delete the first one
    result = delete_memo(issues_root, id1)
    assert result is True
    memos = list_memos(issues_root)
    assert len(memos) == 1
    memos = list_memos(issues_root)
    assert len(memos) == 1
    assert memos[0].uid == id3
    
    # 5. Delete the last one
    result = delete_memo(issues_root, id3)
    assert result is True
    assert len(list_memos(issues_root)) == 0
    
    # Check if file still exists but is empty (or just header)
    inbox_path = get_inbox_path(issues_root)
    content = inbox_path.read_text(encoding="utf-8")
    assert "Note 1" not in content
    assert "Note 2" not in content
    assert "Note 3" not in content


def test_memo_no_status_field(tmp_path):
    """Signal Queue Model: Memos don't have status field."""
    issues_root = tmp_path / "Issues"
    issues_root.mkdir()
    
    # Add a memo
    uid = add_memo(issues_root, "Test memo", memo_type="insight")
    
    # Load and verify
    memos = list_memos(issues_root)
    assert len(memos) == 1
    memo = memos[0]
    
    # Verify: Memo doesn't have status attribute (Signal Queue Model)
    assert not hasattr(memo, 'status') or memo.status is None
    assert not hasattr(memo, 'ref') or memo.ref is None
    
    # Verify: Other attributes work
    assert memo.uid == uid
    assert memo.content == "Test memo"
    assert memo.type == "insight"


def test_memo_to_markdown_no_status(tmp_path):
    """Signal Queue Model: Markdown doesn't include status."""
    memo = Memo(
        uid="abc123",
        content="Test content",
        type="feature",
        source="cli",
        author="User",
    )
    
    markdown = memo.to_markdown()
    
    # Should not contain status-related text
    assert "Status" not in markdown
    assert "pending" not in markdown
    assert "tracked" not in markdown
    assert "resolved" not in markdown
    assert "ref" not in markdown.lower()
    
    # Should contain standard fields
    assert "abc123" in markdown
    assert "Test content" in markdown
    assert "feature" in markdown


def test_memo_signal_queue_consumption(tmp_path):
    """Test Signal Queue consumption semantics.
    
    In Signal Queue Model:
    - File existence = signal pending
    - File cleared (header only) = signal consumed
    """
    issues_root = tmp_path / "Issues"
    issues_root.mkdir()
    
    # Add memos (signals created)
    add_memo(issues_root, "Signal 1")
    add_memo(issues_root, "Signal 2")
    
    # Verify: Signals exist
    memos = list_memos(issues_root)
    assert len(memos) == 2
    
    # Simulate consumption: Clear inbox
    inbox_path = get_inbox_path(issues_root)
    inbox_path.write_text("# Monoco Memos Inbox\n\n", encoding="utf-8")
    
    # Verify: Signals consumed
    memos = list_memos(issues_root)
    assert len(memos) == 0


def test_memo_parsing_backward_compatibility(tmp_path):
    """Test parsing of old-format memos (backward compatibility).
    
    Old format memos may have status/ref fields in markdown.
    New parser should ignore them without error.
    """
    issues_root = tmp_path / "Issues"
    issues_root.mkdir()
    memos_dir = issues_root.parent / "Memos"
    memos_dir.mkdir()
    inbox_path = memos_dir / "inbox.md"
    
    # Write old-format memo with status/ref
    inbox_path.write_text("""# Monoco Memos Inbox

## [abc123] 2026-01-15 10:00:00
- **From**: User
- **Source**: cli
- **Type**: insight
- **Status**: [x] Tracked
- **Ref**: FEAT-1234

Old format memo with status and ref
""", encoding="utf-8")
    
    # Should parse without error (ignoring status/ref)
    memos = list_memos(issues_root)
    assert len(memos) == 1
    
    memo = memos[0]
    assert memo.uid == "abc123"
    assert "Old format memo" in memo.content
    # Status and ref are not parsed in new model
    assert not hasattr(memo, 'status') or memo.status is None
    assert not hasattr(memo, 'ref') or memo.ref is None
