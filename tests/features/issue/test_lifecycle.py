import pytest
from pathlib import Path
from monoco.features.issue import core
from monoco.features.issue.models import (
    IssueType,
    IssueStatus,
    IssueStage,
    IssueSolution,
)


def test_create_issue_basic(issues_root):
    """测试创建 Issue 文件的基本功能。"""
    title = "Test Feature"
    meta, path = core.create_issue_file(
        issues_root=issues_root,
        issue_type=IssueType.FEATURE,
        title=title,
        parent="EPIC-0001",
    )

    assert meta.id == "FEAT-0001"
    assert path.exists()
    assert meta.status == IssueStatus.OPEN
    assert meta.stage == IssueStage.DRAFT
    assert "#EPIC-0001" in meta.tags
    assert "#FEAT-0001" in meta.tags


def test_issue_id_sequence(issues_root):
    """测试 Issue ID 的自动递增。"""
    core.create_issue_file(issues_root, IssueType.FIX, "Fix 1", parent="EPIC-0001")
    meta2, _ = core.create_issue_file(
        issues_root, IssueType.FIX, "Fix 2", parent="EPIC-0001"
    )

    assert meta2.id == "FIX-0002"


def test_update_issue_status_transition(issues_root):
    """测试 Issue 状态流转（Open -> Backlog -> Open -> Doing -> Review -> Closed）。"""
    # 准备：创建一个 EPIC-0001 以满足 parent 校验
    core.create_issue_file(issues_root, IssueType.EPIC, "Root Epic")

    meta, _ = core.create_issue_file(
        issues_root, IssueType.FEATURE, "Lifecycle Test", parent="EPIC-0001"
    )
    issue_id = meta.id

    # 1. Move to Backlog
    meta = core.update_issue(issues_root, issue_id, status=IssueStatus.BACKLOG)
    assert meta.status == IssueStatus.BACKLOG
    assert meta.stage == IssueStage.FREEZED

    # 2. Move back to Open (Explicitly set stage to draft to match lifecycle)
    meta = core.update_issue(
        issues_root, issue_id, status=IssueStatus.OPEN, stage=IssueStage.DRAFT
    )
    assert meta.status == IssueStatus.OPEN
    assert meta.stage == IssueStage.DRAFT

    # 3. Start (Stage: Doing)
    meta = core.update_issue(issues_root, issue_id, stage=IssueStage.DOING)
    assert meta.stage == IssueStage.DOING

    # Resolve all tasks and AC to allow moving to REVIEW/DONE
    path = Path(meta.path)
    content = path.read_text().replace("- [ ]", "- [x]")
    # Remove placeholder comment and add actual review content
    content = content.replace(
        "<!-- Required for Review/Done stage. Record review feedback here. -->",
        "Review completed successfully."
    )
    path.write_text(content)

    # 4. Submit for Review (Review)
    meta = core.update_issue(issues_root, issue_id, stage=IssueStage.REVIEW)
    assert meta.stage == IssueStage.REVIEW

    # 5. Close (Status: Closed) - Requires solution
    meta = core.update_issue(
        issues_root,
        issue_id,
        status=IssueStatus.CLOSED,
        solution=IssueSolution.IMPLEMENTED,
    )
    assert meta.status == IssueStatus.CLOSED
    assert meta.solution == IssueSolution.IMPLEMENTED
    assert meta.stage == IssueStage.DONE


def test_issue_dependencies_blocking_closure(issues_root):
    """测试依赖项未关闭时，阻止父任务关闭。"""
    core.create_issue_file(issues_root, IssueType.EPIC, "Root Epic")

    dep_meta, _ = core.create_issue_file(
        issues_root, IssueType.FIX, "Dependency", parent="EPIC-0001"
    )
    main_meta, _ = core.create_issue_file(
        issues_root,
        IssueType.FEATURE,
        "Main Task",
        parent="EPIC-0001",
        dependencies=[dep_meta.id],
    )

    # 准备主任务：Draft -> Doing -> Review
    core.update_issue(issues_root, main_meta.id, stage=IssueStage.DOING)

    path = Path(main_meta.path)
    content = path.read_text().replace("- [ ]", "- [x]")
    # Remove placeholder comment and add actual review content
    content = content.replace(
        "<!-- Required for Review/Done stage. Record review feedback here. -->",
        "Review completed successfully."
    )
    path.write_text(content)

    core.update_issue(issues_root, main_meta.id, stage=IssueStage.REVIEW)

    # 尝试在依赖项未关闭时关闭主任务
    with pytest.raises(ValueError) as excinfo:
        core.update_issue(
            issues_root,
            main_meta.id,
            status=IssueStatus.CLOSED,
            solution=IssueSolution.IMPLEMENTED,
        )
    assert "Dependency Block" in str(excinfo.value)

    # 准备依赖项并关闭之
    dep_path = Path(dep_meta.path)
    dep_content = dep_path.read_text().replace("- [ ]", "- [x]")
    # Remove placeholder comment and add actual review content
    dep_content = dep_content.replace(
        "<!-- Required for Review/Done stage. Record review feedback here. -->",
        "Review completed successfully."
    )
    dep_path.write_text(dep_content)

    # Fix: Draft -> Doing -> Review -> Closed
    core.update_issue(issues_root, dep_meta.id, stage=IssueStage.DOING)
    core.update_issue(issues_root, dep_meta.id, stage=IssueStage.REVIEW)
    core.update_issue(
        issues_root,
        dep_meta.id,
        status=IssueStatus.CLOSED,
        solution=IssueSolution.IMPLEMENTED,
    )

    # 现在可以关闭主任务了
    core.update_issue(
        issues_root,
        main_meta.id,
        status=IssueStatus.CLOSED,
        solution=IssueSolution.IMPLEMENTED,
    )
