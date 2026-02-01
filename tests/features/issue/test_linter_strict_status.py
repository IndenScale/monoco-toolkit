"""
Tests for FEAT-0144: Strict Status and Directory Consistency in Issue Linter
"""
import textwrap
import pytest
from monoco.features.issue import core
from monoco.features.issue.linter import check_integrity
from monoco.features.issue.models import IssueType
from monoco.features.issue.validator import IssueValidator


class TestStatusEnumValidation:
    """Test status enum validation (must be one of: open, closed, backlog)"""

    def test_linter_reports_invalid_status_done(self, issues_root):
        """验证 Linter 能发现非法状态 'done'（应为 'closed'）。"""
        # 创建 Issue 文件，手动设置 status 为 'done'
        issue_path = issues_root / "Features" / "open" / "FEAT-9999-invalid-status.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-9999
                type: feature
                status: done
                stage: done
                title: Invalid Status Test
                parent: EPIC-0001
                tags: ["#EPIC-0001", "#FEAT-9999"]
                ---

                ## FEAT-9999: Invalid Status Test

                - [x] Task
            """
            )
        )

        diagnostics = check_integrity(issues_root)

        # Pydantic model rejects invalid status during parsing, reported as Schema Error
        status_errors = [d for d in diagnostics if "Schema Error" in d.message and "status" in d.message]
        assert len(status_errors) >= 1
        assert "Input should be" in status_errors[0].message

    def test_linter_reports_invalid_status_freezed(self, issues_root):
        """验证 Linter 能发现非法状态 'freezed'（应为 'backlog'）。"""
        issue_path = issues_root / "Features" / "open" / "FEAT-9998-invalid-status.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-9998
                type: feature
                status: freezed
                stage: freezed
                title: Invalid Status Freezed
                parent: EPIC-0001
                tags: ["#EPIC-0001", "#FEAT-9998"]
                ---

                ## FEAT-9998: Invalid Status Freezed

                - [ ] Task
            """
            )
        )

        diagnostics = check_integrity(issues_root)

        # Pydantic model rejects invalid status during parsing, reported as Schema Error
        status_errors = [d for d in diagnostics if "Schema Error" in d.message and "status" in d.message]
        assert len(status_errors) >= 1
        assert "Input should be" in status_errors[0].message

    def test_linter_accepts_valid_statuses(self, issues_root):
        """验证 Linter 接受有效的状态值。"""
        # Create valid issues with different valid statuses
        for status in ["open", "closed", "backlog"]:
            issue_id = f"FEAT-{9000 + ['open', 'closed', 'backlog'].index(status)}"
            issue_path = issues_root / "Features" / status / f"{issue_id}-valid-status.md"
            if status != "open":
                # For non-open, we need to create the directory
                issue_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                issue_path.parent.mkdir(parents=True, exist_ok=True)
            
            stage = "done" if status == "closed" else ("freezed" if status == "backlog" else "draft")
            solution = "implemented" if status == "closed" else None
            
            content = textwrap.dedent(
                f"""\
                ---
                id: {issue_id}
                type: feature
                status: {status}
                stage: {stage}
                title: Valid Status {status}
                parent: EPIC-0001
                tags: ["#EPIC-0001", "#{issue_id}"]
                {"solution: implemented" if solution else ""}
                ---

                ## {issue_id}: Valid Status {status}

                - [{"x" if status == "closed" else " "}] Task
            """
            )
            issue_path.write_text(content)

        diagnostics = check_integrity(issues_root)

        # Should not have Invalid Status errors
        status_errors = [d for d in diagnostics if "Invalid Status" in d.message]
        assert len(status_errors) == 0


class TestStageEnumValidation:
    """Test stage enum validation (must be one of: draft, doing, review, done, freezed)"""

    def test_linter_reports_invalid_stage(self, issues_root):
        """验证 Linter 能发现非法 stage 值。"""
        issue_path = issues_root / "Features" / "open" / "FEAT-9997-invalid-stage.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-9997
                type: feature
                status: open
                stage: invalid_stage
                title: Invalid Stage Test
                parent: EPIC-0001
                tags: ["#EPIC-0001", "#FEAT-9997"]
                ---

                ## FEAT-9997: Invalid Stage Test

                - [ ] Task
            """
            )
        )

        diagnostics = check_integrity(issues_root)

        # Pydantic model rejects invalid stage during parsing, reported as Schema Error
        stage_errors = [d for d in diagnostics if "Schema Error" in d.message and "stage" in d.message]
        assert len(stage_errors) >= 1
        assert "Input should be" in stage_errors[0].message

    def test_linter_accepts_valid_stages(self, issues_root):
        """验证 Linter 接受有效的 stage 值。"""
        valid_stages = ["draft", "doing", "review", "done", "freezed"]
        
        for stage in valid_stages:
            issue_id = f"FEAT-{8000 + valid_stages.index(stage)}"
            issue_path = issues_root / "Features" / "open" / f"{issue_id}-valid-stage.md"
            issue_path.parent.mkdir(parents=True, exist_ok=True)
            
            # For review/done stages, we need Review Comments section
            review_section = "\n## Review Comments\n\n- [x] Reviewed\n" if stage in ["review", "done"] else ""
            
            content = textwrap.dedent(
                f"""\
                ---
                id: {issue_id}
                type: feature
                status: open
                stage: {stage}
                title: Valid Stage {stage}
                parent: EPIC-0001
                tags: ["#EPIC-0001", "#{issue_id}"]
                ---

                ## {issue_id}: Valid Stage {stage}

                - [{"x" if stage in ["done", "review"] else " "}] Task
                {review_section}
            """
            )
            issue_path.write_text(content)

        diagnostics = check_integrity(issues_root)

        # Should not have Invalid Stage errors
        stage_errors = [d for d in diagnostics if "Invalid Stage" in d.message]
        assert len(stage_errors) == 0


class TestDirectoryStatusConsistency:
    """Test directory <-> status consistency validation"""

    def test_linter_reports_status_directory_mismatch(self, issues_root):
        """验证 Linter 能发现 status 与目录不一致。"""
        # Create an issue with status='closed' but put it in 'open/' directory
        issue_path = issues_root / "Features" / "open" / "FEAT-9996-mismatch.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-9996
                type: feature
                status: closed
                stage: done
                title: Status Directory Mismatch
                parent: EPIC-0001
                solution: implemented
                tags: ["#EPIC-0001", "#FEAT-9996"]
                ---

                ## FEAT-9996: Status Directory Mismatch

                - [x] Task

                ## Review Comments

                - [x] Reviewed
            """
            )
        )

        diagnostics = check_integrity(issues_root)

        mismatch_errors = [d for d in diagnostics if "Status/Directory Mismatch" in d.message]
        assert len(mismatch_errors) >= 1
        assert "status 'closed'" in mismatch_errors[0].message
        assert "is in 'open/' directory" in mismatch_errors[0].message

    def test_linter_reports_open_in_closed_directory(self, issues_root):
        """验证 Linter 能发现 open status 放在 closed 目录中。"""
        issue_path = issues_root / "Features" / "closed" / "FEAT-9995-open-in-closed.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-9995
                type: feature
                status: open
                stage: draft
                title: Open in Closed Directory
                parent: EPIC-0001
                tags: ["#EPIC-0001", "#FEAT-9995"]
                ---

                ## FEAT-9995: Open in Closed Directory

                - [ ] Task
            """
            )
        )

        diagnostics = check_integrity(issues_root)

        mismatch_errors = [d for d in diagnostics if "Status/Directory Mismatch" in d.message]
        assert len(mismatch_errors) >= 1
        assert "status 'open'" in mismatch_errors[0].message
        assert "is in 'closed/' directory" in mismatch_errors[0].message


class TestIllegalDirectoryNames:
    """Test illegal directory name detection"""

    def test_linter_reports_illegal_done_directory(self, issues_root):
        """验证 Linter 能发现非法的 'done/' 目录。"""
        # Create a 'done' directory (which is illegal)
        done_dir = issues_root / "Features" / "done"
        done_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy file in the illegal directory
        issue_path = done_dir / "FEAT-9994-in-done.md"
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-9994
                type: feature
                status: closed
                stage: done
                title: In Done Directory
                parent: EPIC-0001
                solution: implemented
                tags: ["#EPIC-0001", "#FEAT-9994"]
                ---

                ## FEAT-9994: In Done Directory

                - [x] Task

                ## Review Comments

                - [x] Reviewed
            """
            )
        )

        diagnostics = check_integrity(issues_root)

        illegal_errors = [d for d in diagnostics if "Illegal Directory" in d.message]
        assert len(illegal_errors) >= 1
        assert "'done/' directory" in illegal_errors[0].message

    def test_linter_reports_illegal_freezed_directory(self, issues_root):
        """验证 Linter 能发现非法的 'freezed/' 目录。"""
        # Create a 'freezed' directory (which is illegal)
        freezed_dir = issues_root / "Features" / "freezed"
        freezed_dir.mkdir(parents=True, exist_ok=True)
        
        issue_path = freezed_dir / "FEAT-9993-in-freezed.md"
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-9993
                type: feature
                status: backlog
                stage: freezed
                title: In Freezed Directory
                parent: EPIC-0001
                tags: ["#EPIC-0001", "#FEAT-9993"]
                ---

                ## FEAT-9993: In Freezed Directory

                - [ ] Task
            """
            )
        )

        diagnostics = check_integrity(issues_root)

        illegal_errors = [d for d in diagnostics if "Illegal Directory" in d.message]
        assert len(illegal_errors) >= 1
        assert "'freezed/' directory" in illegal_errors[0].message


class TestValidatorDirect:
    """Direct tests for IssueValidator"""

    def test_pydantic_rejects_invalid_status(self):
        """验证 Pydantic 模型在构造时拒绝无效的 status。"""
        from monoco.features.issue.models import IssueMetadata, IssueType
        import pydantic
        
        # Pydantic should reject invalid status at construction time
        with pytest.raises(pydantic.ValidationError) as exc_info:
            IssueMetadata(
                id="FEAT-1000",
                type=IssueType.FEATURE,
                status="done",  # Invalid status
                stage="done",
                title="Test",
                parent="EPIC-0001"
            )
        
        assert "status" in str(exc_info.value)
        assert "Input should be" in str(exc_info.value)

    def test_pydantic_rejects_invalid_stage(self):
        """验证 Pydantic 模型在构造时拒绝无效的 stage。"""
        from monoco.features.issue.models import IssueMetadata, IssueType
        import pydantic
        
        # Pydantic should reject invalid stage at construction time
        with pytest.raises(pydantic.ValidationError) as exc_info:
            IssueMetadata(
                id="FEAT-1001",
                type=IssueType.FEATURE,
                status="open",
                stage="invalid_stage",  # Invalid stage
                title="Test",
                parent="EPIC-0001"
            )
        
        assert "stage" in str(exc_info.value)
        assert "Input should be" in str(exc_info.value)

    def test_validator_accepts_valid_enum_values(self):
        """测试 validator 接受有效的 status 和 stage 枚举值。"""
        from monoco.features.issue.models import IssueMetadata, IssueType, IssueStatus, IssueStage
        
        validator = IssueValidator()
        
        meta = IssueMetadata(
            id="FEAT-1002",
            type=IssueType.FEATURE,
            status=IssueStatus.OPEN,
            stage=IssueStage.DRAFT,
            title="Test",
            parent="EPIC-0001"
        )
        
        content = "---\nstatus: open\nstage: draft\n---\n"
        status_diagnostics = validator._validate_status_enum(meta, content)
        stage_diagnostics = validator._validate_stage_enum(meta, content)
        
        assert len(status_diagnostics) == 0
        assert len(stage_diagnostics) == 0
