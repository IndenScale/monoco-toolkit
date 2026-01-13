from typing import List, Optional, Tuple, Set
from pathlib import Path
from rich.console import Console
from rich.table import Table
import typer

from . import core
from .models import IssueStatus, IssueStage

console = Console()


def validate_issue(path: Path, meta: core.IssueMetadata, all_issue_ids: Set[str] = set(), issues_root: Optional[Path] = None) -> List[str]:
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
             # Check workspace (fallback)
             found = False
             if issues_root:
                 if core.find_issue_path(issues_root, meta.parent):
                     found = True
             
             if not found:
                 errors.append(f"[red]Broken Link:[/red] {meta.id} refers to non-existent parent [bold]{meta.parent}[/bold].")

    # D. Lifecycle Guard (Backlog)
    if meta.status == IssueStatus.BACKLOG and meta.stage != IssueStage.FREEZED:
        errors.append(f"[red]Lifecycle Error:[/red] {meta.id} is backlog but stage is not [bold]freezed[/bold] (found: {meta.stage}).")

    return errors

def check_integrity(issues_root: Path, recursive: bool = False) -> List[str]:
    """
    Verify the integrity of the Issues directory.
    Returns a list of error messages.
    
    If recursive=True, performs workspace-level validation including:
    - Cross-project ID collision detection
    - Cross-project UID collision detection
    """
    errors = []
    all_issue_ids = set()  # For parent reference validation (includes namespaced IDs)
    id_to_projects = {}  # local_id -> [(project_name, meta, file)]
    all_uids = {}  # uid -> (project, issue_id)
    all_issues = []
    
    # Helper to collect issues from a project
    def collect_project_issues(project_issues_root: Path, project_name: str = "local"):
        project_issues = []
        for subdir in ["Epics", "Features", "Chores", "Fixes"]:
            d = project_issues_root / subdir
            if d.exists():
                files = []
                for status in ["open", "closed", "backlog"]:
                    status_dir = d / status
                    if status_dir.exists():
                        files.extend(status_dir.rglob("*.md"))

                for f in files:
                    meta = core.parse_issue(f)
                    if meta:
                        local_id = meta.id
                        full_id = f"{project_name}::{local_id}" if project_name != "local" else local_id
                        
                        # Track ID occurrences per project
                        if local_id not in id_to_projects:
                            id_to_projects[local_id] = []
                        id_to_projects[local_id].append((project_name, meta, f))
                        
                        # Add IDs for reference validation
                        all_issue_ids.add(local_id)  # Local ID
                        if project_name != "local":
                            all_issue_ids.add(full_id)  # Namespaced ID
                        
                        # Check UID collision (if UID exists)
                        if meta.uid:
                            if meta.uid in all_uids:
                                existing_project, existing_id = all_uids[meta.uid]
                                errors.append(
                                    f"[red]UID Collision:[/red] UID {meta.uid} is duplicated.\n"
                                    f"  - {existing_project}::{existing_id}\n"
                                    f"  - {project_name}::{local_id}"
                                )
                            else:
                                all_uids[meta.uid] = (project_name, local_id)
                        
                        project_issues.append((f, meta, project_name))
        return project_issues

    # 1. Collect local issues
    all_issues.extend(collect_project_issues(issues_root, "local"))

    # 2. If recursive, collect workspace member issues
    if recursive:
        try:
            from monoco.core.config import get_config
            project_root = issues_root.parent
            conf = get_config(str(project_root))
            
            for member_name, rel_path in conf.project.members.items():
                member_root = (project_root / rel_path).resolve()
                member_issues_dir = member_root / "Issues"
                
                if member_issues_dir.exists():
                    all_issues.extend(collect_project_issues(member_issues_dir, member_name))
        except Exception as e:
            # Fail gracefully if workspace config is missing
            pass

    # 3. Check for ID collisions within same project
    for local_id, occurrences in id_to_projects.items():
        # Group by project
        projects_with_id = {}
        for project_name, meta, f in occurrences:
            if project_name not in projects_with_id:
                projects_with_id[project_name] = []
            projects_with_id[project_name].append((meta, f))
        
        # Check for duplicates within same project
        for project_name, metas in projects_with_id.items():
            if len(metas) > 1:
                # Same ID appears multiple times in same project - this is an error
                error_msg = f"[red]ID Collision:[/red] {local_id} appears {len(metas)} times in project '{project_name}':\n"
                for idx, (meta, f) in enumerate(metas, 1):
                    error_msg += f"  {idx}. uid: {meta.uid or 'N/A'} | created: {meta.created_at} | stage: {meta.stage} | status: {meta.status.value}\n"
                error_msg += f"  [yellow]→ Action:[/yellow] Remove duplicate or use 'monoco issue move --to <target> --renumber' to resolve."
                errors.append(error_msg)

    # 4. Validation
    for path, meta, project_name in all_issues:
        # A. Directory/Status Consistency (Only check this for files in the tree)
        expected_status = meta.status.value
        path_parts = path.parts
        if expected_status not in path_parts:
             errors.append(f"[yellow]Placement Error:[/yellow] {meta.id} has status [cyan]{expected_status}[/cyan] but is not under a [dim]{expected_status}/[/dim] directory.")
        
        # Reuse common logic
        errors.extend(validate_issue(path, meta, all_issue_ids, issues_root))

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
