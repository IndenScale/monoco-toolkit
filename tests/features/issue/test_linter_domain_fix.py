import textwrap
from monoco.features.issue import core
from monoco.features.issue.linter import check_integrity
from monoco.features.issue.models import IssueType


def test_linter_detects_domain_format_error(issues_root):
    """验证 Linter 能发现 Domain 格式错误（非 PascalCase）。"""
    # 1. 创建 Domain 定义文件
    domain_dir = issues_root / "Domains"
    domain_dir.mkdir(parents=True, exist_ok=True)
    guardrail_file = domain_dir / "Guardrail.md"
    guardrail_file.write_text("# Guardrail")

    # 2. 创建一个带有错误格式 Domain 的 Issue
    # 注意：core.create_issue_file 可能会在内部进行一些转义，
    # 我们直接手动写文件以确保触发 Linter 报错。
    issue_dir = issues_root / "Fixes" / "open"
    issue_dir.mkdir(parents=True, exist_ok=True)
    issue_path = issue_dir / "FIX-0001-test-domain.md"
    issue_path.write_text(
        textwrap.dedent(
            """\
        ---
        id: FIX-0001
        type: fix
        status: open
        stage: draft
        title: Test Domain
        parent: EPIC-0001
        domains:
        - "Guardrail"
        - "Issue Tracing"
        tags: ["#EPIC-0001", "#FIX-0001"]
        ---

        ## FIX-0001: Test Domain

        - [ ] Task 1
        - [ ] Task 2
    """
        )
    )

    # 3. 运行 Linter (不带 fix)
    diagnostics = check_integrity(issues_root)

    # 4. 验证格式错误
    format_errors = [d for d in diagnostics if "Domain Format Error" in d.message]
    # "Guardrail" (带引号) 和 "Issue Tracing" (带空格) 都应该是错的
    assert len(format_errors) >= 1
    assert any("must be PascalCase" in d.message for d in format_errors)


def test_linter_fix_domain_format(issues_root):
    """验证 Linter --fix 能修复 Domain 格式。"""
    # 1. 创建 Domain 定义文件 和必要的 Epic
    domain_dir = issues_root / "Domains"
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / "Guardrail.md").write_text("# Guardrail")
    (domain_dir / "IssueTracing.md").write_text("# IssueTracing")

    # 创建 Parent Epic 以避免 Broken Reference 报错
    core.create_issue_file(issues_root, IssueType.EPIC, "Root Epic")

    # 2. 创建错误格式的 Issue
    issue_path = issues_root / "Fixes" / "open" / "FIX-0001-test-fix.md"
    issue_path.parent.mkdir(parents=True, exist_ok=True)
    issue_path.write_text(
        textwrap.dedent(
            """\
        ---
        id: FIX-0001
        type: fix
        status: open
        stage: draft
        title: Test Fix
        parent: EPIC-0001
        domains:
        - "Guardrail"
        - "Issue Tracing"
        tags: ["#EPIC-0001", "#FIX-0001"]
        ---

        ## FIX-0001: Test Fix

        - [ ] Task
        - [ ] Task
    """
        )
    )

    # 3. 运行 run_lint 带 fix=True
    from monoco.features.issue.linter import run_lint
    import typer

    try:
        run_lint(issues_root, fix=True)
    except (typer.Exit, SystemExit):
        pass

    # 4. 验证文件内容已更新
    content = issue_path.read_text()
    assert "- Guardrail" in content
    assert "- IssueTracing" in content
    assert '"Guardrail"' not in content
    assert '"Issue Tracing"' not in content
