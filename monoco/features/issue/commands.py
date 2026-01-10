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
    dependencies: List[str] = typer.Option([], "--dependency", "-d", help="Issue dependency ID(s)"),
    related: List[str] = typer.Option([], "--related", "-r", help="Related Issue ID(s)"),
    subdir: Optional[str] = typer.Option(None, "--subdir", "-s", help="Subdirectory for organization (e.g. 'Backend/Auth')"),
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

    issue = core.create_issue_file(issues_root, type, title, parent, status=status, dependencies=dependencies, related=related, subdir=subdir)
    console.print(f"[green]✔[/green] Created [bold]{issue.id}[/bold] in status [cyan]{issue.status.value}[/cyan].")

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
    """Submit issue for review (Stage -> Review)."""
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    try:
        # Implicitly ensure status is Open
        core.update_issue(issues_root, issue_id, status=IssueStatus.OPEN, stage=IssueStage.REVIEW)
        console.print(f"[green]🚀[/green] Issue [bold]{issue_id}[/bold] submitted for review.")
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
    Priority:
    1. CLI Argument (--root)
    2. Config (paths.issues) - can be absolute or relative to project root
    3. Default (Issues) - handled by config default
    """
    if cli_root:
        return Path(cli_root).resolve()
    
    # Config path handling
    config_issues_path = Path(config.paths.issues)
    if config_issues_path.is_absolute():
        return config_issues_path
    else:
        return (Path(config.paths.root) / config_issues_path).resolve()
@app.command("commit")
def commit(
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Commit message"),
    root: Optional[str] = typer.Option(None, "--root", help="Override issues root directory"),
):
    """
    Atomic Commit: Validate (Lint) and Commit changes in the Issues directory only.
    Use this to persist your work.
    """
    config = get_config()
    issues_root = _resolve_issues_root(config, root)
    
    # 1. Lint Check (Gatekeeper)
    console.print("[dim]Running pre-commit lint check...[/dim]")
    try:
        # We reuse the lint logic function directly (refactor if needed to return bool instead of exit)
        try:
           lint(recursive=True, root=str(issues_root))
        except typer.Exit as e:
           if e.exit_code != 0:
               console.print("[red]⛔ Commit Aborted:[/red] Lint check failed.")
               raise typer.Exit(code=1)

    except Exception as e:
         console.print(f"[red]Error during lint:[/red] {e}")
         raise typer.Exit(code=1)

    # 2. Stage & Commit
    # Note: We need to import git module correctly, usually from core or similar
    # Assuming core.git is available because we will add 'import monoco.core.git' or similar
    # But since we only have 'from . import core' and core is 'monoco.features.issue.core',
    # we need to ensure 'monoco.core.git' is accessible.
    
    # Let's import it dynamically or ensure it's in the file imports
    from monoco.core import git
    
    try:
        # Check status ONLY for issues_root
        # Path.relative_to might fail if issues_root is not subpath of repo root
        # Assuming repo root is parent of issues_root for now or we run from cwd
        repo_root = issues_root.parent.parent # Standard guess: Issues/../.. -> ROOT
        # Better: use git root detection
        
        # Simple fallback: Use current working directory if it is a git repo
        # Or traverse up to find .git
        # For this MVP, let's assume CWD which usually is project root
        project_root = Path(config.paths.root).resolve()
        
        # Calculate relative path of issues dir to project root
        try:
            rel_issues = issues_root.relative_to(project_root)
        except ValueError:
            # Issues dir is outside project root?
            console.print("[red]Error:[/red] Issues directory must be inside the project root for git tracking.")
            raise typer.Exit(code=1)

        status_files = git.get_git_status(project_root, str(rel_issues))
        
        if not status_files:
            console.print("[yellow]Nothing to commit.[/yellow] Working directory clean.")
            return

        if not message:
            # 3. Message Generation logic
            cnt = len(status_files)
            if cnt == 1:
                fpath = project_root / status_files[0]
                # Try parse
                match = core.parse_issue(fpath) # Note: parse_issue expects Path
                if match:
                     # Detect if new file?
                     # Naive check
                     action = "update" 
                     message = f"docs(issues): {action} {match.id} {match.title}"
                else:
                     message = f"docs(issues): update {status_files[0]}"
            else:
                 message = f"docs(issues): batch update {cnt} files"

        git.git_add(project_root, status_files)
        commit_hash = git.git_commit(project_root, message)
        console.print(f"[green]✔ Committed:[/green] {commit_hash[:7]} - {message}")
        
    except Exception as e:
         console.print(f"[red]Git Error:[/red] {e}")
         raise typer.Exit(code=1)
