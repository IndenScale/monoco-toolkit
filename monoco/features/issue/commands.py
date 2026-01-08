import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table

from monoco.core.config import get_config
from monoco.core.output import print_output
from .models import IssueType, IssueStatus, IssueSolution
from . import core

app = typer.Typer(help="Agent-Native Issue Management.")
console = Console()

@app.command("create")
def create(
    type: IssueType = typer.Argument(..., help="Issue type (epic, story, task, bug)"),
    title: str = typer.Option(..., "--title", "-t", help="Issue title"),
    parent: Optional[str] = typer.Option(None, "--parent", "-p", help="Parent Issue ID"),
    is_backlog: bool = typer.Option(False, "--backlog", help="Create as backlog item"),
):
    """Create a new issue."""
    config = get_config()
    root_dir = Path(config.paths.root)
    status = IssueStatus.BACKLOG if is_backlog else IssueStatus.OPEN
    
    if parent:
        parent_path = core.find_issue_path(root_dir, parent)
        if not parent_path:
            console.print(f"[red]✘ Error:[/red] Parent issue {parent} not found.")
            raise typer.Exit(code=1)

    issue_id = core.create_issue_file(root_dir, type, title, parent, status=status)
    console.print(f"[green]✔[/green] Created [bold]{issue_id}[/bold] in status [cyan]{status.value}[/cyan].")

@app.command("open")
def move_open(issue_id: str = typer.Argument(..., help="Issue ID to open")):
    """Move issue to open status."""
    config = get_config()
    root_dir = Path(config.paths.root)
    try:
        core.update_issue_status(root_dir, issue_id, IssueStatus.OPEN)
        console.print(f"[green]▶[/green] Issue [bold]{issue_id}[/bold] moved to open.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("close")
def move_close(
    issue_id: str = typer.Argument(..., help="Issue ID to close"),
    solution: Optional[IssueSolution] = typer.Option(None, "--solution", "-s", help="Solution type")
):
    """Close issue."""
    config = get_config()
    root_dir = Path(config.paths.root)
    try:
        core.update_issue_status(root_dir, issue_id, IssueStatus.CLOSED, solution=solution)
        console.print(f"[dim]✔[/dim] Issue [bold]{issue_id}[/bold] closed.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("backlog")
def move_backlog(issue_id: str = typer.Argument(..., help="Issue ID to backlog")):
    """Move issue to backlog status."""
    config = get_config()
    root_dir = Path(config.paths.root)
    try:
        core.update_issue_status(root_dir, issue_id, IssueStatus.BACKLOG)
        console.print(f"[blue]💤[/blue] Issue [bold]{issue_id}[/bold] moved to backlog.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("cancel")
def cancel(issue_id: str = typer.Argument(..., help="Issue ID to cancel")):
    """Cancel issue."""
    config = get_config()
    root_dir = Path(config.paths.root)
    try:
        core.update_issue_status(root_dir, issue_id, IssueStatus.CLOSED, solution=IssueSolution.CANCELLED)
        console.print(f"[red]✘[/red] Issue [bold]{issue_id}[/bold] cancelled.")
    except Exception as e:
        console.print(f"[red]✘ Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("scope")
def scope(
    sprint: Optional[str] = typer.Option(None, "--sprint", help="Filter by Sprint ID"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all, otherwise show only open items")
):
    """Show progress tree."""
    config = get_config()
    root_dir = Path(config.paths.root)
    
    issues = []
    base_issue_dir = root_dir / "ISSUES"
    for subdir in ["EPICS", "STORIES", "TASKS", "BUGS"]:
        d = base_issue_dir / subdir
        if d.exists():
            for f in d.rglob("*.md"):
                meta = core.parse_issue(f)
                if meta:
                    if sprint and meta.sprint != sprint:
                        continue
                    if not all and meta.status != IssueStatus.OPEN:
                        continue
                    issues.append(meta)

    tree = Tree(f"[bold blue]Monoco Issue Scope[/bold blue]")
    epics = sorted([i for i in issues if i.type == IssueType.EPIC], key=lambda x: x.id)
    stories = [i for i in issues if i.type == IssueType.STORY]
    tasks = [i for i in issues if i.type in [IssueType.TASK, IssueType.BUG]]

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
def lint():
    """Verify the integrity of the ISSUES directory (declarative check)."""
    config = get_config()
    root_dir = Path(config.paths.root)
    base_issue_dir = root_dir / "ISSUES"
    
    errors = []
    all_issue_ids = set()
    all_issues = []

    # 1. Collection
    for subdir in ["EPICS", "STORIES", "TASKS", "BUGS"]:
        d = base_issue_dir / subdir
        if d.exists():
            for f in d.rglob("*.md"):
                meta = core.parse_issue(f)
                if meta:
                    all_issues.append((f, meta))
                    if meta.id in all_issue_ids:
                        errors.append(f"[red]ID Collision:[/red] {meta.id} found in multiple files.")
                    all_issue_ids.add(meta.id)

    # 2. Validation
    for path, meta in all_issues:
        # A. Directory/Status Consistency
        expected_subdir = meta.status.value
        if path.parent.name != expected_subdir:
            errors.append(f"[yellow]Placement Error:[/yellow] {meta.id} has status [cyan]{meta.status.value}[/cyan] but is in [dim]{path.parent.name}/[/dim]")
        
        # B. Solution Compliance
        if meta.status == IssueStatus.CLOSED and not meta.solution:
            errors.append(f"[red]Solution Missing:[/red] {meta.id} is closed but has no [dim]solution[/dim] field.")
            
        # C. Link Integrity
        if meta.parent:
            if meta.parent not in all_issue_ids:
                errors.append(f"[red]Broken Link:[/red] {meta.id} refers to non-existent parent [bold]{meta.parent}[/bold].")

    # 3. Report
    if not errors:
        console.print("[green]✔[/green] Issue integrity check passed. No issues found.")
    else:
        table = Table(title="Issue Integrity Issues", show_header=False, border_style="red")
        for err in errors:
            table.add_row(err)
        console.print(table)
        raise typer.Exit(code=1)
