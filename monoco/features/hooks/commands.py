"""
CLI commands for Universal Hooks management.

This module provides commands for managing Universal Hooks (Git/IDE/Agent).
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .manager import UniversalHookManager
from .models import HookType
from .dispatchers import GitHookDispatcher

app = typer.Typer(help="Universal Hooks management (Git/IDE/Agent).")
console = Console()


@app.command("scan")
def scan(
    directory: Path = typer.Option(
        ".monoco/hooks",
        "--dir",
        "-d",
        help="Directory to scan for hook scripts",
    ),
) -> None:
    """Scan for hook scripts with Front Matter metadata."""
    manager = UniversalHookManager()
    dir_path = Path(directory)

    if not dir_path.exists():
        console.print(f"[yellow]Directory not found: {dir_path}[/yellow]")
        raise typer.Exit(1)

    groups = manager.scan(dir_path)

    if not groups:
        console.print("[dim]No hooks found.[/dim]")
        return

    for key, group in groups.items():
        console.print(f"\n[bold]{key}[/bold] ({len(group.hooks)} hooks)")
        for hook in group.get_prioritized_hooks():
            console.print(f"  • {hook.script_path.name}")
            console.print(f"    Event: {hook.metadata.event}")
            if hook.metadata.matcher:
                console.print(f"    Matchers: {', '.join(hook.metadata.matcher)}")


@app.command("validate")
def validate(
    directory: Path = typer.Option(
        ".monoco/hooks",
        "--dir",
        "-d",
        help="Directory to validate hook scripts",
    ),
) -> None:
    """Validate hook metadata."""
    manager = UniversalHookManager()
    dir_path = Path(directory)

    if not dir_path.exists():
        console.print(f"[yellow]Directory not found: {dir_path}[/yellow]")
        raise typer.Exit(1)

    groups = manager.scan(dir_path)
    errors_found = False

    for key, group in groups.items():
        for hook in group.hooks:
            result = manager.validate(hook)
            if not result.is_valid:
                errors_found = True
                console.print(f"\n[red]✗ {hook.script_path}[/red]")
                for error in result.errors:
                    console.print(f"  Error: {error}")
                for warning in result.warnings:
                    console.print(f"  Warning: {warning}")
            elif result.warnings:
                console.print(f"\n[yellow]⚠ {hook.script_path}[/yellow]")
                for warning in result.warnings:
                    console.print(f"  Warning: {warning}")

    if not errors_found:
        console.print("[green]✓ All hooks are valid[/green]")
    else:
        raise typer.Exit(1)


@app.command("run")
def run(
    hook_type: str = typer.Argument(..., help="Hook type (git, ide, agent)"),
    event: str = typer.Argument(..., help="Hook event (e.g., pre-commit)"),
    project_root: Path = typer.Option(
        ".",
        "--project",
        "-p",
        help="Project root directory",
    ),
) -> None:
    """Run hooks for a specific type and event."""
    try:
        hook_type_enum = HookType(hook_type.lower())
    except ValueError:
        console.print(f"[red]Invalid hook type: {hook_type}[/red]")
        console.print(f"Valid types: git, ide, agent")
        raise typer.Exit(1)

    manager = UniversalHookManager()
    hooks_dir = project_root / ".monoco" / "hooks"

    if not hooks_dir.exists():
        # No hooks configured, exit silently
        raise typer.Exit(0)

    # Scan for hooks
    groups = manager.scan(hooks_dir)

    # Find matching hooks
    key = hook_type_enum.value
    if key not in groups:
        raise typer.Exit(0)

    group = groups[key]
    matching_hooks = [
        h for h in group.hooks if h.metadata.event == event
    ]

    if not matching_hooks:
        raise typer.Exit(0)

    # Execute matching hooks
    dispatcher = manager.get_dispatcher(hook_type_enum)
    if not dispatcher:
        # Register appropriate dispatcher
        if hook_type_enum == HookType.GIT:
            dispatcher = GitHookDispatcher()
            manager.register_dispatcher(hook_type_enum, dispatcher)
        else:
            console.print(f"[red]No dispatcher available for type: {hook_type}[/red]")
            raise typer.Exit(1)

    exit_code = 0
    for hook in matching_hooks:
        context = {
            "event": event,
            "git_root": str(project_root),
        }
        if not dispatcher.execute(hook, context):
            exit_code = 1
            console.print(f"[red]Hook failed: {hook.script_path.name}[/red]")

    raise typer.Exit(exit_code)


@app.command("install")
def install(
    directory: Path = typer.Option(
        ".monoco/hooks",
        "--dir",
        "-d",
        help="Directory containing hook scripts",
    ),
    project_root: Path = typer.Option(
        ".",
        "--project",
        "-p",
        help="Project root directory",
    ),
) -> None:
    """Install Git hooks to .git/hooks/."""
    manager = UniversalHookManager()
    dispatcher = GitHookDispatcher()
    manager.register_dispatcher(HookType.GIT, dispatcher)

    dir_path = Path(directory)
    if not dir_path.exists():
        console.print(f"[yellow]Hooks directory not found: {dir_path}[/yellow]")
        raise typer.Exit(1)

    # Scan for git hooks
    groups = manager.scan(dir_path)

    if "git" not in groups:
        console.print("[dim]No Git hooks found.[/dim]")
        return

    # Install hooks
    group = groups["git"]
    installed = 0
    failed = 0

    for hook in group.hooks:
        if dispatcher.install(hook, project_root):
            installed += 1
            console.print(f"[green]✓ Installed {hook.metadata.event}[/green]")
        else:
            failed += 1
            console.print(f"[red]✗ Failed to install {hook.metadata.event}[/red]")

    if failed > 0:
        raise typer.Exit(1)

    console.print(f"\n[green]Installed {installed} hook(s)[/green]")


@app.command("uninstall")
def uninstall(
    event: Optional[str] = typer.Option(
        None,
        "--event",
        "-e",
        help="Specific event to uninstall (uninstalls all if not specified)",
    ),
    project_root: Path = typer.Option(
        ".",
        "--project",
        "-p",
        help="Project root directory",
    ),
) -> None:
    """Uninstall Git hooks from .git/hooks/."""
    dispatcher = GitHookDispatcher()

    if event:
        if dispatcher.uninstall(event, project_root):
            console.print(f"[green]✓ Uninstalled {event}[/green]")
        else:
            console.print(f"[red]✗ Failed to uninstall {event}[/red]")
            raise typer.Exit(1)
    else:
        # Uninstall all Monoco hooks
        installed = dispatcher.list_installed(project_root)
        uninstalled = 0
        failed = 0

        for hook_info in installed:
            if dispatcher.uninstall(hook_info["event"], project_root):
                uninstalled += 1
                console.print(f"[green]✓ Uninstalled {hook_info['event']}[/green]")
            else:
                failed += 1
                console.print(f"[red]✗ Failed to uninstall {hook_info['event']}[/red]")

        if failed > 0:
            raise typer.Exit(1)

        console.print(f"\n[green]Uninstalled {uninstalled} hook(s)[/green]")


@app.command("list")
def list_hooks(
    project_root: Path = typer.Option(
        ".",
        "--project",
        "-p",
        help="Project root directory",
    ),
) -> None:
    """List installed Git hooks."""
    dispatcher = GitHookDispatcher()
    installed = dispatcher.list_installed(project_root)

    if not installed:
        console.print("[dim]No Monoco Git hooks installed.[/dim]")
        return

    console.print("[bold]Installed Git Hooks:[/bold]\n")
    for hook in installed:
        merged_status = " (merged)" if hook.get("is_merged") else ""
        console.print(f"  • {hook['event']}{merged_status}")
        if hook.get("hook_id"):
            console.print(f"    ID: {hook['hook_id']}")
