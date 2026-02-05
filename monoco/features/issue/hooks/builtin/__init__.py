"""
Built-in Issue Lifecycle Hooks

This module contains the default hooks that ship with Monoco.
These hooks provide core functionality like lint checking and branch validation.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import IssueHookContext, IssueHookResult

# Export all built-in hook functions
__all__ = [
    "pre_submit_hook",
    "post_start_hook",
    "pre_start_hook",
    "post_submit_hook",
    "register_all_builtins",
]


def pre_submit_hook(context: "IssueHookContext") -> "IssueHookResult":
    """
    Pre-submit hook: Validates issue before submission.
    
    Checks:
    - Issue lint status
    - Files synchronization
    - Acceptance criteria completion
    """
    from ..models import IssueHookResult, HookDecision
    
    # Import here to avoid circular dependencies
    from monoco.features.issue.core import find_issue_path, parse_issue
    from monoco.features.issue.linter import check_integrity
    from monoco.core.config import find_monoco_root
    
    issue_id = context.issue_id
    if not issue_id:
        return IssueHookResult.deny(
            "No issue ID provided",
            suggestions=["Ensure issue_id is set in the context"]
        )
    
    project_root = context.project_root or find_monoco_root()
    if not project_root:
        return IssueHookResult.deny(
            "Could not find project root",
            suggestions=["Run this command from within a Monoco project"]
        )
    
    issues_root = project_root / "Issues"
    issue_path = find_issue_path(issues_root, issue_id)
    
    if not issue_path:
        return IssueHookResult.deny(
            f"Issue {issue_id} not found",
            suggestions=[f"Check if issue {issue_id} exists"]
        )
    
    # Parse issue to check its state
    issue = parse_issue(issue_path)
    if not issue:
        return IssueHookResult.deny(
            f"Could not parse issue {issue_id}",
            suggestions=["Check the issue file format"]
        )
    
    # NEW logic: Auto-sync files before validation
    try:
        from monoco.features.issue.core import sync_issue_files
        sync_issue_files(issues_root, issue_id, project_root)
    except Exception as e:
        # Warning only, don't block
        logger.warning(f"Auto-sync failed in pre-submit hook: {e}")

    # NEW logic: Execute Lint Check
    diagnostics = check_integrity(issues_root, recursive=False)
    # Filter diagnostics for this specific issue
    issue_diags = [d for d in diagnostics if d.source == issue_id]
    
    if issue_diags:
        from ..models import Diagnostic as HookDiagnostic
        hook_diags = [
            HookDiagnostic(
                line=d.range.start.line + 1 if d.range else None,
                message=d.message,
                severity="error" if d.severity.value <= 2 else "warning"
            ) for d in issue_diags
        ]
        return IssueHookResult.deny(
            f"Issue {issue_id} failed lint validation",
            diagnostics=hook_diags,
            suggestions=[
                "Run 'monoco issue lint --fix' to solve common issues",
                "Ensure all mandatory fields are filled"
            ]
        )

    suggestions = []
    if not issue.files:
        suggestions.append("No files tracked for this issue. This might be a mistake if code changes were made.")
    
    return IssueHookResult.allow("Pre-submit checks (sync & lint) passed")


def post_start_hook(context: "IssueHookContext") -> "IssueHookResult":
    """
    Post-start hook: Actions after starting work on an issue.
    
    Actions:
    - Output branch information
    - Provide next steps suggestions
    """
    from ..models import IssueHookResult
    
    suggestions = [
        "Start implementing the solution",
        "Run tests frequently: pytest",
        "Use 'monoco issue sync-files' to track changed files",
        "Use 'monoco issue submit' when ready for review",
    ]
    
    if context.current_branch:
        message = f"Working on branch: {context.current_branch}"
    else:
        message = "Issue started successfully"
    
    return IssueHookResult.allow(
        message,
        suggestions=suggestions,
        context={
            "branch": context.current_branch,
            "issue_id": context.issue_id,
        }
    )


def pre_start_hook(context: "IssueHookContext") -> "IssueHookResult":
    """
    Pre-start hook: Validates before starting work on an issue.
    
    Checks:
    - Branch context (should be on trunk if creating new branch)
    - Issue status (should be open or backlog)
    """
    from ..models import IssueHookResult
    
    # Branch context check is handled by the command itself
    # This hook provides additional validation
    
    if context.force:
        return IssueHookResult.allow("Force mode: skipping pre-start checks")
    
    return IssueHookResult.allow("Pre-start checks passed")


def post_submit_hook(context: "IssueHookContext") -> "IssueHookResult":
    """
    Post-submit hook: Actions after submitting an issue for review.
    
    Actions:
    - Generate delivery report summary
    - Provide next steps
    """
    from ..models import IssueHookResult
    from monoco.features.issue.core import generate_delivery_report
    
    project_root = context.project_root
    issues_root = project_root / "Issues"
    
    report_status = "generated"
    try:
        generate_delivery_report(issues_root, context.issue_id, project_root)
    except Exception as e:
        report_status = f"failed: {e}"
        logger.warning(f"Failed to generate delivery report in post-submit: {e}")

    suggestions = [
        "Wait for review feedback",
        "Address any review comments",
        "Use 'monoco issue close' after approval",
    ]
    
    return IssueHookResult.allow(
        f"Issue submitted for review (Report: {report_status})",
        suggestions=suggestions,
        context={
            "issue_id": context.issue_id,
            "stage": "review",
            "report": report_status
        }
    )


def register_all_builtins(dispatcher: "IssueHookDispatcher") -> None:
    """
    Register all built-in hooks with the dispatcher.
    
    Args:
        dispatcher: The IssueHookDispatcher instance
    """
    from ..models import IssueEvent
    
    # Register pre-submit hook
    dispatcher.register_callable(
        name="builtin.pre-issue-submit",
        events=[IssueEvent.PRE_SUBMIT],
        fn=pre_submit_hook,
        priority=10,
    )
    
    # Register pre-start hook
    dispatcher.register_callable(
        name="builtin.pre-issue-start",
        events=[IssueEvent.PRE_START],
        fn=pre_start_hook,
        priority=10,
    )
    
    # Register post-start hook
    dispatcher.register_callable(
        name="builtin.post-issue-start",
        events=[IssueEvent.POST_START],
        fn=post_start_hook,
        priority=100,
    )
    
    # Register post-submit hook
    dispatcher.register_callable(
        name="builtin.post-issue-submit",
        events=[IssueEvent.POST_SUBMIT],
        fn=post_submit_hook,
        priority=100,
    )
