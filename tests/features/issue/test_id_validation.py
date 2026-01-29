import pytest
import textwrap
from pydantic import ValidationError
from monoco.features.issue.models import IssueMetadata
from monoco.features.issue.validator import IssueValidator
from monoco.core.lsp import DiagnosticSeverity


def test_issue_metadata_invalid_id_suffix():
    """验证 IssueMetadata 拒绝带后缀的 ID。"""
    data = {
        "id": "FEAT-0001-1",
        "type": "feature",
        "title": "Invalid ID",
        "parent": "EPIC-0001",
    }
    with pytest.raises(ValidationError) as excinfo:
        IssueMetadata(**data)

    assert "Invalid Issue ID format" in str(excinfo.value)
    assert "Expected 'TYPE-XXXX'" in str(excinfo.value)


def test_issue_metadata_valid_ids():
    """验证合法的 ID 格式仍能运行。"""
    valid_ids = ["FEAT-0001", "FIX-9999", "CHORE-1234", "EPIC-0000"]
    for issue_id in valid_ids:
        data = {
            "id": issue_id,
            "type": "feature"
            if "FEAT" in issue_id
            else "fix"
            if "FIX" in issue_id
            else "chore"
            if "CHORE" in issue_id
            else "epic",
            "title": "Valid ID",
        }
        if data["type"] != "epic":
            data["parent"] = "EPIC-0000"

        meta = IssueMetadata(**data)
        assert meta.id == issue_id


def test_issue_validator_invalid_id_references():
    """验证 IssueValidator 能发现正文中非法的 ID 引用。"""
    validator = IssueValidator()

    # 一个合法的元数据，但正文中包含非法引用
    meta_data = {
        "id": "FIX-0017",
        "type": "fix",
        "title": "Test ID Refs",
        "parent": "EPIC-0000",
    }
    meta = IssueMetadata(**meta_data)

    content = textwrap.dedent(
        """\
        ---
        id: FIX-0017
        type: fix
        title: Test ID Refs
        parent: EPIC-0000
        ---

        ## FIX-0017: Test ID Refs

        这里引用了一个非法的 ID: FEAT-0001-1。
        还有一个合法的 ID: FEAT-0002。
    """
    )

    diagnostics = validator.validate(meta, content)

    # 查找关于非法 ID 格式的警告
    invalid_id_diags = [d for d in diagnostics if "Invalid ID Format" in d.message]
    assert len(invalid_id_diags) == 1
    assert "FEAT-0001-1" in invalid_id_diags[0].message
    assert invalid_id_diags[0].severity == DiagnosticSeverity.Warning


def test_issue_validator_valid_references_pass():
    """验证正文中的合法引用不会触发格式警告。"""
    validator = IssueValidator()

    meta_data = {
        "id": "FIX-0017",
        "type": "fix",
        "title": "Test ID Refs",
        "parent": "EPIC-0000",
    }
    meta = IssueMetadata(**meta_data)

    content = textwrap.dedent(
        """\
        ---
        id: FIX-0017
        type: fix
        title: Test ID Refs
        parent: EPIC-0000
        ---

        ## FIX-0017: Test ID Refs

        这里引用了合法的 ID: FEAT-0001, EPIC-1234, FIX-0001, CHORE-9999。
    """
    )

    diagnostics = validator.validate(meta, content)

    # 不应该有 Invalid ID Format 警告
    invalid_id_diags = [d for d in diagnostics if "Invalid ID Format" in d.message]
    assert len(invalid_id_diags) == 0
