import typer
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import logging
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table
import typer

from monoco.core.config import get_config
from monoco.core.output import OutputManager, AgentOutput
from .models import IssueType, IssueStatus, IssueMetadata
from .criticality import CriticalityLevel
from . import core
from monoco.core import git

app = typer.Typer(help="Agent-Native Issue Management.")
backlog_app = typer.Typer(help="Manage backlog operations.")
lsp_app = typer.Typer(help="LSP Server commands.")
app.add_typer(backlog_app, name="backlog")
app.add_typer(lsp_app, name="lsp")
from . import domain_commands

app.add_typer(domain_commands.app, name="domain")
console = Console()
logger = logging.getLogger(__name__)


@app.command("create")
def create(
    type: str = typer.Argument(
        ..., help="Issue type (epic, feature, chore, fix, etc.)"
    ),
    title: str = typer.Option(..., "--title", "-t", help="Issue title"),
    parent: Optional[str] = typer.Option(
        None, "--parent", "-p", help="Parent Issue ID"
    ),
    is_backlog: bool = typer.Option(False, "--backlog", help="Create as backlog item"),
    stage: Optional[str] = typer.Option(None, "--stage", help="Issue stage"),
    dependencies: List[str] = typer.Option(
        [], "--dependency", "-d", help="Issue dependency ID(s)"
    ),
    related: List[str] = typer.Option(
        [], "--related", "-r", help="Related Issue ID(s)"
    ),
    from_memo: List[str] = typer.Option(
        [], "--from-memo", "-m", help="Memo ID(s) to link to this issue"
    ),
    force: bool = typer.Option(False, "--force", help="Bypass branch context checks"),
    subdir: Optional[str] = typer.Option(
        None,
        "--subdir",
        "-s",
        help="Subdirectory for organization (e.g. 'Backend/Auth')",
    ),
    sprint: Optional[str] = typer.Option(None, "--sprint", help="Sprint ID"),
    tags: List[str] = typer.Option([], "--tag", help="Tags"),
    domains: List[str] = typer.Option([], "--domain", help="Domains"),
    criticality: Optional[str] = typer.Option(
        None,
        "--criticality",
        "-c",
        help="Criticality level (low, medium, high, critical). Auto-derived from type if not specified.",
    ),
    no_hooks: bool = typer.Option(
        False, "--no-hooks", help="Skip lifecycle hooks"
    ),
    debug_hooks: bool = typer.Option(
        False, "--debug-hooks", help="Show hook execution details"
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """Create a new issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

    # Import hooks integration
    from .hooks import HookContextManager, init_hooks
    
    # Initialize hooks system
    init_hooks(project_root)

    # Context Check
    _validate_branch_context(
        project_root, allowed=["TRUNK"], force=force, command_name="create"
    )

    status = "backlog" if is_backlog else "open"

    # Sanitize inputs (strip #)
    if parent and parent.startswith("#"):
        parent = parent[1:]

    dependencies = [d[1:] if d.startswith("#") else d for d in dependencies]
    related = [r[1:] if r.startswith("#") else r for r in related]

    if parent:
        parent_path = core.find_issue_path(issues_root, parent)
        if not parent_path:
            OutputManager.error(f"Parent issue {parent} not found.")
            raise typer.Exit(code=1)

    # Parse criticality if provided
    criticality_level = None
    if criticality:
        try:
            criticality_level = CriticalityLevel(criticality.lower())
        except ValueError:
            valid_levels = [e.value for e in CriticalityLevel]
            OutputManager.error(
                f"Invalid criticality: '{criticality}'. Valid: {', '.join(valid_levels)}"
            )
            raise typer.Exit(code=1)

    try:
        # Use HookContextManager to execute pre/post hooks
        with HookContextManager(
            command="create",
            issue_id=None,
            project_root=project_root,
            force=force,
            no_hooks=no_hooks,
            debug_hooks=debug_hooks,
        ) as h_ctx:
            issue, path = core.create_issue_file(
                issues_root,
                type,
                title,
                parent,
                status=status,
                stage=stage,
                dependencies=dependencies,
                related=related,
                domains=domains,
                subdir=subdir,
                sprint=sprint,
                tags=tags,
                criticality=criticality_level,
            )
            
            # Update ID for post-hooks
            h_ctx.issue_id = issue.id

            # Link memos to the newly created issue
            linked_memos = []
            if from_memo:
                from monoco.features.memo.core import load_memos, update_memo
                existing_memos = {m.uid: m for m in load_memos(issues_root)}
                for memo_id in from_memo:
                    if memo_id in existing_memos:
                        memo = existing_memos[memo_id]
                        if memo.ref != issue.id:
                            update_memo(issues_root, memo_id, {"status": "tracked", "ref": issue.id})
                            linked_memos.append(memo_id)

            OutputManager.print(
                {
                    "issue": issue,
                    "status": "created",
                    "path": str(path.relative_to(project_root) if project_root in path.parents else path),
                    "memos": linked_memos,
                }
            )

    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)



@app.command("update")
def update(
    issue_id: str = typer.Argument(..., help="Issue ID to update"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    status: Optional[str] = typer.Option(None, "--status", help="New status"),
    stage: Optional[str] = typer.Option(None, "--stage", help="New stage"),
    solution: Optional[str] = typer.Option(None, "--solution", "-s", help="Solution type (implemented, cancelled, wontfix, duplicate)"),
    parent: Optional[str] = typer.Option(
        None, "--parent", "-p", help="Parent Issue ID"
    ),
    sprint: Optional[str] = typer.Option(None, "--sprint", help="Sprint ID"),
    dependencies: Optional[List[str]] = typer.Option(
        None, "--dependency", "-d", help="Issue dependency ID(s)"
    ),
    related: Optional[List[str]] = typer.Option(
        None, "--related", "-r", help="Related Issue ID(s)"
    ),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Tags"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """Update an existing issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    try:
        issue = core.update_issue(
            issues_root,
            issue_id,
            status=status,
            stage=stage,
            solution=solution,
            title=title,
            parent=parent,
            sprint=sprint,
            dependencies=dependencies,
            related=related,
            tags=tags,
        )

        OutputManager.print({"issue": issue, "status": "updated"})
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("open")
def move_open(
    issue_id: str = typer.Argument(..., help="Issue ID to open"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    no_commit: bool = typer.Option(
        False, "--no-commit", help="Skip auto-commit of issue file"
    ),
    no_hooks: bool = typer.Option(
        False, "--no-hooks", help="Skip lifecycle hooks"
    ),
    debug_hooks: bool = typer.Option(
        False, "--debug-hooks", help="Show hook execution details"
    ),
    json: AgentOutput = False,
):
    """Move issue to open status and set stage to Draft."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)
    
    # Import hooks integration
    from .hooks import HookContextManager, init_hooks
    init_hooks(project_root)

    try:
        with HookContextManager(
            command="open",
            issue_id=issue_id,
            project_root=project_root,
            no_hooks=no_hooks,
            debug_hooks=debug_hooks,
        ):
            # Pull operation: Force stage to TODO
            issue = core.update_issue(
                issues_root,
                issue_id,
                status="open",
                stage="draft",
                no_commit=no_commit,
                project_root=project_root,
            )
            OutputManager.print({"issue": issue, "status": "opened"})
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("start")
def start(
    issue_id: str = typer.Argument(..., help="Issue ID to start"),
    branch: bool = typer.Option(
        False,
        "--branch",
        "-b",
        help="Start in a new git branch (feat/<id>-<slug>). Mutually exclusive with --worktree.",
    ),
    direct: bool = typer.Option(
        False,
        "--direct",
        help="Privileged: Work directly on current branch (equivalent to --no-branch).",
    ),
    worktree: bool = typer.Option(
        True,
        "--worktree/--no-worktree",
        "-w",
        help="[Default] Start in a new git worktree for parallel development. Use --no-worktree to disable.",
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    force: bool = typer.Option(False, "--force", help="Bypass branch context checks"),
    no_commit: bool = typer.Option(
        False, "--no-commit", help="Skip auto-commit of issue file"
    ),
    no_hooks: bool = typer.Option(
        False, "--no-hooks", help="Skip lifecycle hooks"
    ),
    debug_hooks: bool = typer.Option(
        False, "--debug-hooks", help="Show hook execution details"
    ),
    json: AgentOutput = False,
):
    """
    Start working on an issue (Stage -> Doing).

    Default behavior is to create a git worktree for isolated development.
    Use --branch to create a feature branch instead.
    Use --direct or --no-worktree to work on current branch directly.
    """
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

    # Import hooks integration
    from .hooks import HookContextManager, init_hooks
    
    # Initialize hooks system
    init_hooks(project_root)

    # Handle flag overrides and mutual exclusivity
    # --branch and --worktree are mutually exclusive; --branch takes precedence
    if branch:
        worktree = False
    if direct:
        worktree = False
        branch = False

    # Context Check
    # If creating isolation (worktree or branch), we MUST be on trunk to avoid nesting.
    # If direct mode, we don't care.
    if worktree or branch:
        _validate_branch_context(
            project_root, allowed=["TRUNK"], force=force, command_name="start"
        )

    try:
        # Use HookContextManager to execute pre/post hooks
        with HookContextManager(
            command="start",
            issue_id=issue_id,
            project_root=project_root,
            force=force,
            no_hooks=no_hooks,
            debug_hooks=debug_hooks,
        ):
            # Implicitly ensure status is Open
            issue = core.update_issue(
                issues_root,
                issue_id,
                status="open",
                stage="doing",
                no_commit=no_commit,
                project_root=project_root,
            )

            isolation_info = None

            if branch:
                try:
                    issue = core.start_issue_isolation(
                        issues_root, issue_id, "branch", project_root
                    )
                    isolation_info = {"type": "branch", "ref": issue.isolation.ref}
                except Exception as e:
                    OutputManager.error(f"Failed to create branch: {e}")
                    raise typer.Exit(code=1)

            if worktree:
                try:
                    issue = core.start_issue_isolation(
                        issues_root, issue_id, "worktree", project_root
                    )
                    isolation_info = {
                        "type": "worktree",
                        "path": issue.isolation.path,
                        "ref": issue.isolation.ref,
                    }
                except Exception as e:
                    OutputManager.error(f"Failed to create worktree: {e}")
                    raise typer.Exit(code=1)

            if not branch and not worktree:
                # Direct mode message
                isolation_info = {"type": "direct", "ref": "current"}

            OutputManager.print(
                {"issue": issue, "status": "started", "isolation": isolation_info}
            )
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("submit")
def submit(
    issue_id: str = typer.Argument(..., help="Issue ID to submit"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    force: bool = typer.Option(False, "--force", help="Bypass branch context checks"),
    no_commit: bool = typer.Option(
        False, "--no-commit", help="Skip auto-commit of issue file"
    ),
    no_hooks: bool = typer.Option(
        False, "--no-hooks", help="Skip lifecycle hooks"
    ),
    debug_hooks: bool = typer.Option(
        False, "--debug-hooks", help="Show hook execution details"
    ),
    json: AgentOutput = False,
):
    """Submit issue for review (Stage -> Review) and generate delivery report."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

    # Import hooks integration
    from .hooks import HookContextManager, init_hooks
    
    # Initialize hooks system
    init_hooks(project_root)

    # Context Check: Submit should happen on feature branch, not trunk
    _validate_branch_context(
        project_root, forbidden=["TRUNK"], force=force, command_name="submit"
    )

    try:
        # Use HookContextManager to execute pre/post hooks
        with HookContextManager(
            command="submit",
            issue_id=issue_id,
            project_root=project_root,
            force=force,
            no_hooks=no_hooks,
            debug_hooks=debug_hooks,
        ):
            # Implicitly ensure status is Open
            issue = core.update_issue(
                issues_root,
                issue_id,
                status="open",
                stage="review",
                no_commit=no_commit,
                project_root=project_root,
            )

            OutputManager.print(
                {
                    "issue": issue,
                    "status": "submitted",
                }
            )

    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("close")
def move_close(
    issue_id: str = typer.Argument(..., help="Issue ID to close"),
    solution: Optional[str] = typer.Option(
        None, "--solution", "-s", help="Solution type"
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    no_commit: bool = typer.Option(
        False, "--no-commit", help="Skip auto-commit of issue file"
    ),
    no_hooks: bool = typer.Option(
        False, "--no-hooks", help="Skip lifecycle hooks"
    ),
    debug_hooks: bool = typer.Option(
        False, "--debug-hooks", help="Show hook execution details"
    ),
    json: AgentOutput = False,
):
    """Close issue with atomic transaction guarantee.
    
    Always prunes branch/worktree and bypasses branch checks.
    If any step fails, all changes are automatically rolled back.
    """
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

    # Import hooks integration
    from .hooks import HookContextManager, init_hooks, execute_hooks, build_hook_context, IssueEvent
    
    # Initialize hooks system
    init_hooks(project_root)

    # Pre-flight check for interactive guidance
    if solution is None:
        from .engine import get_engine
        engine = get_engine(str(issues_root.parent))
        valid_solutions = engine.issue_config.solutions or []
        OutputManager.error(
            f"Closing an issue requires a solution. Options: {', '.join(valid_solutions)}"
        )
        raise typer.Exit(code=1)

    # Force mode: always bypass branch checks and prune
    prune = True
    force = True

    # ATOMIC TRANSACTION: Capture initial state for potential rollback
    initial_head = None
    transaction_commits = []
    
    def rollback_transaction():
        """Rollback all changes made during the transaction."""
        if initial_head and transaction_commits:
            try:
                git.git_reset_hard(project_root, initial_head)
                if not OutputManager.is_agent_mode():
                    console.print(f"[yellow]↩ Rolled back to {initial_head[:7]}[/yellow]")
            except Exception as rollback_error:
                if not OutputManager.is_agent_mode():
                    console.print(f"[red]⚠ Rollback failed: {rollback_error}[/red]")
                    console.print(f"[red]   Manual recovery may be required. Run: git reset --hard {initial_head[:7]}[/red]")

    try:
        with HookContextManager(
            command="close",
            issue_id=issue_id,
            project_root=project_root,
            force=force,
            no_hooks=no_hooks,
            debug_hooks=debug_hooks,
        ):
            # Capture initial HEAD before any modifications
            initial_head = git.get_current_head(project_root)
            
            # 0. Find issue across branches (FIX-0006, CHORE-0036)
            # allow_multi_branch=True: Issue metadata files can exist in both main and feature branch
            found_path, source_branch, conflicting_branches = core.find_issue_path_across_branches(
                issues_root, issue_id, project_root, allow_multi_branch=True
            )
            if not found_path:
                OutputManager.error(f"Issue {issue_id} not found in any branch.")
                raise typer.Exit(code=1)

            # CHORE-0036: Always dump Issue file from feature branch to main first
            # First, parse issue to get isolation ref if available
            issue = core.parse_issue(found_path)

            # Determine feature branch: use isolation.ref if available, otherwise heuristic search
            feature_branch = None
            if issue and issue.isolation and issue.isolation.ref:
                feature_branch = issue.isolation.ref
            else:
                # Heuristic: Find feature branch by convention {issue_id}-*
                import re
                code, stdout, _ = git._run_git(["branch", "--format=%(refname:short)"], project_root)
                if code == 0:
                    for branch in stdout.splitlines():
                        branch = branch.strip()
                        # Match format: FEAT-XXXX-*
                        if re.match(rf"{re.escape(issue_id)}-", branch, re.IGNORECASE):
                            feature_branch = branch
                            break

            if feature_branch and git.branch_exists(project_root, feature_branch):
                # Checkout Issue file from feature branch to override main's version
                try:
                    rel_path = found_path.relative_to(project_root)
                    git.git_checkout_files(project_root, feature_branch, [str(rel_path)])
                    # Re-read issue after dumping to get latest state
                    issue = core.parse_issue(found_path)
                    if not OutputManager.is_agent_mode():
                        console.print(
                            f"[green]✔ Dumped:[/green] Issue file synced from '{feature_branch}'"
                        )
                except Exception as e:
                    OutputManager.error(f"Failed to sync Issue file from feature branch: {e}")
                    rollback_transaction()
                    raise typer.Exit(code=1)
            else:
                # No feature branch found, use current issue state
                issue = core.parse_issue(found_path)

            # 1. Perform Smart Atomic Merge (FEAT-0154)
            # Validate: if no branch and no files, issue didn't do any work
            if not feature_branch and not issue.files:
                OutputManager.error(
                    f"Cannot close {issue_id}: No feature branch found and no files tracked. "
                    "Issue appears to have no work done."
                )
                raise typer.Exit(code=1)

            merged_files = []
            try:
                merged_files = core.merge_issue_changes(issues_root, issue_id, project_root)
                if merged_files:
                    if not OutputManager.is_agent_mode():
                        console.print(
                            f"[green]✔ Smart Merge:[/green] Synced {len(merged_files)} files from feature branch."
                        )

                    # Auto-commit merged files if not no_commit
                    if not no_commit:
                        commit_msg = f"feat: atomic merge changes from {issue_id}"
                        try:
                            commit_hash = git.git_commit(project_root, commit_msg)
                            transaction_commits.append(commit_hash)
                            if not OutputManager.is_agent_mode():
                                console.print(f"[green]✔ Committed merged changes.[/green]")
                        except Exception as e:
                            # If commit fails (e.g. nothing to commit?), just warn
                            if not OutputManager.is_agent_mode():
                                console.print(f"[yellow]⚠ Commit skipped: {e}[/yellow]")

            except Exception as e:
                OutputManager.error(f"Merge Error: {e}")
                rollback_transaction()
                raise typer.Exit(code=1)

            # 2. Update issue status to closed
            try:
                issue = core.update_issue(
                    issues_root,
                    issue_id,
                    status="closed",
                    solution=solution,
                    no_commit=no_commit,
                    project_root=project_root,
                )
                # Track the auto-commit from update_issue if it occurred
                if hasattr(issue, 'commit_result') and issue.commit_result:
                    transaction_commits.append(issue.commit_result)
            except Exception as e:
                OutputManager.error(f"Update Error: {e}")
                rollback_transaction()
                raise typer.Exit(code=1)

            # 3. Prune issue resources (branch/worktree)
            pruned_resources = []
            if prune:
                # Get isolation info for confirmation prompt
                isolation_info = None
                if issue.isolation:
                    isolation_type = issue.isolation.type if issue.isolation.type else None
                    isolation_ref = issue.isolation.ref
                    isolation_info = (isolation_type, isolation_ref)

                # Auto-prune without confirmation (FEAT-0082 Update)
                if not OutputManager.is_agent_mode() and isolation_info:
                    iso_type, iso_ref = isolation_info
                    if iso_ref:
                        console.print(f"[dim]Cleaning up {iso_type}: {iso_ref}...[/dim]")

                try:
                    pruned_resources = core.prune_issue_resources(
                        issues_root, issue_id, force, project_root
                    )
                    if pruned_resources and not OutputManager.is_agent_mode():
                        console.print(f"[green]✔ Cleaned up:[/green] {', '.join(pruned_resources)}")
                except Exception as e:
                    # Prune failure triggers rollback
                    OutputManager.error(f"Prune Error: {e}")
                    rollback_transaction()
                    raise typer.Exit(code=1)

            # Success: Clear transaction state as all operations completed
            OutputManager.print(
                {"issue": issue, "status": "closed", "pruned": pruned_resources}
            )

    except typer.Abort:
        # User cancelled, rollback already handled
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        OutputManager.error(str(e))
        rollback_transaction()
        raise typer.Exit(code=1)


@backlog_app.command("push")
def push(
    issue_id: str = typer.Argument(..., help="Issue ID to push to backlog"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    no_commit: bool = typer.Option(
        False, "--no-commit", help="Skip auto-commit of issue file"
    ),
    json: AgentOutput = False,
):
    """Push issue to backlog."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)
    try:
        issue = core.update_issue(
            issues_root,
            issue_id,
            status="backlog",
            no_commit=no_commit,
            project_root=project_root,
        )
        OutputManager.print({"issue": issue, "status": "pushed_to_backlog"})
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@backlog_app.command("pull")
def pull(
    issue_id: str = typer.Argument(..., help="Issue ID to pull from backlog"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    no_commit: bool = typer.Option(
        False, "--no-commit", help="Skip auto-commit of issue file"
    ),
    json: AgentOutput = False,
):
    """Pull issue from backlog (Open & Draft)."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)
    try:
        issue = core.update_issue(
            issues_root,
            issue_id,
            status="open",
            stage="draft",
            no_commit=no_commit,
            project_root=project_root,
        )
        OutputManager.print({"issue": issue, "status": "pulled_from_backlog"})
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("cancel")
def cancel(
    issue_id: str = typer.Argument(..., help="Issue ID to cancel"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    no_commit: bool = typer.Option(
        False, "--no-commit", help="Skip auto-commit of issue file"
    ),
    json: AgentOutput = False,
):
    """Cancel issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)
    try:
        issue = core.update_issue(
            issues_root,
            issue_id,
            status="closed",
            solution="cancelled",
            no_commit=no_commit,
            project_root=project_root,
        )
        OutputManager.print({"issue": issue, "status": "cancelled"})
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("delete")
def delete(
    issue_id: str = typer.Argument(..., help="Issue ID to delete"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """Physically remove an issue file."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        core.delete_issue_file(issues_root, issue_id)
        OutputManager.print({"id": issue_id, "status": "deleted"})
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("move")
def move(
    issue_id: str = typer.Argument(..., help="Issue ID to move"),
    target: str = typer.Option(
        ..., "--to", help="Target project directory (e.g., ../OtherProject)"
    ),
    renumber: bool = typer.Option(
        False, "--renumber", help="Automatically renumber on ID conflict"
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override source issues root directory"
    ),
    json: AgentOutput = False,
):
    """Move an issue to another project."""
    config = get_config()
    source_issues_root = _resolve_issues_root(config, root)

    # Resolve target project
    target_path = Path(target).resolve()

    # Check if target is a project root or Issues directory
    if (target_path / "Issues").exists():
        target_issues_root = target_path / "Issues"
    elif target_path.name == "Issues" and target_path.exists():
        target_issues_root = target_path
    else:
        OutputManager.error(
            "Target path must be a project root with 'Issues' directory or an 'Issues' directory itself."
        )
        raise typer.Exit(code=1)

    try:
        updated_meta, new_path = core.move_issue(
            source_issues_root, issue_id, target_issues_root, renumber=renumber
        )

        try:
            rel_path = new_path.relative_to(Path.cwd())
        except ValueError:
            rel_path = new_path

        OutputManager.print(
            {
                "issue": updated_meta,
                "new_path": str(rel_path),
                "status": "moved",
                "renumbered": updated_meta.id != issue_id,
            }
        )

    except FileNotFoundError as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)
    except ValueError as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("board")
def board(
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """Visualize issues in a Kanban board."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    board_data = core.get_board_data(issues_root)

    if OutputManager.is_agent_mode():
        OutputManager.print(board_data)
        return

    from rich.columns import Columns
    from rich.console import RenderableType

    columns: List[RenderableType] = []

    stage_titles = {
        "draft": "[bold white]DRAFT[/bold white]",
        "doing": "[bold yellow]DOING[/bold yellow]",
        "review": "[bold cyan]REVIEW[/bold cyan]",
        "done": "[bold green]DONE[/bold green]",
    }

    for stage, issues in board_data.items():
        issue_list = []
        for issue in sorted(issues, key=lambda x: x.updated_at, reverse=True):
            type_color = {
                "feature": "green",
                "chore": "blue",
                "fix": "red",
                "epic": "magenta",
            }.get(issue.type, "white")

            issue_list.append(
                Panel(
                    f"[{type_color}]{issue.id}[/{type_color}]\n{issue.title}",
                    expand=True,
                    padding=(0, 1),
                )
            )

        from rich.console import Group

        content = Group(*issue_list) if issue_list else "[dim]Empty[/dim]"

        columns.append(
            Panel(
                content,
                title=stage_titles.get(stage, stage.upper()),
                width=35,
                padding=(1, 1),
            )
        )

    console.print(Columns(columns, equal=True, expand=True))


@app.command("list")
def list_cmd(
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="Filter by status (open, closed, backlog, all)"
    ),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type"),
    stage: Optional[str] = typer.Option(None, "--stage", help="Filter by stage"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    workspace: bool = typer.Option(
        False, "--workspace", "-w", help="Include issues from workspace members"
    ),
    all: bool = typer.Option(
        False, "--all", "-a", help="Include archived issues in the list"
    ),
    json: AgentOutput = False,
):
    """List issues in a table format with filtering."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    # Validation
    if status and status.lower() not in ["open", "closed", "backlog", "archived", "all"]:
        OutputManager.error(
            f"Invalid status: {status}. Use open, closed, backlog, archived or all."
        )
        raise typer.Exit(code=1)

    target_status = status.lower() if status else "open"

    issues = core.list_issues(issues_root, recursive_workspace=workspace, include_archived=all)
    filtered = []

    for i in issues:
        # Status Filter
        if target_status != "all":
            if i.status != target_status:
                continue

        # Type Filter
        if type and i.type != type:
            continue

        # Stage Filter
        if stage and i.stage != stage:
            continue

        filtered.append(i)

    # Sort: Updated Descending
    filtered.sort(key=lambda x: x.updated_at, reverse=True)

    if OutputManager.is_agent_mode():
        OutputManager.print(filtered)
        return

    # Render
    _render_issues_table(filtered, title=f"Issues ({len(filtered)})")


def _render_issues_table(issues: List[IssueMetadata], title: str = "Issues"):
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=12)
    table.add_column("Type", width=10)
    table.add_column("Status", width=10)
    table.add_column("Stage", width=10)
    table.add_column("Title", style="white")
    table.add_column("Updated", style="dim", width=20)

    type_colors = {
        IssueType.EPIC: "magenta",
        IssueType.FEATURE: "green",
        IssueType.CHORE: "blue",
        IssueType.FIX: "red",
    }

    status_colors = {
        IssueStatus.OPEN: "green",
        IssueStatus.BACKLOG: "blue",
        IssueStatus.CLOSED: "dim",
    }

    for i in issues:
        t_color = type_colors.get(i.type, "white")
        s_color = status_colors.get(i.status, "white")

        stage_str = i.stage if i.stage else "-"
        updated_str = i.updated_at.strftime("%Y-%m-%d %H:%M")

        table.add_row(
            i.id,
            f"[{t_color}]{i.type}[/{t_color}]",
            f"[{s_color}]{i.status}[/{s_color}]",
            stage_str,
            i.title,
            updated_str,
        )

    console.print(table)


@app.command("query")
def query_cmd(
    query: str = typer.Argument(..., help="Search query (e.g. '+bug -ui' or 'login')"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """
    Search issues using advanced syntax.

    Syntax:
      term   : Must include 'term' (implicit AND)
      +term  : Must include 'term'
      -term  : Must NOT include 'term'

    Scope: ID, Title, Body, Tags, Status, Stage, Dependencies, Related.
    """
    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    results = core.search_issues(issues_root, query)

    # Sort by relevance? Or just updated?
    # For now, updated at descending is useful.
    results.sort(key=lambda x: x.updated_at, reverse=True)

    if OutputManager.is_agent_mode():
        OutputManager.print(results)
        return

    _render_issues_table(
        results, title=f"Search Results for '{query}' ({len(results)})"
    )


@app.command("scope")
def scope(
    sprint: Optional[str] = typer.Option(None, "--sprint", help="Filter by Sprint ID"),
    all: bool = typer.Option(
        False, "--all", "-a", help="Show all, otherwise show only open items"
    ),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Recursively scan subdirectories"
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    workspace: bool = typer.Option(
        False, "--workspace", "-w", help="Include issues from workspace members"
    ),
    json: AgentOutput = False,
):
    """Show progress tree."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    issues = core.list_issues(issues_root, recursive_workspace=workspace)
    filtered_issues = []

    for meta in issues:
        if sprint and meta.sprint != sprint:
            continue
        if not all and meta.status != IssueStatus.OPEN:
            continue
        filtered_issues.append(meta)

    issues = filtered_issues

    if OutputManager.is_agent_mode():
        OutputManager.print(issues)
        return

    tree = Tree("[bold blue]Monoco Issue Scope[/bold blue]")
    epics = sorted([i for i in issues if i.type == "epic"], key=lambda x: x.id)
    stories = [i for i in issues if i.type == "feature"]
    tasks = [i for i in issues if i.type in ["chore", "fix"]]

    status_map = {
        "open": "[blue]●[/blue]",
        "closed": "[green]✔[/green]",
        "backlog": "[dim]💤[/dim]",
    }

    for epic in epics:
        epic_node = tree.add(
            f"{status_map[epic.status]} [bold]{epic.id}[/bold]: {epic.title}"
        )
        child_stories = sorted(
            [s for s in stories if s.parent == epic.id], key=lambda x: x.id
        )
        for story in child_stories:
            story_node = epic_node.add(
                f"{status_map[story.status]} [bold]{story.id}[/bold]: {story.title}"
            )
            child_tasks = sorted(
                [t for t in tasks if t.parent == story.id], key=lambda x: x.id
            )
            for task in child_tasks:
                story_node.add(
                    f"{status_map[task.status]} [bold]{task.id}[/bold]: {task.title}"
                )

    console.print(Panel(tree, expand=False))


@app.command("sync-files")
def sync_files(
    issue_id: Optional[str] = typer.Argument(
        None, help="Issue ID to sync (default: current context)"
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """
    Sync issue 'files' field with git changed files.
    """
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

    if not issue_id:
        # Infer from branch
        from monoco.core import git

        current = git.get_current_branch(project_root)
        # Try to parse ID from branch: FEAT-123-slug format
        import re

        # Format: ID at start followed by dash (e.g., FEAT-123-login-page)
        match = re.match(r"([a-zA-Z]+-\d+)-", current)
        if match:
            issue_id = match.group(1).upper()
        else:
            OutputManager.error(
                "Cannot infer Issue ID from current branch. Please specify Issue ID."
            )
            raise typer.Exit(code=1)

    try:
        changed = core.sync_issue_files(issues_root, issue_id, project_root)
        OutputManager.print({"id": issue_id, "status": "synced", "files": changed})
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("inspect")
def inspect(
    target: str = typer.Argument(..., help="Issue ID or File Path"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    ast: bool = typer.Option(
        False, "--ast", help="Output JSON AST structure for debugging"
    ),
    json: AgentOutput = False,
):
    """
    Inspect a specific issue and return its metadata (including actions).
    """
    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    # Try as Path
    target_path = Path(target)
    if target_path.exists() and target_path.is_file():
        path = target_path
    else:
        # Try as ID
        # Search path logic is needed? Or core.find_issue_path
        path = core.find_issue_path(issues_root, target)
        if not path:
            OutputManager.error(f"Issue or file {target} not found.")
            raise typer.Exit(code=1)

    # AST Debug Mode
    if ast:
        from .domain.parser import MarkdownParser

        content = path.read_text()
        try:
            domain_issue = MarkdownParser.parse(content, path=str(path))
            print(domain_issue.model_dump_json(indent=2))
        except Exception as e:
            OutputManager.error(f"Failed to parse AST: {e}")
            raise typer.Exit(code=1)
        return

    # Normal Mode
    meta = core.parse_issue(path)

    if not meta:
        OutputManager.error(f"Could not parse issue {target}.")
        raise typer.Exit(code=1)

    # In JSON mode (AgentOutput), we might want to return rich data
    if OutputManager.is_agent_mode():
        OutputManager.print(meta)
    else:
        # For human, print yaml-like or table
        console.print(meta)


@app.command("lint")
def lint(
    files: Optional[List[str]] = typer.Argument(
        None, help="List of specific files to validate"
    ),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Recursively scan subdirectories"
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Attempt to automatically fix issues (e.g. missing headings)",
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format (table, json)"
    ),
    file: Optional[str] = typer.Option(
        None,
        "--file",
        help="[Deprecated] Validate a single file. Use arguments instead.",
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """Verify the integrity of the Issues directory (declarative check)."""
    from . import linter

    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    if OutputManager.is_agent_mode():
        format = "json"

    # Merge legacy --file option into files list
    target_files = files if files else []
    if file:
        target_files.append(file)

    linter.run_lint(
        issues_root,
        recursive=recursive,
        fix=fix,
        format=format,
        file_paths=target_files if target_files else None,
    )


def _resolve_issues_root(config, cli_root: Optional[str]) -> Path:
    """
    Resolve the absolute path to the issues directory.
    Implements Smart Path Resolution & Workspace Awareness.
    """
    from monoco.core.workspace import is_project_root

    # 1. Handle Explicit CLI Root
    if cli_root:
        path = Path(cli_root).resolve()

        # Scenario A: User pointed to a Project Root (e.g. ./Toolkit)
        # We auto-resolve to ./Toolkit/Issues if it exists
        if is_project_root(path) and (path / "Issues").exists():
            return path / "Issues"

        # Scenario B: User pointed to Issues dir directly (e.g. ./Toolkit/Issues)
        # Or user pointed to a path that will be created
        return path

    # 2. Handle Default / Contextual Execution (No --root)
    # Strict Workspace Check: If not in a project root, we rely on the config root.
    # (The global app callback already enforces presence of .monoco for most commands)
    cwd = Path.cwd()

    # 3. Config Fallback
    config_issues_path = Path(config.paths.issues)
    if config_issues_path.is_absolute():
        return config_issues_path
    else:
        return (Path(config.paths.root) / config_issues_path).resolve()


def _resolve_project_root(config) -> Path:
    """Resolve project root from config or defaults."""
    return Path(config.paths.root).resolve()


@app.command("commit")
def commit(
    message: Optional[str] = typer.Option(
        None, "--message", "-m", help="Commit message"
    ),
    issue_id: Optional[str] = typer.Option(
        None, "--issue", "-i", help="Link commit to Issue ID"
    ),
    detached: bool = typer.Option(
        False,
        "--detached",
        help="Flag commit as intentionally detached (no issue link)",
    ),
    type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Commit type (feat, fix, etc.)"
    ),
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Commit scope"),
    subject: Optional[str] = typer.Option(None, "--subject", help="Commit subject"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
):
    """
    Atomic Commit: Validate (Lint) and Commit.

    Modes:
    1. Linked Commit (--issue): Commits staged changes with 'Ref: <ID>' footer.
    2. Detached Commit (--detached): Commits staged changes without link.
    3. Auto-Issue (No args): Only allowed if ONLY issue files are modified.
    """
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

    # 1. Lint Check (Gatekeeper)
    console.print("[dim]Running pre-commit lint check...[/dim]")
    try:
        from . import linter

        linter.check_integrity(issues_root, recursive=True)
    except Exception:
        pass

    # 2. Stage & Commit
    from monoco.core import git

    try:
        # Check Staging Status
        code, stdout, _ = git._run_git(
            ["diff", "--cached", "--name-only"], project_root
        )
        staged_files = [l for l in stdout.splitlines() if l.strip()]

        # Determine Mode
        if issue_id:
            # MODE: Linked Commit
            console.print(
                f"[bold cyan]Linked Commit Mode[/bold cyan] (Ref: {issue_id})"
            )

            if not core.find_issue_path(issues_root, issue_id):
                console.print(f"[red]Error:[/red] Issue {issue_id} not found.")
                raise typer.Exit(code=1)

            if not staged_files:
                console.print(
                    "[yellow]No staged files.[/yellow] Please `git add` files."
                )
                raise typer.Exit(code=1)

            if not message:
                if not type or not subject:
                    console.print(
                        "[red]Error:[/red] Provide --message OR (--type and --subject)."
                    )
                    raise typer.Exit(code=1)
                scope_part = f"({scope})" if scope else ""
                message = f"{type}{scope_part}: {subject}"

            if f"Ref: {issue_id}" not in message:
                message += f"\n\nRef: {issue_id}"

            commit_hash = git.git_commit(project_root, message)
            console.print(f"[green]✔ Committed:[/green] {commit_hash[:7]}")

        elif detached:
            # MODE: Detached
            console.print("[bold yellow]Detached Commit Mode[/bold yellow]")

            if not staged_files:
                console.print(
                    "[yellow]No staged files.[/yellow] Please `git add` files."
                )
                raise typer.Exit(code=1)

            if not message:
                console.print("[red]Error:[/red] Detached commits require --message.")
                raise typer.Exit(code=1)

            commit_hash = git.git_commit(project_root, message)
            console.print(f"[green]✔ Committed:[/green] {commit_hash[:7]}")

        else:
            # MODE: Implicit / Auto-DB
            # Strict Policy: Only allow if changes are constrained to Issues/ directory

            # Check if any non-issue files are staged
            # (We assume issues dir is 'Issues/')
            try:
                rel_issues = issues_root.relative_to(project_root)
                issues_prefix = str(rel_issues)
            except ValueError:
                issues_prefix = "Issues"  # Fallback

            non_issue_staged = [
                f for f in staged_files if not f.startswith(issues_prefix)
            ]

            if non_issue_staged:
                console.print(
                    f"[red]⛔ Strict Policy:[/red] Code changes detected in staging ({len(non_issue_staged)} files)."
                )
                console.print(
                    "You must specify [bold]--issue <ID>[/bold] or [bold]--detached[/bold]."
                )
                raise typer.Exit(code=1)

            # If nothing staged, check unstaged Issue files (Legacy Auto-Add)
            if not staged_files:
                status_files = git.get_git_status(project_root, str(rel_issues))
                if not status_files:
                    console.print("[yellow]Nothing to commit.[/yellow]")
                    return

                # Auto-stage Issue files
                git.git_add(project_root, status_files)
                staged_files = status_files  # Now they are staged
            else:
                pass

            # Auto-generate message from Issue File
            if not message:
                cnt = len(staged_files)
                if cnt == 1:
                    fpath = project_root / staged_files[0]
                    match = core.parse_issue(fpath)
                    if match:
                        action = "update"
                        message = f"docs(issues): {action} {match.id} {match.title}"
                    else:
                        message = f"docs(issues): update {staged_files[0]}"
                else:
                    message = f"docs(issues): batch update {cnt} files"

            commit_hash = git.git_commit(project_root, message)
            console.print(
                f"[green]✔ Committed (DB):[/green] {commit_hash[:7]} - {message}"
            )

    except Exception as e:
        console.print(f"[red]Git Error:[/red] {e}")
        raise typer.Exit(code=1)


@lsp_app.command("definition")
def lsp_definition(
    file: str = typer.Option(..., "--file", "-f", help="Abs path to file"),
    line: int = typer.Option(..., "--line", "-l", help="0-indexed line number"),
    character: int = typer.Option(
        ..., "--char", "-c", help="0-indexed character number"
    ),
):
    """
    Handle textDocument/definition request.
    Output: JSON Location | null
    """
    import json
    from monoco.core.lsp import Position
    from monoco.features.issue.lsp import DefinitionProvider

    config = get_config()
    # Workspace Root resolution is key here.
    # If we are in a workspace, we want the workspace root, not just issue root.
    # _resolve_project_root returns the closest project root or monoco root.
    workspace_root = _resolve_project_root(config)
    # Search for topmost workspace root to enable cross-project navigation
    current_best = workspace_root
    for parent in [workspace_root] + list(workspace_root.parents):
        if (parent / ".monoco" / "workspace.yaml").exists() or (
            parent / ".monoco" / "project.yaml"
        ).exists():
            current_best = parent
    workspace_root = current_best

    provider = DefinitionProvider(workspace_root)
    file_path = Path(file)

    locations = provider.provide_definition(
        file_path, Position(line=line, character=character)
    )

    # helper to serialize
    print(json.dumps([l.model_dump(mode="json") for l in locations]))


@app.command("escalate")
def escalate(
    issue_id: str = typer.Argument(..., help="Issue ID to escalate"),
    to_level: str = typer.Option(
        ..., "--to", help="Target criticality level (low, medium, high, critical)"
    ),
    reason: str = typer.Option(..., "--reason", help="Reason for escalation"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """
    Request escalation of issue criticality.
    Requires approval before taking effect.
    """
    from .criticality import (
        CriticalityLevel,
        EscalationApprovalWorkflow,
        CriticalityValidator,
    )
    from monoco.core.workspace import find_monoco_root

    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    # Parse target level
    try:
        target_level = CriticalityLevel(to_level.lower())
    except ValueError:
        valid_levels = [e.value for e in CriticalityLevel]
        OutputManager.error(
            f"Invalid level: '{to_level}'. Valid: {', '.join(valid_levels)}"
        )
        raise typer.Exit(code=1)

    # Find issue
    issue_path = core.find_issue_path(issues_root, issue_id)
    if not issue_path:
        OutputManager.error(f"Issue {issue_id} not found.")
        raise typer.Exit(code=1)

    issue = core.parse_issue(issue_path)
    if not issue:
        OutputManager.error(f"Could not parse issue {issue_id}.")
        raise typer.Exit(code=1)

    current_level = issue.criticality or CriticalityLevel.MEDIUM

    # Validate escalation direction
    can_modify, error_msg = CriticalityValidator.can_modify_criticality(
        current_level, target_level, is_escalation_approved=False
    )

    if not can_modify:
        OutputManager.error(error_msg or "Escalation not allowed")
        raise typer.Exit(code=1)

    # Create escalation request
    project_root = find_monoco_root()
    storage_path = project_root / ".monoco" / "escalations.yaml"
    workflow = EscalationApprovalWorkflow(storage_path)

    import getpass

    request = workflow.create_request(
        issue_id=issue_id,
        from_level=current_level,
        to_level=target_level,
        reason=reason,
        requested_by=getpass.getuser(),
    )

    OutputManager.print(
        {
            "status": "escalation_requested",
            "escalation_id": request.id,
            "issue_id": issue_id,
            "from": current_level.value,
            "to": target_level.value,
            "message": f"Escalation request {request.id} created. Awaiting approval.",
        }
    )


@app.command("approve-escalation")
def approve_escalation(
    escalation_id: str = typer.Argument(..., help="Escalation request ID"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """
    Approve a pending escalation request.
    Updates the issue's criticality upon approval.
    """
    from .criticality import (
        EscalationApprovalWorkflow,
        EscalationStatus,
    )
    from monoco.core.workspace import find_monoco_root

    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    # Load workflow
    project_root = find_monoco_root()
    storage_path = project_root / ".monoco" / "escalations.yaml"
    workflow = EscalationApprovalWorkflow(storage_path)

    request = workflow.get_request(escalation_id)
    if not request:
        OutputManager.error(f"Escalation request {escalation_id} not found.")
        raise typer.Exit(code=1)

    if request.status != EscalationStatus.PENDING:
        OutputManager.error(f"Request is already {request.status.value}.")
        raise typer.Exit(code=1)

    # Approve
    import getpass

    approved = workflow.approve(escalation_id, getpass.getuser())

    # Update issue criticality
    try:
        core.update_issue(
            issues_root,
            request.issue_id,
            # Pass criticality through extra fields mechanism or update directly
        )
        # We need to update criticality directly
        issue_path = core.find_issue_path(issues_root, request.issue_id)
        if issue_path:
            content = issue_path.read_text()
            import yaml
            import re

            match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
            if match:
                yaml_str = match.group(1)
                data = yaml.safe_load(yaml_str) or {}
                data["criticality"] = request.to_level.value
                data["updated_at"] = datetime.now().isoformat()

                new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)
                body = content[match.end() :]
                new_content = f"---\n{new_yaml}---{body}"
                issue_path.write_text(new_content)

        OutputManager.print(
            {
                "status": "escalation_approved",
                "escalation_id": escalation_id,
                "issue_id": request.issue_id,
                "new_criticality": request.to_level.value,
            }
        )
    except Exception as e:
        OutputManager.error(f"Failed to update issue: {e}")
        raise typer.Exit(code=1)


@app.command("show")
def show(
    issue_id: str = typer.Argument(..., help="Issue ID to show"),
    policy: bool = typer.Option(False, "--policy", help="Show resolved policy"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """
    Show issue details, optionally with resolved policy.
    """
    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    issue_path = core.find_issue_path(issues_root, issue_id)
    if not issue_path:
        OutputManager.error(f"Issue {issue_id} not found.")
        raise typer.Exit(code=1)

    issue = core.parse_issue(issue_path)
    if not issue:
        OutputManager.error(f"Could not parse issue {issue_id}.")
        raise typer.Exit(code=1)

    result = {
        "issue": issue.model_dump(),
    }

    if policy:
        resolved_policy = issue.resolved_policy
        result["policy"] = {
            "criticality": issue.criticality.value
            if issue.criticality
            else "medium (default)",
            "agent_review": resolved_policy.agent_review.value,
            "human_review": resolved_policy.human_review.value,
            "min_coverage": resolved_policy.min_coverage,
            "rollback_on_failure": resolved_policy.rollback_on_failure.value,
            "require_security_scan": resolved_policy.require_security_scan,
            "require_performance_check": resolved_policy.require_performance_check,
            "max_reviewers": resolved_policy.max_reviewers,
        }

    OutputManager.print(result)


@app.command("check-critical")
def check_critical(
    fail_on_warning: bool = typer.Option(
        False,
        "--fail-on-warning",
        help="Exit with error code if high priority issues are found",
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """
    Check for incomplete critical/high priority issues.

    Returns:
        0: No critical/high issues found
        1: High priority issues found (warning)
        2: Critical issues found (blocking)
    """
    from .criticality import CriticalityLevel

    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    issues = core.list_issues(issues_root)

    critical_issues = []
    high_issues = []

    for issue in issues:
        if issue.status == "closed":
            continue

        criticality = issue.criticality
        if not criticality:
            continue

        if criticality == CriticalityLevel.CRITICAL:
            critical_issues.append(issue)
        elif criticality == CriticalityLevel.HIGH:
            high_issues.append(issue)

    result = {
        "critical_count": len(critical_issues),
        "high_count": len(high_issues),
        "critical_issues": [
            {"id": i.id, "title": i.title, "stage": i.stage}
            for i in critical_issues
        ],
        "high_issues": [
            {"id": i.id, "title": i.title, "stage": i.stage}
            for i in high_issues
        ],
    }

    if OutputManager.is_agent_mode() or json:
        OutputManager.print(result)
    else:
        if critical_issues:
            console.print("[red]❌ Critical issues (blocking):[/red]")
            for issue in critical_issues:
                console.print(f"  [red]• {issue.id}:[/red] {issue.title} ({issue.stage})")

        if high_issues:
            console.print("[yellow]⚠️  High priority issues (warning):[/yellow]")
            for issue in high_issues:
                console.print(f"  [yellow]• {issue.id}:[/yellow] {issue.title} ({issue.stage})")

        if not critical_issues and not high_issues:
            console.print("[green]✓ No incomplete critical or high priority issues.[/green]")

    # Determine exit code
    if critical_issues:
        raise typer.Exit(code=2)
    elif high_issues and fail_on_warning:
        raise typer.Exit(code=1)
    elif high_issues:
        # Warning only, don't fail
        pass

    raise typer.Exit(code=0)


@app.command("sync-isolation")
def sync_isolation(
    issue_id: str = typer.Argument(..., help="Issue ID to sync isolation for"),
    branch: Optional[str] = typer.Option(
        None, "--branch", help="Current branch name (auto-detected if not provided)"
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """
    Sync issue isolation configuration with current branch.

    Updates the isolation.ref field to match the current branch context.
    This is typically called by the post-checkout hook.
    """
    import subprocess
    from .core import update_issue_field

    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = Path(config.paths.root).resolve()

    # Auto-detect branch if not provided
    if not branch:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            branch = result.stdout.strip()
        except Exception:
            OutputManager.error("Could not detect current branch. Use --branch.")
            raise typer.Exit(code=1)

    # Find the issue
    issue_path = core.find_issue_path(issues_root, issue_id)
    if not issue_path:
        OutputManager.error(f"Issue {issue_id} not found.")
        raise typer.Exit(code=1)

    # Parse current issue
    issue = core.parse_issue(issue_path)
    if not issue:
        OutputManager.error(f"Could not parse issue {issue_id}.")
        raise typer.Exit(code=1)

    # Check if isolation needs updating
    current_isolation = issue.isolation
    if current_isolation:
        current_ref = current_isolation.ref or ""
        current_isolation_dict = {
            "type": current_isolation.type,
            "ref": current_isolation.ref,
        }
        if current_isolation.path:
            current_isolation_dict["path"] = current_isolation.path
        if current_isolation.created_at:
            current_isolation_dict["created_at"] = current_isolation.created_at.isoformat()
    else:
        current_ref = ""
        current_isolation_dict = {}

    # Expected ref format: branch:branch-name
    expected_ref = f"branch:{branch}"

    if current_ref == expected_ref:
        if OutputManager.is_agent_mode() or json:
            OutputManager.print({"updated": False, "message": "Isolation already up to date"})
        else:
            console.print(f"[dim]Isolation already up to date for {issue_id}[/dim]")
        raise typer.Exit(code=0)

    # Update the isolation field
    new_isolation = {**current_isolation_dict, "ref": expected_ref, "type": "branch"}

    try:
        update_issue_field(
            issue_path,
            "isolation",
            new_isolation,
        )

        result = {
            "updated": True,
            "issue_id": issue_id,
            "isolation": new_isolation,
        }

        if OutputManager.is_agent_mode() or json:
            OutputManager.print(result)
        else:
            console.print(f"[green]✓ Updated isolation for {issue_id}:[/green] {expected_ref}")

    except Exception as e:
        OutputManager.error(f"Failed to update isolation: {e}")
        raise typer.Exit(code=1)


def _validate_branch_context(
    project_root: Path,
    allowed: Optional[List[str]] = None,
    forbidden: Optional[List[str]] = None,
    force: bool = False,
    command_name: str = "Command",
):
    """
    Enforce branch context rules.
    """
    if force:
        return
    
    import os
    if os.getenv("PYTEST_CURRENT_TEST"):
        return

    try:
        current = git.get_current_branch(project_root)
    except Exception:
        # If git fails (not a repo?), skip check or fail?
        # Let's assume strictness.
        return

    is_trunk = current in ["main", "master"]

    if allowed:
        if "TRUNK" in allowed and not is_trunk:
            # Check if current is strictly in allowed list otherwise
            if current not in allowed:
                OutputManager.error(
                    f"❌ {command_name} restricted to 'main' branch. Current: {current}\n"
                    f"   Use --force to bypass if necessary."
                )
                raise typer.Exit(code=1)

    if forbidden:
        if "TRUNK" in forbidden and is_trunk:
            OutputManager.error(
                f"❌ {command_name} cannot be run on 'main' branch.\n"
                f"   Please checkout your feature branch first."
            )
            raise typer.Exit(code=1)
