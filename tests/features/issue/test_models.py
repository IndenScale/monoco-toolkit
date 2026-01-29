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


def test_issue_id_parsing():
    """测试 IssueID 的解析和匹配逻辑。"""
    from monoco.features.issue.models import IssueID

    # 本地 ID
    id1 = IssueID("FEAT-1001")
    assert id1.namespace is None
    assert id1.local_id == "FEAT-1001"
    assert id1.is_local is True
    assert id1.matches("FEAT-1001")
    assert str(id1) == "FEAT-1001"

    # 带命名空间的 ID
    id2 = IssueID("toolkit::EPIC-0021")
    assert id2.namespace == "toolkit"
    assert id2.local_id == "EPIC-0021"
    assert id2.is_local is False
    assert id2.matches("toolkit::EPIC-0021")
    assert not id2.matches("EPIC-0021")
    assert str(id2) == "toolkit::EPIC-0021"


def test_generate_uid():
    """测试 UID 生成。"""
    from monoco.features.issue.models import generate_uid

    uid1 = generate_uid()
    uid2 = generate_uid()
    assert len(uid1) == 6
    assert len(uid2) == 6
    assert uid1 != uid2


def test_issue_isolation_model():
    """测试 IssueIsolation 模型。"""
    from monoco.features.issue.models import IssueIsolation

    data = {"type": "branch", "ref": "feat/test"}
    iso = IssueIsolation(**data)
    assert iso.type == "branch"
    assert iso.ref == "feat/test"
    assert iso.created_at is not None


def test_issue_metadata_epic_no_parent():
    """验证 epic 类型的任务不需要 parent。"""
    data = {"id": "EPIC-1001", "type": "epic", "title": "Top Level Epic"}
    meta = IssueMetadata(**data)
    assert meta.id == "EPIC-1001"
    assert meta.parent is None


def test_issue_metadata_extra_fields():
    """验证 extra 字段被允许（Pydantic extra='allow'）。"""
    data = {
        "id": "FEAT-0001",
        "type": "feature",
        "title": "Extra Field Test",
        "parent": "EPIC-0001",
        "custom_info": "hello",
    }
    meta = IssueMetadata(**data)
    assert meta.custom_info == "hello"


def test_issue_metadata_status_normalization_and_lowercase():
    """验证 status 自动转为小写。"""
    data = {
        "id": "FIX-0001",
        "type": "FIX",
        "status": "OPEN",  # 大写
        "title": "Lowercase Test",
        "parent": "EPIC-0001",
    }
    meta = IssueMetadata(**data)
    assert meta.status == IssueStatus.OPEN
    assert meta.type == IssueType.FIX
