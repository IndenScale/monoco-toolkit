import tempfile
from pathlib import Path
from monoco.features.issue import core
from monoco.features.issue.migration import migrate_issues_directory
from monoco.features.issue.models import IssueType, IssueStage


def test_issue_migration():
    """
    Test the migration of legacy issue structure to the current standard.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        issues_root = Path(tmp_dir) / "Issues"
        issues_root.mkdir()

        # 1. Setup Legacy Structure
        # -------------------------
        # Old DIR: STORIES
        stories_dir = issues_root / "STORIES" / "open"
        stories_dir.mkdir(parents=True)

        legacy_content = """---
id: STORY-1001
type: story
status: open
stage: todo
title: Legacy Story
parent: EPIC-0000
---

## STORY-1001: Legacy Story
"""
        legacy_file = stories_dir / "STORY-1001-legacy.md"
        legacy_file.write_text(legacy_content)

        # 2. Run Migration
        # ----------------
        migrate_issues_directory(issues_root)

        # 3. Verify Results
        # -----------------
        # Check DIR rename
        assert not (issues_root / "STORIES").exists()
        assert (issues_root / "Features").exists()

        # Check File rename
        new_file = issues_root / "Features" / "open" / "FEAT-1001-legacy.md"
        assert new_file.exists()

        # Check Content update
        meta = core.parse_issue(new_file)
        assert meta.id == "FEAT-1001"
        assert meta.type == IssueType.FEATURE
        assert meta.stage == IssueStage.DRAFT
        assert meta.uid is not None

        content = new_file.read_text()
        assert "## FEAT-1001" in content


if __name__ == "__main__":
    test_issue_migration()
    print("✅ Migration test passed.")
