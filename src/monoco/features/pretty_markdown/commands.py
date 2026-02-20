"""
CLI commands for pretty-markdown feature.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .core import (
    sync_config,
    check_config,
    enable_hook,
    disable_hook,
    find_project_root,
)

app = typer.Typer(help="Markdown formatting and linting utilities")
console = Console()


@app.command("sync")
def sync_cmd(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration files",
    ),
    templates: Optional[list[str]] = typer.Option(
        None,
        "--template",
        "-t",
        help="Specific templates to sync (prettier, markdownlint)",
    ),
    project_root: Path = typer.Option(
        ".",
        "--project",
        "-p",
        help="Project root directory",
    ),
):
    """Sync prettier and markdownlint configuration templates to the project."""
    root = Path(project_root).resolve()
    if not (root / ".monoco").exists():
        console.print(f"[red]Error: Not a Monoco project (no .monoco directory)[/red]")
        raise typer.Exit(1)
    
    results = sync_config(
        project_root=root,
        force=force,
        templates=templates,
    )
    
    # Display results
    if results["synced"]:
        console.print(f"[green]✓ Synced {len(results['synced'])} file(s):[/green]")
        for f in results["synced"]:
            console.print(f"  • {f}")
    
    if results["skipped"]:
        console.print(f"[yellow]⚠ Skipped {len(results['skipped'])} file(s) (use --force to overwrite):[/yellow]")
        for f in results["skipped"]:
            console.print(f"  • {f}")
    
    if results["errors"]:
        console.print(f"[red]✗ Errors ({len(results['errors'])}):[/red]")
        for e in results["errors"]:
            console.print(f"  • {e}")
        raise typer.Exit(1)
    
    if not results["synced"] and not results["skipped"]:
        console.print("[dim]No files to sync[/dim]")
    elif results["synced"]:
        console.print(f"\n[green]Configuration synced successfully![/green]")
        console.print("[dim]Run 'npm install' to install prettier if needed[/dim]")


@app.command("check")
def check_cmd(
    project_root: Path = typer.Option(
        ".",
        "--project",
        "-p",
        help="Project root directory",
    ),
):
    """Check if project configuration matches Monoco templates."""
    root = Path(project_root).resolve()
    if not (root / ".monoco").exists():
        console.print(f"[red]Error: Not a Monoco project (no .monoco directory)[/red]")
        raise typer.Exit(1)
    
    results = check_config(project_root=root)
    
    # Display results in a table
    table = Table(title="Configuration Status")
    table.add_column("Status", style="bold")
    table.add_column("Files")
    
    if results["consistent"]:
        table.add_row(
            "[green]✓ Consistent[/green]",
            "\n".join(results["consistent"]) or "None"
        )
    
    if results["different"]:
        table.add_row(
            "[yellow]≠ Different[/yellow]",
            "\n".join(results["different"]) or "None"
        )
    
    if results["missing"]:
        table.add_row(
            "[red]✗ Missing[/red]",
            "\n".join(results["missing"]) or "None"
        )
    
    console.print(table)
    
    # Summary
    if results["different"] or results["missing"]:
        console.print(f"\n[yellow]Run 'monoco pretty-markdown sync' to fix configuration[/yellow]")
        raise typer.Exit(1)
    else:
        console.print(f"\n[green]All configuration files are up to date![/green]")


@app.command("enable")
def enable_cmd(
    project_root: Path = typer.Option(
        ".",
        "--project",
        "-p",
        help="Project root directory",
    ),
):
    """Enable the pretty-markdown auto-formatting hook."""
    root = Path(project_root).resolve()
    if not (root / ".monoco").exists():
        console.print(f"[red]Error: Not a Monoco project (no .monoco directory)[/red]")
        raise typer.Exit(1)
    
    if enable_hook(project_root=root):
        console.print("[green]✓ Pretty-markdown hook enabled[/green]")
        console.print("[dim]Markdown files will be linted after save[/dim]")
    else:
        console.print("[red]✗ Failed to enable hook[/red]")
        raise typer.Exit(1)


@app.command("disable")
def disable_cmd(
    project_root: Path = typer.Option(
        ".",
        "--project",
        "-p",
        help="Project root directory",
    ),
):
    """Disable the pretty-markdown auto-formatting hook."""
    root = Path(project_root).resolve()
    if not (root / ".monoco").exists():
        console.print(f"[red]Error: Not a Monoco project (no .monoco directory)[/red]")
        raise typer.Exit(1)
    
    if disable_hook(project_root=root):
        console.print("[green]✓ Pretty-markdown hook disabled[/green]")
    else:
        console.print("[red]✗ Failed to disable hook[/red]")
        raise typer.Exit(1)


@app.command("status")
def status_cmd(
    project_root: Path = typer.Option(
        ".",
        "--project",
        "-p",
        help="Project root directory",
    ),
):
    """Show pretty-markdown status."""
    root = Path(project_root).resolve()
    if not (root / ".monoco").exists():
        console.print(f"[red]Error: Not a Monoco project (no .monoco directory)[/red]")
        raise typer.Exit(1)
    
    # Check hook status
    hook_enabled = (root / ".monoco" / "hooks" / "pretty-markdown.sh").exists()
    
    # Check config status
    config_results = check_config(project_root=root)
    config_ok = not config_results["different"] and not config_results["missing"]
    
    # Display status
    table = Table(title="Pretty Markdown Status")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    
    hook_status = "[green]✓ Enabled[/green]" if hook_enabled else "[dim]Disabled[/dim]"
    config_status = "[green]✓ Synced[/green]" if config_ok else "[yellow]≠ Out of sync[/yellow]"
    
    table.add_row("Auto-formatting Hook", hook_status)
    table.add_row("Configuration", config_status)
    
    console.print(table)
    
    if not hook_enabled:
        console.print(f"\n[dim]Run 'monoco pretty-markdown enable' to enable auto-formatting[/dim]")
    
    if not config_ok:
        console.print(f"\n[dim]Run 'monoco pretty-markdown sync' to sync configuration[/dim]")
