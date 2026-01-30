import typer
from pathlib import Path
from typing import Optional, List
from datetime import datetime
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
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """Create a new issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

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

        try:
            rel_path = path.relative_to(Path.cwd())
        except ValueError:
            rel_path = path

        if OutputManager.is_agent_mode():
            OutputManager.print(
                {"issue": issue, "path": str(rel_path), "status": "created"}
            )
        else:
            console.print(
                f"[green]✔ Created {issue.id} in status {issue.status}.[/green]"
            )
            console.print(f"Path: {rel_path}")

            # Prompt for Language
            source_lang = config.i18n.source_lang or "en"

            hint_msgs = {
                "zh": "请使用中文填写 Issue 内容。",
                "en": "Please fill the ticket content in English.",
            }

            hint_msg = hint_msgs.get(
                source_lang, f"Please fill the ticket content in {source_lang.upper()}."
            )

            console.print(f"\n[bold yellow]Agent Hint:[/bold yellow] {hint_msg}")

    except ValueError as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)

    except ValueError as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("update")
def update(
    issue_id: str = typer.Argument(..., help="Issue ID to update"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    status: Optional[str] = typer.Option(None, "--status", help="New status"),
    stage: Optional[str] = typer.Option(None, "--stage", help="New stage"),
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
    json: AgentOutput = False,
):
    """Move issue to open status and set stage to Draft."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)
    try:
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
        True,
        "--branch/--no-branch",
        "-b",
        help="[Default] Start in a new git branch (feat/<id>-<slug>). Use --no-branch to disable.",
    ),
    direct: bool = typer.Option(
        False,
        "--direct",
        help="Privileged: Work directly on current branch (equivalent to --no-branch).",
    ),
    worktree: bool = typer.Option(
        False,
        "--worktree",
        "-w",
        help="Start in a new git worktree for parallel development",
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    force: bool = typer.Option(False, "--force", help="Bypass branch context checks"),
    json: AgentOutput = False,
):
    """
    Start working on an issue (Stage -> Doing).

    Default behavior is to create a feature branch.
    Use --direct or --no-branch to work on current branch.
    """
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

    # Handle direct flag override
    if direct:
        branch = False

    # Context Check
    # If creating a new branch (default), we MUST be on trunk to avoid nesting.
    # If direct/no-branch, we don't care.
    if branch:
        _validate_branch_context(
            project_root, allowed=["TRUNK"], force=force, command_name="start"
        )

    if branch and worktree:
        OutputManager.error("Cannot specify both --branch and --worktree.")
        raise typer.Exit(code=1)

    try:
        # Implicitly ensure status is Open
        issue = core.update_issue(issues_root, issue_id, status="open", stage="doing")

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
    json: AgentOutput = False,
):
    """Submit issue for review (Stage -> Review) and generate delivery report."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

    # Context Check: Submit should happen on feature branch, not trunk
    _validate_branch_context(
        project_root, forbidden=["TRUNK"], force=force, command_name="submit"
    )

    try:
        # Implicitly ensure status is Open
        issue = core.update_issue(issues_root, issue_id, status="open", stage="review")

        # Delivery Report Generation
        report_status = "skipped"
        try:
            core.generate_delivery_report(issues_root, issue_id, project_root)
            report_status = "generated"
        except Exception as e:
            report_status = f"failed: {e}"

        OutputManager.print(
            {
                "issue": issue,
                "status": "submitted",
                "report": report_status,
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
    prune: bool = typer.Option(
        False, "--prune", help="Delete branch/worktree after close"
    ),
    force: bool = typer.Option(False, "--force", help="Force delete branch/worktree"),
    force_prune: bool = typer.Option(
        False,
        "--force-prune",
        help="Force delete branch/worktree with checking bypassed (includes warning)",
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """Close issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

    # Pre-flight check for interactive guidance (Requirement FEAT-0082 #6)
    if solution is None:
        # Resolve options from engine
        from .engine import get_engine

        engine = get_engine(str(issues_root.parent))
        valid_solutions = engine.issue_config.solutions or []
        OutputManager.error(
            f"Closing an issue requires a solution. Options: {', '.join(valid_solutions)}"
        )
        raise typer.Exit(code=1)

    # Context Check: Close should happen on trunk (after merge)
    _validate_branch_context(
        project_root,
        allowed=["TRUNK"],
        force=(force or force_prune),
        command_name="close",
    )

    # Handle force-prune logic
    if force_prune:
        # Use OutputManager to check mode, as `json` arg might not be reliable with Typer Annotated
        if not OutputManager.is_agent_mode() and not force:
            confirm = typer.confirm(
                "⚠️  [Bold Red]Warning:[/Bold Red] You are about to FORCE prune issue resources. Git merge checks will be bypassed.\nAre you sure you want to proceed?",
                default=False,
            )
            if not confirm:
                raise typer.Abort()
        prune = True
        force = True

    try:
        issue = core.update_issue(
            issues_root, issue_id, status="closed", solution=solution
        )

        pruned_resources = []
        if prune:
            try:
                pruned_resources = core.prune_issue_resources(
                    issues_root, issue_id, force, project_root
                )
            except Exception as e:
                OutputManager.error(f"Prune Error: {e}")
                raise typer.Exit(code=1)

        OutputManager.print(
            {"issue": issue, "status": "closed", "pruned": pruned_resources}
        )

    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@backlog_app.command("push")
def push(
    issue_id: str = typer.Argument(..., help="Issue ID to push to backlog"),
    root: Optional[str] = typer.Option(
        None, "--root", help="Override issues root directory"
    ),
    json: AgentOutput = False,
):
    """Push issue to backlog."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        issue = core.update_issue(issues_root, issue_id, status="backlog")
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
    json: AgentOutput = False,
):
    """Pull issue from backlog (Open & Draft)."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        issue = core.update_issue(issues_root, issue_id, status="open", stage="draft")
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
    json: AgentOutput = False,
):
    """Cancel issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        issue = core.update_issue(
            issues_root, issue_id, status="closed", solution="cancelled"
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
    json: AgentOutput = False,
):
    """List issues in a table format with filtering."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)

    # Validation
    if status and status.lower() not in ["open", "closed", "backlog", "all"]:
        OutputManager.error(
            f"Invalid status: {status}. Use open, closed, backlog or all."
        )
        raise typer.Exit(code=1)

    target_status = status.lower() if status else "open"

    issues = core.list_issues(issues_root, recursive_workspace=workspace)
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
        # Try to parse ID from branch "feat/issue-123-slug"
        import re

        match = re.search(r"(?:feat|fix|chore|epic)/([a-zA-Z]+-\d+)", current)
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
