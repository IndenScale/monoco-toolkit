from typing import List, Optional, Tuple, Set
from pathlib import Path
from rich.console import Console
from rich.table import Table
import typer

from . import core
from .models import IssueStatus, IssueStage

console = Console()


def validate_issue(path: Path, meta: core.IssueMetadata, all_issue_ids: Set[str] = set()) -> List[str]:
    """
    Validate a single issue's integrity.
    """
    errors = []
    
    # A. Directory/Status Consistency
    expected_status = meta.status.value
    path_parts = path.parts
    # We might be validating a temp file, so we skip path check if it's not in the tree?
    # Or strict check? For "Safe Edit", the file might be in a temp dir. 
    # So we probably only care about content/metadata integrity.
    
    # But wait, if we overwrite the file, it MUST be valid.
    # Let's assume the validation is about the content itself (metadata logic).
    
    # B. Solution Compliance
    if meta.status == IssueStatus.CLOSED and not meta.solution:
        errors.append(f"[red]Solution Missing:[/red] {meta.id} is closed but has no [dim]solution[/dim] field.")
        
    # C. Link Integrity
    if meta.parent:
        if all_issue_ids and meta.parent not in all_issue_ids:
             errors.append(f"[red]Broken Link:[/red] {meta.id} refers to non-existent parent [bold]{meta.parent}[/bold].")

    # D. Lifecycle Guard (Backlog)
    if meta.status == IssueStatus.BACKLOG and meta.stage != IssueStage.FREEZED:
        errors.append(f"[red]Lifecycle Error:[/red] {meta.id} is backlog but stage is not [bold]freezed[/bold] (found: {meta.stage}).")

    return errors

def check_integrity(issues_root: Path, recursive: bool = False) -> List[str]:
    """
    Verify the integrity of the Issues directory.
    Returns a list of error messages.
    """
    errors = []
    all_issue_ids = set()
    all_issues = []

    # 1. Collection
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
                    all_issues.append((f, meta))
                    if meta.id in all_issue_ids:
                        errors.append(f"[red]ID Collision:[/red] {meta.id} found in multiple files.")
                    all_issue_ids.add(meta.id)

    # 2. Validation
    for path, meta in all_issues:
        # A. Directory/Status Consistency (Only check this for files in the tree)
        expected_status = meta.status.value
        path_parts = path.parts
        if expected_status not in path_parts:
             errors.append(f"[yellow]Placement Error:[/yellow] {meta.id} has status [cyan]{expected_status}[/cyan] but is not under a [dim]{expected_status}/[/dim] directory.")
        
        # Reuse common logic
        errors.extend(validate_issue(path, meta, all_issue_ids))

    return errors

def run_lint(issues_root: Path, recursive: bool = False):
    errors = check_integrity(issues_root, recursive)
    
    if not errors:
        console.print("[green]✔[/green] Issue integrity check passed. No integrity errors found.")
    else:
        table = Table(title="Issue Integrity Issues", show_header=False, border_style="red")
        for err in errors:
            table.add_row(err)
        console.print(table)
        raise typer.Exit(code=1)
