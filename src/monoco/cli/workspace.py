import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
import yaml

from monoco.core.output import AgentOutput, OutputManager
from monoco.core.githooks import install_hooks
from monoco.core.registry import get_workspace_inventory

app = typer.Typer(help="Manage Monoco Workspace")
console = Console()


@app.command("init")
def init_workspace(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing config"
    ),
    json: AgentOutput = False,
):
    """Initialize a workspace environment in the current directory."""
    cwd = Path.cwd()
    workspace_config_path = cwd / ".monoco" / "workspace.yaml"

    if workspace_config_path.exists() and not force:
        OutputManager.error(
            f"Workspace already initialized in {cwd}. Use --force to overwrite."
        )
        raise typer.Exit(code=1)

    cwd.mkdir(parents=True, exist_ok=True)
    (cwd / ".monoco").mkdir(exist_ok=True)

    # Default workspace config
    config = {
        "paths": {
            "issues": "Issues",  # Default
            "spikes": ".references",
        },
        "hooks": {"pre-commit": "monoco issue lint --recursive"},
    }

    with open(workspace_config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    try:
        install_hooks(cwd, config["hooks"])
    except Exception as e:
        OutputManager.warning(f"Failed to install hooks: {e}")

    OutputManager.print(
        {
            "status": "initialized",
            "path": str(cwd),
            "config_file": str(workspace_config_path),
        }
    )
@app.command("list")
def list_workspaces(
    json: AgentOutput = False,
    all_workspaces: bool = typer.Option(False, "--all", "-a", help="Show global inventory instead of local workspace info"),
):
    """List registered workspaces."""
    if all_workspaces:
        inventory = get_workspace_inventory()
        entries = inventory.list()
        
        if OutputManager.is_agent_mode():
            OutputManager.print([e.to_dict() for e in entries])
        else:
            table = Table(title="Global Workspace Inventory")
            table.add_column("Name", style="magenta")
            table.add_column("Path", style="cyan")
            
            for e in entries:
                table.add_row(e.name, str(e.path))
            
            console.print(table)
            console.print(f"[dim]Total: {len(entries)} workspaces in global inventory[/dim]")
        return

    # Local workspace info
    cwd = Path.cwd()
    workspace_config_path = cwd / ".monoco" / "workspace.yaml"
    if not workspace_config_path.exists():
        console.print(f"[yellow]Current directory is not a Monoco Workspace.[/yellow]")
        return
        
    console.print(f"Current Workspace: [cyan]{cwd}[/cyan]")


@app.command("register")
def register_workspace(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Workspace path (defaults to current)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Optional name for the workspace"),
    json: AgentOutput = False,
):
    """Register a workspace in the global inventory."""
    if path is None:
        path = Path.cwd()
    else:
        path = path.resolve()
        
    inventory = get_workspace_inventory()
    entry = inventory.register(path, name=name)
    
    if json:
        OutputManager.print(entry.to_dict())
    else:
        console.print(f"[green]✓[/green] Workspace registered: [magenta]{entry.name}[/magenta] -> [dim]{path}[/dim]")


@app.command("remove")
def remove_workspace(
    path: Path = typer.Argument(..., help="Path of the workspace to remove"),
    json: AgentOutput = False,
):
    """Remove a workspace from the global inventory."""
    inventory = get_workspace_inventory()
    path = Path(path).resolve()
    
    inventory.remove(path)
    
    if json:
        OutputManager.print({"success": True, "path": str(path)})
    else:
        console.print(f"[green]✓[/green] Workspace [dim]{path}[/dim] removed from inventory.")
