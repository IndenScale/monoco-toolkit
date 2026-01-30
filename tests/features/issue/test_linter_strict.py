import textwrap
from monoco.features.issue import core
from monoco.features.issue.linter import check_integrity
from monoco.features.issue.models import IssueType


def test_linter_detects_filename_id_mismatch(issues_root):
    """验证 Linter 能发现文件名中的 ID 与 Frontmatter 不一致。"""
    # 1. 创建一个合法的 Issue
    meta, path = core.create_issue_file(
        issues_root, IssueType.FIX, "Filename Mismatch", parent="EPIC-0001"
    )

    # 2. 手动重命名文件，使 ID 冲突
    incorrect_path = path.parent / f"FIX-9999-{meta.title.lower().replace(' ', '-')}.md"
    path.rename(incorrect_path)

    # 3. 运行 Linter
    diagnostics = check_integrity(issues_root)

    # 4. 验证错误
    filename_errors = [
        d
        for d in diagnostics
        if "Filename Error" in d.message and "must start with ID" in d.message
    ]
    assert len(filename_errors) >= 1
    assert "must start with ID 'FIX-0001-'" in filename_errors[0].message


def test_linter_detects_duplicate_ids(issues_root):
    """验证 Linter 能发现跨文件的重复 ID。"""
    # 1. 创建第一个 Issue
    core.create_issue_file(
        issues_root, IssueType.FIX, "First Issue", parent="EPIC-0001"
    )

    # 2. 手动创建第二个 Issue，使用相同的 ID
    second_path = issues_root / "Fixes" / "open" / "FIX-0001-Duplicate.md"
    second_path.parent.mkdir(parents=True, exist_ok=True)
    second_path.write_text(
        textwrap.dedent(
            """\
        ---
        id: FIX-0001
        type: fix
        status: open
        stage: draft
        title: Duplicate Issue
        parent: EPIC-0001
        tags: ["#EPIC-0001", "#FIX-0001"]
        ---

        ## FIX-0001: Duplicate Issue

        - [ ] Task
        - [ ] Task
    """
        )
    )

    # 3. 运行 Linter
    diagnostics = check_integrity(issues_root)

    # 4. 验证重复 ID 错误
    dup_errors = [d for d in diagnostics if "Duplicate ID Violation" in d.message]
    assert len(dup_errors) >= 1
    assert "ID 'FIX-0001' is already used" in dup_errors[0].message


def test_linter_detects_missing_slug(issues_root):
    """验证 Linter 能发现文件名缺少 Slug。"""
    # 1. 创建 Issue
    meta, path = core.create_issue_file(
        issues_root, IssueType.FIX, "Missing Slug", parent="EPIC-0001"
    )

    # 2. 重命名为仅带 ID 的文件名
    incorrect_path = path.parent / f"{meta.id}-.md"
    path.rename(incorrect_path)

    # 3. 运行 Linter
    diagnostics = check_integrity(issues_root)

    # 4. 验证错误
    slug_errors = [d for d in diagnostics if "missing title slug" in d.message]
    assert len(slug_errors) >= 1
