import pytest
from pathlib import Path
from monoco.features.memo.core import add_memo, list_memos, delete_memo, get_inbox_path

def test_memo_lifecycle(tmp_path):
    # Set up issues root
    issues_root = tmp_path / "Issues"
    issues_root.mkdir()
    
    # 1. Add some memos
    id1 = add_memo(issues_root, "Note 1")
    id2 = add_memo(issues_root, "Note 2")
    id3 = add_memo(issues_root, "Note 3")
    
    memos = list_memos(issues_root)
    assert len(memos) == 3
    assert any(m["id"] == id1 for m in memos)
    assert any(m["id"] == id2 for m in memos)
    assert any(m["id"] == id3 for m in memos)
    
    # 2. Delete the middle one
    result = delete_memo(issues_root, id2)
    assert result is True
    
    memos = list_memos(issues_root)
    assert len(memos) == 2
    assert any(m["id"] == id1 for m in memos)
    assert not any(m["id"] == id2 for m in memos)
    assert any(m["id"] == id3 for m in memos)
    
    # 3. Delete a non-existent one
    result = delete_memo(issues_root, "nonexistent")
    assert result is False
    assert len(list_memos(issues_root)) == 2
    
    # 4. Delete the first one
    result = delete_memo(issues_root, id1)
    assert result is True
    memos = list_memos(issues_root)
    assert len(memos) == 1
    assert memos[0]["id"] == id3
    
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
