from typing import List, Optional, Set, Tuple
from pathlib import Path
from rich.console import Console
from rich.table import Table
import typer
import re

from . import core
from .validator import IssueValidator
from monoco.core.lsp import Diagnostic, DiagnosticSeverity

console = Console()

def check_integrity(issues_root: Path, recursive: bool = False) -> List[Diagnostic]:
    """
    Verify the integrity of the Issues directory using LSP Validator.
    """
    diagnostics = []
    validator = IssueValidator(issues_root)
    
    all_issue_ids = set()
    all_issues = []
    
    # 1. Collection Phase (Build Index)
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
                        full_id = f"{project_name}::{local_id}"
                        
                        all_issue_ids.add(local_id)
                        all_issue_ids.add(full_id)
                        
                        project_issues.append((f, meta))
        return project_issues

    from monoco.core.config import get_config
    conf = get_config(str(issues_root.parent))
    
    # Identify local project name
    local_project_name = "local"
    if conf and conf.project and conf.project.name:
        local_project_name = conf.project.name.lower()

    # Find Topmost Workspace Root
    workspace_root = issues_root.parent
    for parent in [workspace_root] + list(workspace_root.parents):
        if (parent / ".monoco" / "workspace.yaml").exists() or (parent / ".monoco" / "project.yaml").exists():
            workspace_root = parent
            
    # Collect from local issues_root
    all_issues.extend(collect_project_issues(issues_root, local_project_name))
    
    if recursive:
        try:
            # Re-read config from workspace root to get all members
            ws_conf = get_config(str(workspace_root))
            
            # Index Root project if different from current
            if workspace_root != issues_root.parent:
                root_issues_dir = workspace_root / "Issues"
                if root_issues_dir.exists():
                    all_issues.extend(collect_project_issues(root_issues_dir, ws_conf.project.name.lower()))

            # Index all members
            for member_name, rel_path in ws_conf.project.members.items():
                member_root = (workspace_root / rel_path).resolve()
                member_issues_dir = member_root / "Issues"
                if member_issues_dir.exists() and member_issues_dir != issues_root:
                    all_issues.extend(collect_project_issues(member_issues_dir, member_name.lower()))
        except Exception:
            pass

    # 2. Validation Phase
    for path, meta in all_issues:
        content = path.read_text() # Re-read content for validation
        
        # A. Run Core Validator
        file_diagnostics = validator.validate(meta, content, all_issue_ids)
        
        # Add context to diagnostics (Path)
        for d in file_diagnostics:
             d.source = f"{meta.id}" # Use ID as source context
             d.data = {'path': path} # Attach path for potential fixers
             diagnostics.append(d)
             
    return diagnostics


def run_lint(issues_root: Path, recursive: bool = False, fix: bool = False, format: str = "table", file_path: Optional[str] = None):
    """
    Run lint with optional auto-fix and format selection.
    
    Args:
        issues_root: Root directory of issues
        recursive: Recursively scan workspace members
        fix: Apply auto-fixes
        format: Output format (table, json)
        file_path: Optional path to a single file to validate (LSP mode)
    """
    # Single-file mode (for LSP integration)
    if file_path:
        file = Path(file_path).resolve()
        if not file.exists():
            console.print(f"[red]Error:[/red] File not found: {file_path}")
            raise typer.Exit(code=1)
        
        # Parse and validate single file
        try:
            meta = core.parse_issue(file)
            if not meta:
                console.print(f"[red]Error:[/red] Failed to parse issue metadata from {file_path}")
                raise typer.Exit(code=1)
            
            content = file.read_text()
            validator = IssueValidator(issues_root)
            
            # For single-file mode, we need to build a minimal index
            # We'll scan the entire workspace to get all issue IDs for reference validation
            all_issue_ids = set()
            for subdir in ["Epics", "Features", "Chores", "Fixes"]:
                d = issues_root / subdir
                if d.exists():
                    for status in ["open", "closed", "backlog"]:
                        status_dir = d / status
                        if status_dir.exists():
                            for f in status_dir.rglob("*.md"):
                                try:
                                    m = core.parse_issue(f)
                                    if m:
                                        all_issue_ids.add(m.id)
                                except Exception:
                                    pass
            
            diagnostics = validator.validate(meta, content, all_issue_ids)
            
            # Add context
            for d in diagnostics:
                d.source = meta.id
                d.data = {'path': file}
                
        except Exception as e:
            console.print(f"[red]Error:[/red] Validation failed: {e}")
            raise typer.Exit(code=1)
    else:
        # Full workspace scan mode
        diagnostics = check_integrity(issues_root, recursive)
    
    # Filter only Warnings and Errors
    issues = [d for d in diagnostics if d.severity <= DiagnosticSeverity.Warning]
    
    if fix:
        fixed_count = 0
        console.print("[dim]Attempting auto-fixes...[/dim]")
        
        # We must track processed paths to avoid redundant writes if multiple errors exist
        processed_paths = set()
        
        for d in issues:
            path = d.data.get('path')
            if not path: continue
            
            # Read fresh content iteration
            pass

        # Group diagnostics by file path
        from collections import defaultdict
        file_diags = defaultdict(list)
        for d in issues:
            if d.data.get('path'):
                file_diags[d.data['path']].append(d)
        
        for path, diags in file_diags.items():
            try:
                content = path.read_text()
                new_content = content
                has_changes = False
                
                # Parse meta once for the file
                try:
                    meta = core.parse_issue(path)
                except Exception:
                    console.print(f"[yellow]Skipping fix for {path.name}: Cannot parse metadata[/yellow]")
                    continue

                # Apply fixes for this file
                for d in diags:
                    if "Structure Error" in d.message:
                        expected_header = f"## {meta.id}: {meta.title}"
                        
                        # Check if strictly present
                        if expected_header in new_content:
                            continue
                            
                        # Strategy: Look for existing heading with same ID to replace
                        # Matches: "## ID..." or "## ID ..."
                        # Regex: ^##\s+ID\b.*$
                        # We use meta.id which is safe.
                        heading_regex = re.compile(rf"^##\s+{re.escape(meta.id)}.*$", re.MULTILINE)
                        
                        match_existing = heading_regex.search(new_content)
                        
                        if match_existing:
                            # Replace existing incorrect heading
                            # We use sub to replace just the first occurrence
                            new_content = heading_regex.sub(expected_header, new_content, count=1)
                            has_changes = True
                        else:
                            # Insert after frontmatter
                            fm_match = re.search(r"^---(.*?)---", new_content, re.DOTALL | re.MULTILINE)
                            if fm_match:
                                end_pos = fm_match.end()
                                header_block = f"\n\n{expected_header}\n"
                                new_content = new_content[:end_pos] + header_block + new_content[end_pos:].lstrip()
                                has_changes = True

                    if "Review Requirement: Missing '## Review Comments' section" in d.message:
                         if "## Review Comments" not in new_content:
                             new_content = new_content.rstrip() + "\n\n## Review Comments\n\n- [ ] Self-Review\n"
                             has_changes = True

                if has_changes:
                    path.write_text(new_content)
                    fixed_count += 1
                    console.print(f"[dim]Fixed: {path.name}[/dim]")
            except Exception as e:
                console.print(f"[red]Failed to fix {path.name}: {e}[/red]")

        console.print(f"[green]Applied auto-fixes to {fixed_count} files.[/green]")
        
        # Re-run validation to verify
        if file_path:
            # Re-validate single file
            file = Path(file_path).resolve()
            meta = core.parse_issue(file)
            content = file.read_text()
            validator = IssueValidator(issues_root)
            diagnostics = validator.validate(meta, content, all_issue_ids)
            for d in diagnostics:
                d.source = meta.id
                d.data = {'path': file}
        else:
            diagnostics = check_integrity(issues_root, recursive)
        issues = [d for d in diagnostics if d.severity <= DiagnosticSeverity.Warning]

    # Output formatting
    if format == "json":
        import json
        from pydantic import RootModel
        # Use RootModel to export a list of models
        print(RootModel(issues).model_dump_json(indent=2))
        if any(d.severity == DiagnosticSeverity.Error for d in issues):
            raise typer.Exit(code=1)
        return

    if not issues:
        console.print("[green]✔[/green] Issue integrity check passed. No integrity errors found.")
    else:
        table = Table(title="Issue Integrity Report", show_header=True, header_style="bold magenta", border_style="red")
        table.add_column("Issue", style="cyan")
        table.add_column("Severity", justify="center")
        table.add_column("Line", justify="right", style="dim")
        table.add_column("Message")
        
        for d in issues:
            sev_style = "red" if d.severity == DiagnosticSeverity.Error else "yellow"
            sev_label = "ERROR" if d.severity == DiagnosticSeverity.Error else "WARN"
            line_str = str(d.range.start.line + 1) if d.range else "-"
            table.add_row(
                d.source or "Unknown",
                f"[{sev_style}]{sev_label}[/{sev_style}]",
                line_str,
                d.message
            )
            
        console.print(table)
        
        if any(d.severity == DiagnosticSeverity.Error for d in issues):
            raise typer.Exit(code=1)

