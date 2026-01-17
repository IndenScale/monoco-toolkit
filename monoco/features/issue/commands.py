import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table
import typer

from monoco.core.config import get_config
from monoco.core.output import print_output, OutputManager, AgentOutput
from .models import IssueType, IssueStatus, IssueSolution, IssueStage, IsolationType, IssueMetadata
from . import core

app = typer.Typer(help="Agent-Native Issue Management.")
backlog_app = typer.Typer(help="Manage backlog operations.")
app.add_typer(backlog_app, name="backlog")
console = Console()

@app.command("create")
def create(
    type: IssueType = typer.Argument(..., help="Issue type (epic, feature, chore, fix)"),
    title: str = typer.Option(..., "--title", "-t", help="Issue title"),
    parent: Optional[str] = typer.Option(None, "--parent", "-p", help="Parent Issue ID"),
    is_backlog: bool = typer.Option(False, "--backlog", help="Create as backlog item"),
    stage: Optional[IssueStage] = typer.Option(None, "--stage", help="Issue stage (draft, doing, review)"),
    dependencies: List[str] = typer.Option([], "--dependency", "-d", help="Issue dependency ID(s)"),
    related: List[str] = typer.Option([], "--related", "-r", help="Related Issue ID(s)"),
    subdir: Optional[str] = typer.Option(None, "--subdir", "-s", help="Subdirectory for organization (e.g. 'Backend/Auth')"),
    sprint: Optional[str] = typer.Option(None, "--sprint", help="Sprint ID"),
    tags: List[str] = typer.Option([], "--tag", help="Tags"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    json: AgentOutput = False,
):
    """Create a new issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    status = IssueStatus.BACKLOG if is_backlog else IssueStatus.OPEN
    
    if parent:
        parent_path = core.find_issue_path(issues_root, parent)
        if not parent_path:
            OutputManager.error(f"Parent issue {parent} not found.")
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
            subdir=subdir,
            sprint=sprint,
            tags=tags
        )
        
        try:
            rel_path = path.relative_to(Path.cwd())
        except ValueError:
            rel_path = path

        OutputManager.print({
            "issue": issue,
            "path": str(rel_path),
            "status": "created"
        })

    except ValueError as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)

@app.command("update")
def update(
    issue_id: str = typer.Argument(..., help="Issue ID to update"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    status: Optional[IssueStatus] = typer.Option(None, "--status", help="New status"),
    stage: Optional[IssueStage] = typer.Option(None, "--stage", help="New stage"),
    parent: Optional[str] = typer.Option(None, "--parent", "-p", help="Parent Issue ID"),
    sprint: Optional[str] = typer.Option(None, "--sprint", help="Sprint ID"),
    dependencies: Optional[List[str]] = typer.Option(None, "--dependency", "-d", help="Issue dependency ID(s)"),
    related: Optional[List[str]] = typer.Option(None, "--related", "-r", help="Related Issue ID(s)"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Tags"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
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
            tags=tags
        )
        
        OutputManager.print({
            "issue": issue,
            "status": "updated"
        })
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)


@app.command("open")
def move_open(
    issue_id: str = typer.Argument(..., help="Issue ID to open"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    json: AgentOutput = False,
):
    """Move issue to open status and set stage to Draft."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        # Pull operation: Force stage to TODO
        issue = core.update_issue(issues_root, issue_id, status=IssueStatus.OPEN, stage=IssueStage.DRAFT)
        OutputManager.print({
            "issue": issue,
            "status": "opened"
        })
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)

@app.command("start")
def start(
    issue_id: str = typer.Argument(..., help="Issue ID to start"),
    branch: bool = typer.Option(False, "--branch", "-b", help="Start in a new git branch"),
    worktree: bool = typer.Option(False, "--worktree", "-w", help="Start in a new git worktree"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    json: AgentOutput = False,
):
    """Start working on an issue (Stage -> Doing)."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)

    if branch and worktree:
         OutputManager.error("Cannot specify both --branch and --worktree.")
         raise typer.Exit(code=1)

    try:
        # Implicitly ensure status is Open
        issue = core.update_issue(issues_root, issue_id, status=IssueStatus.OPEN, stage=IssueStage.DOING)
        
        isolation_info = None

        if branch:
            try:
                issue = core.start_issue_isolation(issues_root, issue_id, IsolationType.BRANCH, project_root)
                isolation_info = {"type": "branch", "ref": issue.isolation.ref}
            except Exception as e:
                OutputManager.error(f"Failed to create branch: {e}")
                raise typer.Exit(code=1)
                
        if worktree:
            try:
                issue = core.start_issue_isolation(issues_root, issue_id, IsolationType.WORKTREE, project_root)
                isolation_info = {"type": "worktree", "path": issue.isolation.path, "ref": issue.isolation.ref}
            except Exception as e:
                OutputManager.error(f"Failed to create worktree: {e}")
                raise typer.Exit(code=1)

        OutputManager.print({
            "issue": issue,
            "status": "started",
            "isolation": isolation_info
        })
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)

@app.command("submit")
def submit(
    issue_id: str = typer.Argument(..., help="Issue ID to submit"),
    prune: bool = typer.Option(False, "--prune", help="Delete branch/worktree after submit"),
    force: bool = typer.Option(False, "--force", help="Force delete branch/worktree"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    json: AgentOutput = False,
):
    """Submit issue for review (Stage -> Review) and generate delivery report."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)
    try:
        # Implicitly ensure status is Open
        issue = core.update_issue(issues_root, issue_id, status=IssueStatus.OPEN, stage=IssueStage.REVIEW)
        
        # Delivery Report Generation
        report_status = "skipped"
        try:
             core.generate_delivery_report(issues_root, issue_id, project_root)
             report_status = "generated"
        except Exception as e:
             report_status = f"failed: {e}"
        
        pruned_resources = []
        if prune:
            try:
                pruned_resources = core.prune_issue_resources(issues_root, issue_id, force, project_root)
            except Exception as e:
                OutputManager.error(f"Prune Error: {e}")
                raise typer.Exit(code=1)
             
        OutputManager.print({
            "issue": issue,
            "status": "submitted",
            "report": report_status,
            "pruned": pruned_resources
        })
             
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)

@app.command("close")
def move_close(
    issue_id: str = typer.Argument(..., help="Issue ID to close"),
    solution: Optional[IssueSolution] = typer.Option(None, "--solution", "-s", help="Solution type"),
    prune: bool = typer.Option(False, "--prune", help="Delete branch/worktree after close"),
    force: bool = typer.Option(False, "--force", help="Force delete branch/worktree"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    json: AgentOutput = False,
):
    """Close issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)
    
    # Pre-flight check for interactive guidance (Requirement FEAT-0082 #6)
    if solution is None:
        valid_solutions = [e.value for e in IssueSolution]
        OutputManager.error(f"Closing an issue requires a solution. Options: {', '.join(valid_solutions)}")
        raise typer.Exit(code=1)

    try:
        issue = core.update_issue(issues_root, issue_id, status=IssueStatus.CLOSED, solution=solution)
        
        pruned_resources = []
        if prune:
            try:
                pruned_resources = core.prune_issue_resources(issues_root, issue_id, force, project_root)
            except Exception as e:
                OutputManager.error(f"Prune Error: {e}")
                raise typer.Exit(code=1)

        OutputManager.print({
            "issue": issue,
            "status": "closed",
            "pruned": pruned_resources
        })

    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)

@backlog_app.command("push")
def push(
    issue_id: str = typer.Argument(..., help="Issue ID to push to backlog"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    json: AgentOutput = False,
):
    """Push issue to backlog."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        issue = core.update_issue(issues_root, issue_id, status=IssueStatus.BACKLOG)
        OutputManager.print({
            "issue": issue,
            "status": "pushed_to_backlog"
        })
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)

@backlog_app.command("pull")
def pull(
    issue_id: str = typer.Argument(..., help="Issue ID to pull from backlog"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    json: AgentOutput = False,
):
    """Pull issue from backlog (Open & Draft)."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        issue = core.update_issue(issues_root, issue_id, status=IssueStatus.OPEN, stage=IssueStage.DRAFT)
        OutputManager.print({
            "issue": issue,
            "status": "pulled_from_backlog"
        })
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)

@app.command("cancel")
def cancel(
    issue_id: str = typer.Argument(..., help="Issue ID to cancel"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    json: AgentOutput = False,
):
    """Cancel issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        issue = core.update_issue(issues_root, issue_id, status=IssueStatus.CLOSED, solution=IssueSolution.CANCELLED)
        OutputManager.print({
            "issue": issue,
            "status": "cancelled"
        })
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)

@app.command("delete")
def delete(
    issue_id: str = typer.Argument(..., help="Issue ID to delete"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    json: AgentOutput = False,
):
    """Physically remove an issue file."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        core.delete_issue_file(issues_root, issue_id)
        OutputManager.print({
            "id": issue_id,
            "status": "deleted"
        })
    except Exception as e:
        OutputManager.error(str(e))
        raise typer.Exit(code=1)

@app.command("move")
def move(
    issue_id: str = typer.Argument(..., help="Issue ID to move"),
    target: str = typer.Option(..., "--to", help="Target project directory (e.g., ../OtherProject)"),
    renumber: bool = typer.Option(False, "--renumber", help="Automatically renumber on ID conflict"),
    root: Optional[str] = typer.Option(None, "--root", help="Override source issues root directory"),
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
        OutputManager.error("Target path must be a project root with 'Issues' directory or an 'Issues' directory itself.")
        raise typer.Exit(code=1)
    
    try:
        updated_meta, new_path = core.move_issue(
            source_issues_root,
            issue_id,
            target_issues_root,
            renumber=renumber
        )
        
        try:
            rel_path = new_path.relative_to(Path.cwd())
        except ValueError:
            rel_path = new_path
        
        OutputManager.print({
            "issue": updated_meta,
            "new_path": str(rel_path),
            "status": "moved",
            "renumbered": updated_meta.id != issue_id
        })
        
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
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
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
        "done": "[bold green]DONE[/bold green]"
    }
    
    for stage, issues in board_data.items():
        issue_list = []
        for issue in sorted(issues, key=lambda x: x.updated_at, reverse=True):
            type_color = {
                IssueType.FEATURE: "green",
                IssueType.CHORE: "blue",
                IssueType.FIX: "red",
                IssueType.EPIC: "magenta"
            }.get(issue.type, "white")
            
            issue_list.append(
                Panel(
                    f"[{type_color}]{issue.id}[/{type_color}]\n{issue.title}",
                    expand=True,
                    padding=(0, 1)
                )
            )
        
        from rich.console import Group
        content = Group(*issue_list) if issue_list else "[dim]Empty[/dim]"
        
        columns.append(
            Panel(
                content,
                title=stage_titles.get(stage, stage.upper()),
                width=35,
                padding=(1, 1)
            )
        )

    console.print(Columns(columns, equal=True, expand=True))

@app.command("list")
def list_cmd(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (open, closed, backlog, all)"),
    type: Optional[IssueType] = typer.Option(None, "--type", "-t", help="Filter by type"),
    stage: Optional[IssueStage] = typer.Option(None, "--stage", help="Filter by stage"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    workspace: bool = typer.Option(False, "--workspace", "-w", help="Include issues from workspace members"),
    json: AgentOutput = False,
):
    """List issues in a table format with filtering."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    
    # Validation
    if status and status.lower() not in ["open", "closed", "backlog", "all"]:
         OutputManager.error(f"Invalid status: {status}. Use open, closed, backlog or all.")
         raise typer.Exit(code=1)
         
    target_status = status.lower() if status else "open"
    
    issues = core.list_issues(issues_root, recursive_workspace=workspace)
    filtered = []
    
    for i in issues:
        # Status Filter
        if target_status != "all":
            if i.status.value != target_status:
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
        IssueType.FIX: "red"
    }
    
    status_colors = {
        IssueStatus.OPEN: "green",
        IssueStatus.BACKLOG: "blue",
        IssueStatus.CLOSED: "dim"
    }

    for i in issues:
        t_color = type_colors.get(i.type, "white")
        s_color = status_colors.get(i.status, "white")
        
        stage_str = i.stage.value if i.stage else "-"
        updated_str = i.updated_at.strftime("%Y-%m-%d %H:%M")
        
        table.add_row(
            i.id,
            f"[{t_color}]{i.type.value}[/{t_color}]",
            f"[{s_color}]{i.status.value}[/{s_color}]",
            stage_str,
            i.title,
            updated_str
        )
        
    console.print(table)

@app.command("query")
def query_cmd(
    query: str = typer.Argument(..., help="Search query (e.g. '+bug -ui' or 'login')"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
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

    _render_issues_table(results, title=f"Search Results for '{query}' ({len(results)})")

@app.command("scope")
def scope(
    sprint: Optional[str] = typer.Option(None, "--sprint", help="Filter by Sprint ID"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all, otherwise show only open items"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recursively scan subdirectories"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    workspace: bool = typer.Option(False, "--workspace", "-w", help="Include issues from workspace members"),
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

    tree = Tree(f"[bold blue]Monoco Issue Scope[/bold blue]")
    epics = sorted([i for i in issues if i.type == IssueType.EPIC], key=lambda x: x.id)
    stories = [i for i in issues if i.type == IssueType.FEATURE]
    tasks = [i for i in issues if i.type in [IssueType.CHORE, IssueType.FIX]]

    status_map = {IssueStatus.OPEN: "[blue]●[/blue]", IssueStatus.CLOSED: "[green]✔[/green]", IssueStatus.BACKLOG: "[dim]💤[/dim]"}

    for epic in epics:
        epic_node = tree.add(f"{status_map[epic.status]} [bold]{epic.id}[/bold]: {epic.title}")
        child_stories = sorted([s for s in stories if s.parent == epic.id], key=lambda x: x.id)
        for story in child_stories:
            story_node = epic_node.add(f"{status_map[story.status]} [bold]{story.id}[/bold]: {story.title}")
            child_tasks = sorted([t for t in tasks if t.parent == story.id], key=lambda x: x.id)
            for task in child_tasks:
                story_node.add(f"{status_map[task.status]} [bold]{task.id}[/bold]: {task.title}")

    console.print(Panel(tree, expand=False))

@app.command("inspect")
def inspect(
    target: str = typer.Argument(..., help="Issue ID or File Path"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    ast: bool = typer.Option(False, "--ast", help="Output JSON AST structure for debugging"),
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
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recursively scan subdirectories"),
    fix: bool = typer.Option(False, "--fix", help="Attempt to automatically fix issues (e.g. missing headings)"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table, json)"),
    file: Optional[str] = typer.Option(None, "--file", help="Validate a single file instead of scanning the entire workspace"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
    json: AgentOutput = False,
):
    """Verify the integrity of the Issues directory (declarative check)."""
    from . import linter
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    
    if OutputManager.is_agent_mode():
        format = "json"

    linter.run_lint(issues_root, recursive=recursive, fix=fix, format=format, file_path=file)

def _resolve_issues_root(config, cli_root: Optional[str]) -> Path:
    """
    Resolve the absolute path to the issues directory.
    Implements Smart Path Resolution & Workspace Awareness.
    """
    from monoco.core.workspace import is_project_root, find_projects
    
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
    # We need to detect if we are in a Workspace Root with multiple projects
    cwd = Path.cwd()
    
    # If CWD is NOT a project root (no .monoco/), scan for subprojects
    if not is_project_root(cwd):
        subprojects = find_projects(cwd)
        if len(subprojects) > 1:
            console.print(f"[yellow]Workspace detected with {len(subprojects)} projects:[/yellow]")
            for p in subprojects:
                console.print(f" - [bold]{p.name}[/bold]")
            console.print("\n[yellow]Please specify a project using --root <PATH>.[/yellow]")
            # We don't exit here strictly, but usually this means we can't find 'Issues' in CWD anyway
            # so the config fallbacks below will likely fail or point to non-existent CWD/Issues.
            # But let's fail fast to be helpful.
            raise typer.Exit(code=1)
        elif len(subprojects) == 1:
            # Auto-select the only child project?
            # It's safer to require explicit intent, but let's try to be helpful if it's obvious.
            # However, standard behavior is usually "operate on current dir". 
            # Let's stick to standard config resolution, but maybe warn.
            pass

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
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Commit message"),
    issue_id: Optional[str] = typer.Option(None, "--issue", "-i", help="Link commit to Issue ID"),
    detached: bool = typer.Option(False, "--detached", help="Flag commit as intentionally detached (no issue link)"),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="Commit type (feat, fix, etc.)"),
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Commit scope"),
    subject: Optional[str] = typer.Option(None, "--subject", help="Commit subject"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
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
        code, stdout, _ = git._run_git(["diff", "--cached", "--name-only"], project_root)
        staged_files = [l for l in stdout.splitlines() if l.strip()]
        
        # Determine Mode
        if issue_id:
            # MODE: Linked Commit
            console.print(f"[bold cyan]Linked Commit Mode[/bold cyan] (Ref: {issue_id})")
            
            if not core.find_issue_path(issues_root, issue_id):
                 console.print(f"[red]Error:[/red] Issue {issue_id} not found.")
                 raise typer.Exit(code=1)

            if not staged_files:
                 console.print("[yellow]No staged files.[/yellow] Please `git add` files.")
                 raise typer.Exit(code=1)

            if not message:
                if not type or not subject:
                    console.print("[red]Error:[/red] Provide --message OR (--type and --subject).")
                    raise typer.Exit(code=1)
                scope_part = f"({scope})" if scope else ""
                message = f"{type}{scope_part}: {subject}"
            
            if f"Ref: {issue_id}" not in message:
                message += f"\n\nRef: {issue_id}"
                
            commit_hash = git.git_commit(project_root, message)
            console.print(f"[green]✔ Committed:[/green] {commit_hash[:7]}")

        elif detached:
            # MODE: Detached
            console.print(f"[bold yellow]Detached Commit Mode[/bold yellow]")
            
            if not staged_files:
                 console.print("[yellow]No staged files.[/yellow] Please `git add` files.")
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
                issues_prefix = "Issues" # Fallback

            non_issue_staged = [f for f in staged_files if not f.startswith(issues_prefix)]
            
            if non_issue_staged:
                console.print(f"[red]⛔ Strict Policy:[/red] Code changes detected in staging ({len(non_issue_staged)} files).")
                console.print("You must specify [bold]--issue <ID>[/bold] or [bold]--detached[/bold].")
                raise typer.Exit(code=1)

            # If nothing staged, check unstaged Issue files (Legacy Auto-Add)
            if not staged_files:
                status_files = git.get_git_status(project_root, str(rel_issues))
                if not status_files:
                    console.print("[yellow]Nothing to commit.[/yellow]")
                    return
                
                # Auto-stage Issue files
                git.git_add(project_root, status_files)
                staged_files = status_files # Now they are staged
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
            console.print(f"[green]✔ Committed (DB):[/green] {commit_hash[:7]} - {message}")
        
    except Exception as e:
         console.print(f"[red]Git Error:[/red] {e}")
         raise typer.Exit(code=1)
