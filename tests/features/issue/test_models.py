import pytest
from pydantic import ValidationError
from monoco.features.issue.models import (
    IssueMetadata,
    IssueType,
    IssueStatus,
    IssueStage,
    IssueSolution,
)


def test_issue_metadata_valid_minimal():
    """测试最基本的合法 IssueMetadata。"""
    data = {
        "id": "FEAT-0001",
        "type": "feature",
        "title": "Test Issue",
        "parent": "EPIC-0001",
    }
    meta = IssueMetadata(**data)
    assert meta.id == "FEAT-0001"
    assert meta.type == IssueType.FEATURE
    assert meta.status == IssueStatus.OPEN
    assert meta.stage is None


def test_issue_metadata_case_insensitivity():
    """测试字段的大写字母自动纠偏（通过 normalize_fields）。"""
    data = {
        "ID": "FIX-0001",
        "Type": "FIX",
        "Status": "OPEN",
        "Title": "Case Insensitive Title",
        "Solution": "IMPLEMENTED",
        "Parent": "EPIC-0001",
    }
    meta = IssueMetadata(**data)
    assert meta.id == "FIX-0001"
    assert meta.type == IssueType.FIX
    assert meta.status == IssueStatus.OPEN
    assert meta.solution == IssueSolution.IMPLEMENTED


def test_issue_metadata_invalid_type():
    """测试非法的 Issue 类型。"""
    data = {
        "id": "TASK-0001",
        "type": "task",  # 不在枚举中
        "title": "Invalid Type",
        "parent": "EPIC-0001",
    }
    with pytest.raises(ValidationError) as excinfo:
        IssueMetadata(**data)
    assert "type" in str(excinfo.value)


def test_issue_metadata_invalid_solution():
    """测试非法的 Solution 字符串（例如之前的自由文本报错情况）。"""
    data = {
        "id": "FEAT-0005",
        "type": "feature",
        "status": "closed",
        "title": "Invalid Solution",
        "solution": "Finished but with custom text",  # 应报错
        "parent": "EPIC-0001",
    }
    with pytest.raises(ValidationError) as excinfo:
        IssueMetadata(**data)
    assert "solution" in str(excinfo.value)


def test_issue_metadata_stage_normalization():
    """测试 stage 字段的特殊纠偏逻辑（如 todo -> draft）。"""
    data = {
        "id": "CHORE-0001",
        "type": "chore",
        "title": "Stage Test",
        "stage": "TODO",
        "parent": "EPIC-0001",
    }
    meta = IssueMetadata(**data)
    assert meta.stage == IssueStage.DRAFT


def test_issue_metadata_enum_value_identity():
    """验证解析后的值确实是 Enum 实例而不是单纯的字符串。"""
    data = {"id": "EPIC-0001", "type": "epic", "title": "Enum Identity Test"}
    meta = IssueMetadata(**data)
    assert isinstance(meta.type, IssueType)
    assert meta.type == IssueType.EPIC


def test_issue_metadata_closed_requires_solution():
    """验证已关闭的任务必须有 solution。"""
    data = {
        "id": "FIX-0001",
        "type": "fix",
        "status": "closed",
        "title": "Unsolved Mystery",
        "parent": "EPIC-0001",
    }
    with pytest.raises(ValidationError) as excinfo:
        IssueMetadata(**data)
    assert "is closed but 'solution' is missing" in str(excinfo.value)


def test_issue_metadata_feature_requires_parent():
    """验证 feature 类型的任务必须有 parent。"""
    data = {"id": "FEAT-0099", "type": "feature", "title": "Orphan Feature"}
    with pytest.raises(ValidationError) as excinfo:
        IssueMetadata(**data)
    assert "must have a 'parent' reference" in str(excinfo.value)
