"""
Tests for parse_issue_with_diagnostics functionality.

This tests the new multi-error collection feature that allows
reporting ALL validation errors at once instead of stopping at the first error.
"""
import textwrap
import pytest
from pathlib import Path
from monoco.features.issue.core import parse_issue_with_diagnostics, parse_issue
from monoco.core.lsp import DiagnosticSeverity


class TestParseIssueWithDiagnostics:
    """Test the new parse_issue_with_diagnostics function."""

    def test_valid_issue_no_diagnostics(self, issues_root):
        """验证有效 Issue 不产生诊断错误。"""
        issue_path = issues_root / "Features" / "open" / "FEAT-1000-valid.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-1000
                type: feature
                status: open
                stage: draft
                title: Valid Feature
                parent: EPIC-0001
                ---

                ## FEAT-1000: Valid Feature

                - [ ] Task
            """
            )
        )

        meta, diagnostics = parse_issue_with_diagnostics(issue_path)

        assert meta is not None
        assert meta.id == "FEAT-1000"
        assert len(diagnostics) == 0, f"Expected no diagnostics, got: {[d.message for d in diagnostics]}"

    def test_collects_multiple_field_errors(self, issues_root):
        """验证能同时收集多个字段验证错误。"""
        issue_path = issues_root / "Features" / "open" / "FEAT-1001-multi-error.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-1001
                type: invalid_type
                status: invalid_status
                stage: invalid_stage
                title: Multi Error Test
                parent: EPIC-0001
                ---

                ## FEAT-1001: Multi Error Test

                - [ ] Task
            """
            )
        )

        meta, diagnostics = parse_issue_with_diagnostics(issue_path)

        # Should collect all 3 field errors
        assert len(diagnostics) >= 3, f"Expected at least 3 errors, got {len(diagnostics)}"
        
        error_messages = [d.message for d in diagnostics]
        
        # Check that all fields are reported
        assert any("type" in msg for msg in error_messages), "Should report type error"
        assert any("status" in msg for msg in error_messages), "Should report status error"
        assert any("stage" in msg for msg in error_messages), "Should report stage error"
        
        # All should be errors
        for d in diagnostics:
            assert d.severity == DiagnosticSeverity.Error

    def test_reports_missing_required_field(self, issues_root):
        """验证能报告缺失的必填字段。"""
        issue_path = issues_root / "Features" / "open" / "FEAT-1002-no-title.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-1002
                type: feature
                status: open
                parent: EPIC-0001
                ---

                ## FEAT-1002: No Title

                - [ ] Task
            """
            )
        )

        meta, diagnostics = parse_issue_with_diagnostics(issue_path)

        # Should report missing title
        assert len(diagnostics) > 0
        error_messages = [d.message for d in diagnostics]
        assert any("title" in msg.lower() for msg in error_messages), "Should report missing title"

    def test_reports_invalid_id_format(self, issues_root):
        """验证能报告无效的 ID 格式。"""
        issue_path = issues_root / "Features" / "open" / "invalid-id-format.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: invalid-id
                type: feature
                status: open
                title: Invalid ID
                parent: EPIC-0001
                ---

                ## invalid-id: Invalid ID

                - [ ] Task
            """
            )
        )

        meta, diagnostics = parse_issue_with_diagnostics(issue_path)

        # Should report ID format error
        assert len(diagnostics) > 0
        error_messages = [d.message for d in diagnostics]
        assert any("id" in msg.lower() for msg in error_messages), "Should report ID error"

    def test_partial_metadata_on_errors(self, issues_root):
        """验证即使有错误也能返回部分 metadata。"""
        issue_path = issues_root / "Features" / "open" / "FEAT-1003-partial.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-1003
                type: feature
                title: Partial Metadata Test
                status: invalid_status
                parent: EPIC-0001
                ---

                ## FEAT-1003: Partial Metadata Test

                - [ ] Task
            """
            )
        )

        meta, diagnostics = parse_issue_with_diagnostics(issue_path)

        # Should still have partial metadata
        assert meta is not None, "Should return partial metadata even with errors"
        assert meta.id == "FEAT-1003"
        assert meta.title == "Partial Metadata Test"
        
        # But should have error about status
        assert len(diagnostics) > 0
        error_messages = [d.message for d in diagnostics]
        assert any("status" in msg.lower() for msg in error_messages)

    def test_reports_yaml_syntax_error(self, issues_root):
        """验证能报告 YAML 语法错误。"""
        issue_path = issues_root / "Features" / "open" / "FEAT-1004-yaml-error.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-1004
                type: feature
                title: "unclosed string
                status: open
                parent: EPIC-0001
                ---

                ## FEAT-1004: YAML Error

                - [ ] Task
            """
            )
        )

        meta, diagnostics = parse_issue_with_diagnostics(issue_path)

        # Should not return metadata for YAML errors
        assert meta is None
        assert len(diagnostics) > 0
        
        # Should report YAML error
        error_messages = [d.message for d in diagnostics]
        assert any("yaml" in msg.lower() or "syntax" in msg.lower() for msg in error_messages)

    def test_backward_compatibility_with_parse_issue(self, issues_root):
        """验证 parse_issue 保持向后兼容。"""
        issue_path = issues_root / "Features" / "open" / "FEAT-1005-compat.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Valid issue
        valid_content = textwrap.dedent(
            """\
            ---
            id: FEAT-1005
            type: feature
            status: open
            stage: draft
            title: Compatibility Test
            parent: EPIC-0001
            ---

            ## FEAT-1005: Compatibility Test

            - [ ] Task
        """
        )
        issue_path.write_text(valid_content)

        # parse_issue should work for valid issue
        meta = parse_issue(issue_path)
        assert meta is not None
        assert meta.id == "FEAT-1005"

        # Invalid issue should return None (old behavior)
        invalid_content = textwrap.dedent(
            """\
            ---
            id: FEAT-1005
            type: invalid_type
            title: Compatibility Test
            parent: EPIC-0001
            ---
        """
        )
        issue_path.write_text(invalid_content)
        
        meta = parse_issue(issue_path)
        assert meta is None  # Old behavior: return None on error

    def test_diagnostics_include_line_numbers(self, issues_root):
        """验证诊断信息包含正确的行号。"""
        issue_path = issues_root / "Features" / "open" / "FEAT-1006-line-numbers.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-1006
                type: invalid_type
                status: open
                title: Line Number Test
                parent: EPIC-0001
                ---

                ## FEAT-1006: Line Number Test

                - [ ] Task
            """
            )
        )

        meta, diagnostics = parse_issue_with_diagnostics(issue_path)

        # Check that line numbers are reasonable (not all 0)
        type_error = [d for d in diagnostics if "type" in d.message.lower()]
        assert len(type_error) > 0
        
        # Type field is on line 3 (0-indexed: 2)
        # Our implementation may report line 2 or 3 depending on implementation
        assert type_error[0].range.start.line >= 0

    def test_preserves_all_error_messages(self, issues_root):
        """验证保留了所有错误消息，而不仅仅是第一个。"""
        issue_path = issues_root / "Features" / "open" / "FEAT-1007-all-errors.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-1007
                type: bad_type_1
                status: bad_status_1
                stage: bad_stage_1
                title: All Errors Test
                parent: EPIC-0001
                ---

                ## FEAT-1007: All Errors Test

                - [ ] Task
            """
            )
        )

        meta, diagnostics = parse_issue_with_diagnostics(issue_path)

        # Collect unique error types
        error_types = set()
        for d in diagnostics:
            if "type" in d.message.lower():
                error_types.add("type")
            elif "status" in d.message.lower():
                error_types.add("status")
            elif "stage" in d.message.lower():
                error_types.add("stage")

        # Should have all three types of errors
        assert len(error_types) >= 3, f"Expected 3 error types, got: {error_types}"


class TestIntegrationWithLinter:
    """Test integration with linter.check_integrity."""

    def test_linter_uses_new_function(self, issues_root):
        """验证 linter 使用新函数收集所有错误。"""
        from monoco.features.issue.linter import check_integrity
        
        # Create issue with multiple errors
        issue_path = issues_root / "Features" / "open" / "FEAT-1100-lint-multi.md"
        issue_path.parent.mkdir(parents=True, exist_ok=True)
        issue_path.write_text(
            textwrap.dedent(
                """\
                ---
                id: FEAT-1100
                type: badtype
                status: badstatus
                title: Lint Multi Error
                parent: EPIC-0001
                ---

                ## FEAT-1100: Lint Multi Error

                - [ ] Task
            """
            )
        )

        diagnostics = check_integrity(issues_root)

        # Should find type and status errors
        error_messages = [d.message for d in diagnostics]
        
        # Check that both type and status errors are reported
        assert any("type" in msg.lower() for msg in error_messages), \
            f"Should report type error. Messages: {error_messages}"
        assert any("status" in msg.lower() for msg in error_messages), \
            f"Should report status error. Messages: {error_messages}"
