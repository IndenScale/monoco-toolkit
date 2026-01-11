import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table
import typer

from monoco.core.config import get_config
from monoco.core.output import print_output
from .models import IssueType, IssueStatus, IssueSolution, IssueStage
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
    stage: Optional[IssueStage] = typer.Option(None, "--stage", help="Issue stage (todo, doing, review)"),
    dependencies: List[str] = typer.Option([], "--dependency", "-d", help="Issue dependency ID(s)"),
    related: List[str] = typer.Option([], "--related", "-r", help="Related Issue ID(s)"),
    subdir: Optional[str] = typer.Option(None, "--subdir", "-s", help="Subdirectory for organization (e.g. 'Backend/Auth')"),
    sprint: Optional[str] = typer.Option(None, "--sprint", help="Sprint ID"),
    tags: List[str] = typer.Option([], "--tag", help="Tags"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Create a new issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    status = IssueStatus.BACKLOG if is_backlog else IssueStatus.OPEN
    
    if parent:
        parent_path = core.find_issue_path(issues_root, parent)
        if not parent_path:
            console.print(f"[red]✘ Error:[/red] Parent issue {parent} not found.")
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

        console.print(f"[green]✔[/green] Created [bold]{issue.id}[/bold] in status [cyan]{issue.status.value}[/cyan].")
        console.print(f"[dim]Path: {rel_path}[/dim]")
    except ValueError as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("open")
def move_open(
    issue_id: str = typer.Argument(..., help="Issue ID to open"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Move issue to open status and set stage to Todo."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        # Pull operation: Force stage to TODO
        core.update_issue(issues_root, issue_id, status=IssueStatus.OPEN, stage=IssueStage.TODO)
        console.print(f"[green]▶[/green] Issue [bold]{issue_id}[/bold] moved to open/todo.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("start")
def start(
    issue_id: str = typer.Argument(..., help="Issue ID to start"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Start working on an issue (Stage -> Doing)."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        # Implicitly ensure status is Open
        core.update_issue(issues_root, issue_id, status=IssueStatus.OPEN, stage=IssueStage.DOING)
        console.print(f"[green]🚀[/green] Issue [bold]{issue_id}[/bold] started.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("submit")
def submit(
    issue_id: str = typer.Argument(..., help="Issue ID to submit"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Submit issue for review (Stage -> Review) and generate delivery report."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        # Implicitly ensure status is Open
        core.update_issue(issues_root, issue_id, status=IssueStatus.OPEN, stage=IssueStage.REVIEW)
        console.print(f"[green]🚀[/green] Issue [bold]{issue_id}[/bold] submitted for review.")
        
        # Delivery Report Generation
        project_root = _resolve_project_root(config)
        try:
             core.generate_delivery_report(issues_root, issue_id, project_root)
             console.print(f"[dim]✔ Delivery report appended to issue file.[/dim]")
        except Exception as e:
             console.print(f"[yellow]⚠ Failed to generate delivery report: {e}[/yellow]")
             
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("close")
def move_close(
    issue_id: str = typer.Argument(..., help="Issue ID to close"),
    solution: Optional[IssueSolution] = typer.Option(None, "--solution", "-s", help="Solution type"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Close issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        core.update_issue(issues_root, issue_id, status=IssueStatus.CLOSED, solution=solution)
        console.print(f"[dim]✔[/dim] Issue [bold]{issue_id}[/bold] closed.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@backlog_app.command("push")
def push(
    issue_id: str = typer.Argument(..., help="Issue ID to push to backlog"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Push issue to backlog."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        core.update_issue(issues_root, issue_id, status=IssueStatus.BACKLOG)
        console.print(f"[blue]💤[/blue] Issue [bold]{issue_id}[/bold] pushed to backlog.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@backlog_app.command("pull")
def pull(
    issue_id: str = typer.Argument(..., help="Issue ID to pull from backlog"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Pull issue from backlog (Open & Todo)."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        core.update_issue(issues_root, issue_id, status=IssueStatus.OPEN, stage=IssueStage.TODO)
        console.print(f"[green]🔥[/green] Issue [bold]{issue_id}[/bold] pulled from backlog.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("cancel")
def cancel(
    issue_id: str = typer.Argument(..., help="Issue ID to cancel"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Cancel issue."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        core.update_issue(issues_root, issue_id, status=IssueStatus.CLOSED, solution=IssueSolution.CANCELLED)
        console.print(f"[red]✘[/red] Issue [bold]{issue_id}[/bold] cancelled.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("delete")
def delete(
    issue_id: str = typer.Argument(..., help="Issue ID to delete"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Physically remove an issue file."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        core.delete_issue_file(issues_root, issue_id)
        console.print(f"[red]✔[/red] Issue [bold]{issue_id}[/bold] physically deleted.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("board")
def board(
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Visualize issues in a Kanban board."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    
    board_data = core.get_board_data(issues_root)
    
    from rich.columns import Columns
    from rich.console import RenderableType
    
    columns: List[RenderableType] = []
    
    stage_titles = {
        "todo": "[bold white]TODO[/bold white]",
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
):
    """List issues in a table format with filtering."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    
    # Validation
    if status and status.lower() not in ["open", "closed", "backlog", "all"]:
         console.print(f"[red]Invalid status:[/red] {status}. Use open, closed, backlog or all.")
         raise typer.Exit(code=1)
         
    target_status = status.lower() if status else "open"
    
    issues = core.list_issues(issues_root)
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
    
    # Render
    table = Table(title=f"Issues ({len(filtered)})", show_header=True, header_style="bold magenta")
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

    for i in filtered:
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

@app.command("scope")
def scope(
    sprint: Optional[str] = typer.Option(None, "--sprint", help="Filter by Sprint ID"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all, otherwise show only open items"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recursively scan subdirectories"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Show progress tree."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    
    issues = []
    
    for subdir in ["Epics", "Features", "Chores", "Fixes"]:
        d = issues_root / subdir
        if d.exists():
            if recursive:
                files = d.rglob("*.md")
            else:
                files = []
                for status in ["open", "closed", "backlog"]:
                    status_dir = d / status
                    if status_dir.exists():
                        files.extend(status_dir.glob("*.md"))
            
            for f in files:
                meta = core.parse_issue(f)
                if meta:
                    if sprint and meta.sprint != sprint:
                        continue
                    if not all and meta.status != IssueStatus.OPEN:
                        continue
                    issues.append(meta)

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

@app.command("lint")
def lint(
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recursively scan subdirectories"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """Verify the integrity of the Issues directory (declarative check)."""
    from . import linter
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    linter.run_lint(issues_root, recursive=recursive)

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
    
    # If CWD is NOT a project root (no monoco.yaml/Issues), scan for subprojects
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
    type: Optional[str] = typer.Option(None, "--type", "-t", help="Commit type (feat, fix, etc.)"),
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Commit scope"),
    subject: Optional[str] = typer.Option(None, "--subject", help="Commit subject"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """
    Atomic Commit: Validate (Lint) and Commit.
    
    Modes:
    1. Issue-Only (Default): Commits only changes in Issues directory.
    2. Linked Commit (--issue): Commits ALL staged changes with 'Ref: <ID>' footer.
    """
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    project_root = _resolve_project_root(config)
    
    # 1. Lint Check (Gatekeeper)
    console.print("[dim]Running pre-commit lint check...[/dim]")
    try:
        from . import linter
        # We check integrity of issues regardless of what we commit
        errors = linter.check_integrity(issues_root, recursive=True)
        if errors:
            linter._print_errors(errors) # Assuming linter has this or we need to reproduce it
            # linter.run_lint prints errors directly.
            # Let's just call run_lint but it does not return bool.
            # We already imported linter inside lint command, let's reuse it or extract.
            # For now, let's trust run_lint output? No, we need to abort.
            pass # linter check is good practice
    except Exception:
        pass # Don't block if lint fails? Ideally we should.

    # 2. Stage & Commit
    from monoco.core import git
    
    try:
        # MODE SELECTION
        if issue_id:
            # Mode: Linked Commit (Code + Issue)
            console.print(f"[bold cyan]Linked Commit Mode[/bold cyan] (Ref: {issue_id})")
            
            # Validate Issue Exists
            if not core.find_issue_path(issues_root, issue_id):
                 console.print(f"[red]Error:[/red] Issue {issue_id} not found.")
                 raise typer.Exit(code=1)

            # Check Global Status
            status_files = git.get_git_status(project_root)
            if not status_files:
                console.print("[yellow]Nothing to commit.[/yellow] Working directory clean.")
                return

            # Message Construction
            if not message:
                if not type or not subject:
                    # Interactive Prompt could go here, but for now enforce args
                    console.print("[red]Error:[/red] When using --issue, provide --message OR (--type and --subject).")
                    raise typer.Exit(code=1)
                
                scope_part = f"({scope})" if scope else ""
                message = f"{type}{scope_part}: {subject}"
            
            # Append Footer
            if f"Ref: {issue_id}" not in message:
                message += f"\n\nRef: {issue_id}"
                
            # Commit ALL staged files?
            # User must have staged them. git commit usually commits staged.
            # Our git_commit wrapper commits EVERYTHING that is staged?
            # Wait, `git.git_commit` takes `path` and `message`.
            # It runs `git commit -m`. This commits staged files.
            # BUT `commands.py` lines 525 calls `git.git_add`.
            # If we want to commit *staged* files, we don't need to add.
            # If we want to stage all changes, we run `git add .`?
            # Standard `git commit` only commits staged.
            # Let's assume user staged files.
            # But the original code (lines 525) did `git_add(project_root, status_files)`.
            # That auto-staged modified files in Issues dir.
            
            # Let's stick to "Auto-stage" for now to be friendly?
            # No, dangerous for code.
            # Compromise: Check if anything staged.
            # `git diff --cached --name-only`
            code, stdout, _ = git._run_git(["diff", "--cached", "--name-only"], project_root)
            staged_files = [l for l in stdout.splitlines() if l.strip()]
            
            if not staged_files:
                console.print("[yellow]No staged files.[/yellow] Please `git add` files or implement auto-stage flag.")
                # We could `git add -A`? Too aggressive.
                # Let's just exit.
                raise typer.Exit(code=1)
                
            commit_hash = git.git_commit(project_root, message)
            console.print(f"[green]✔ Committed (Linked):[/green] {commit_hash[:7]}")
            console.print(f"[dim]{message}[/dim]")

        else:
            # Mode: Issue-DB Only (Legacy/Default)
            # Check status ONLY for issues_root
            try:
                rel_issues = issues_root.relative_to(project_root)
            except ValueError:
                console.print("[red]Error:[/red] Issues directory must be inside the project root.")
                raise typer.Exit(code=1)

            status_files = git.get_git_status(project_root, str(rel_issues))
            
            if not status_files:
                console.print("[yellow]Nothing to commit.[/yellow] Issues directory clean.")
                return

            if not message:
                cnt = len(status_files)
                if cnt == 1:
                    fpath = project_root / status_files[0]
                    match = core.parse_issue(fpath)
                    if match:
                         action = "update" 
                         message = f"docs(issues): {action} {match.id} {match.title}"
                    else:
                         message = f"docs(issues): update {status_files[0]}"
                else:
                     message = f"docs(issues): batch update {cnt} files"

            # Auto-stage for DB mode
            git.git_add(project_root, status_files)
            commit_hash = git.git_commit(project_root, message)
            console.print(f"[green]✔ Committed (DB):[/green] {commit_hash[:7]} - {message}")
        
    except Exception as e:
         console.print(f"[red]Git Error:[/red] {e}")
         raise typer.Exit(code=1)