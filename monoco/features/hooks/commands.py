"""
CLI commands for Git Hooks management.

Provides:
- monoco hooks install
- monoco hooks uninstall
- monoco hooks status
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from monoco.core.config import get_config
from monoco.core.output import OutputManager
from .core import GitHooksManager, HookConfig

app = typer.Typer(help="Manage Git hooks for development workflow.")
console = Console()


def _get_manager() -> GitHooksManager:
    """Get configured GitHooksManager instance."""
    config = get_config()
    project_root = Path(config.paths.root).resolve()

    hooks_config = HookConfig(
        enabled=config.hooks.enabled,
        enabled_features=config.hooks.features,
        enabled_hooks=config.hooks.hooks,
    )

    return GitHooksManager(project_root, hooks_config)


@app.command("install")
def install(
    hook_type: Optional[str] = typer.Argument(
        None,
        help="Specific hook type to install (pre-commit, pre-push, post-checkout). If not specified, installs all enabled hooks."
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force installation even if hook already exists",
    ),
    json: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format (for agent mode)",
    ),
):
    """
    Install git hooks to .git/hooks/.

    Discovers hooks from all Features and generates combined hook scripts.
    """
    manager = _get_manager()

    if not manager.is_git_repo():
        OutputManager.error("Not a git repository. Cannot install hooks.")
        raise typer.Exit(code=1)

    if hook_type:
        # Install specific hook type
        from .core import HookType
        try:
            htype = HookType(hook_type)
        except ValueError:
            valid_types = [t.value for t in HookType]
            OutputManager.error(f"Invalid hook type: {hook_type}. Valid types: {', '.join(valid_types)}")
            raise typer.Exit(code=1)

        # Temporarily enable this hook type
        manager.config.enabled_hooks[hook_type] = True

    results = manager.install()

    if OutputManager.is_agent_mode() or json:
        OutputManager.print({
            "status": "installed",
            "hooks": {k.value: v for k, v in results.items()}
        })
    else:
        installed = [k.value for k, v in results.items() if v]
        skipped = [k.value for k, v in results.items() if not v]

        if installed:
            console.print(f"[green]✓ Installed hooks:[/green] {', '.join(installed)}")
        if skipped:
            console.print(f"[yellow]⚠ Skipped hooks:[/yellow] {', '.join(skipped)}")


@app.command("uninstall")
def uninstall(
    hook_type: Optional[str] = typer.Argument(
        None,
        help="Specific hook type to uninstall. If not specified, uninstalls all Monoco-managed hooks."
    ),
    json: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format (for agent mode)",
    ),
):
    """
    Uninstall Monoco-managed git hooks from .git/hooks/.

    Only removes hooks that were installed by Monoco (identified by marker).
    """
    manager = _get_manager()

    if not manager.is_git_repo():
        OutputManager.error("Not a git repository.")
        raise typer.Exit(code=1)

    if hook_type:
        # Uninstall specific hook type
        hook_path = manager.hooks_dir / hook_type
        if hook_path.exists():
            try:
                content = hook_path.read_text(encoding="utf-8")
                if manager.MONOCO_MARKER in content:
                    hook_path.unlink()
                    results = {hook_type: True}
                else:
                    results = {hook_type: False}
            except Exception as e:
                OutputManager.error(f"Failed to uninstall {hook_type}: {e}")
                raise typer.Exit(code=1)
        else:
            results = {hook_type: False}
    else:
        results = manager.uninstall()

    if OutputManager.is_agent_mode() or json:
        OutputManager.print({
            "status": "uninstalled",
            "hooks": {k.value if hasattr(k, 'value') else k: v for k, v in results.items()}
        })
    else:
        removed = [k.value if hasattr(k, 'value') else k for k, v in results.items() if v]
        skipped = [k.value if hasattr(k, 'value') else k for k, v in results.items() if not v]

        if removed:
            console.print(f"[green]✓ Removed hooks:[/green] {', '.join(removed)}")
        if skipped:
            console.print(f"[dim]- Skipped (not managed by Monoco):[/dim] {', '.join(skipped)}")


@app.command("status")
def status(
    json: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format (for agent mode)",
    ),
):
    """
    Show current hooks installation status.

    Displays which hooks are installed, discovered, and their configuration.
    """
    manager = _get_manager()
    status_info = manager.get_status()

    if OutputManager.is_agent_mode() or json:
        OutputManager.print(status_info)
        return

    # Human-readable output
    if not status_info["is_git_repo"]:
        console.print("[red]Not a git repository.[/red]")
        raise typer.Exit(code=1)

    console.print(Panel("[bold blue]Git Hooks Status[/bold blue]", expand=False))

    # Installed hooks table
    table = Table(title="Installed Hooks")
    table.add_column("Hook Type", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Managed By", style="dim")

    for hook_type, info in status_info["installed"].items():
        if info["exists"]:
            status_str = "[green]Installed[/green]"
            managed = "Monoco" if info.get("managed_by_monoco") else "External"
        else:
            status_str = "[dim]Not installed[/dim]"
            managed = "-"
        table.add_row(hook_type, status_str, managed)

    console.print(table)

    # Discovered hooks
    if status_info["discovered"]:
        console.print("\n[bold]Discovered Hook Scripts:[/bold]")
        for hook_type, scripts in status_info["discovered"].items():
            tree = Tree(f"[cyan]{hook_type}[/cyan]")
            for script in scripts:
                tree.add(f"[dim]{script['feature']}[/dim] (priority: {script['priority']})")
            console.print(tree)
    else:
        console.print("\n[yellow]No hook scripts discovered from Features.[/yellow]")

    # Configuration
    config_tree = Tree("[bold]Configuration:[/bold]")
    config_tree.add(f"Hooks enabled: {status_info['config']['enabled']}")

    if status_info['config']['enabled_features']:
        features_branch = config_tree.add("Feature-specific settings:")
        for feature, enabled in status_info['config']['enabled_features'].items():
            status = "enabled" if enabled else "disabled"
            features_branch.add(f"{feature}: {status}")

    if status_info['config']['enabled_hooks']:
        hooks_branch = config_tree.add("Hook-type settings:")
        for hook, enabled in status_info['config']['enabled_hooks'].items():
            status = "enabled" if enabled else "disabled"
            hooks_branch.add(f"{hook}: {status}")

    console.print(config_tree)


@app.command("enable")
def enable(
    hook_type: str = typer.Argument(..., help="Hook type to enable (pre-commit, pre-push, post-checkout)"),
):
    """
    Enable a specific hook type in configuration.

    This updates workspace.yaml to enable the hook for future installs.
    """
    from .core import HookType
    try:
        HookType(hook_type)
    except ValueError:
        valid_types = [t.value for t in HookType]
        OutputManager.error(f"Invalid hook type: {hook_type}. Valid types: {', '.join(valid_types)}")
        raise typer.Exit(code=1)

    # Update workspace.yaml
    config = get_config()
    config_path = Path(config.paths.root) / ".monoco" / "workspace.yaml"
    try:
        import yaml
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}

        if 'hooks' not in data:
            data['hooks'] = {}
        if 'hooks' not in data['hooks']:
            data['hooks']['hooks'] = {}
        data['hooks']['hooks'][hook_type] = True

        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        console.print(f"[green]✓ Enabled {hook_type} hook in configuration[/green]")
        console.print(f"[dim]Run 'monoco hooks install' to apply changes.[/dim]")
    except Exception as e:
        OutputManager.error(f"Failed to update configuration: {e}")
        raise typer.Exit(code=1)


@app.command("disable")
def disable(
    hook_type: str = typer.Argument(..., help="Hook type to disable (pre-commit, pre-push, post-checkout)"),
):
    """
    Disable a specific hook type in configuration.

    This updates workspace.yaml to disable the hook for future installs.
    """
    from .core import HookType
    try:
        HookType(hook_type)
    except ValueError:
        valid_types = [t.value for t in HookType]
        OutputManager.error(f"Invalid hook type: {hook_type}. Valid types: {', '.join(valid_types)}")
        raise typer.Exit(code=1)

    # Update workspace.yaml
    config = get_config()
    config_path = Path(config.paths.root) / ".monoco" / "workspace.yaml"
    try:
        import yaml
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}

        if 'hooks' not in data:
            data['hooks'] = {}
        if 'hooks' not in data['hooks']:
            data['hooks']['hooks'] = {}
        data['hooks']['hooks'][hook_type] = False

        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        console.print(f"[green]✓ Disabled {hook_type} hook in configuration[/green]")
        console.print(f"[dim]Run 'monoco hooks uninstall {hook_type}' to remove existing hook.[/dim]")
    except Exception as e:
        OutputManager.error(f"Failed to update configuration: {e}")
        raise typer.Exit(code=1)
