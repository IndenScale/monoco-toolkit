import os
import typer
from typing import Optional
from monoco.core.output import print_output

app = typer.Typer(
    name="monoco",
    help="Monoco Agent Native Toolkit",
    add_completion=False,
    no_args_is_help=True,
)


def version_callback(value: bool):
    if value:
        # Try to read from pyproject.toml first (for dev mode)
        from pathlib import Path

        version = "unknown"

        try:
            # Look for pyproject.toml relative to this file
            # monoco/main.py -> ../pyproject.toml
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith('version = "'):
                            version = line.split('"')[1]
                            break

            if version == "unknown":
                import importlib.metadata

                version = importlib.metadata.version("monoco-toolkit")
        except Exception:
            # Fallback
            pass

        print(f"Monoco Toolkit v{version}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    root: Optional[str] = typer.Option(
        None, "--root", help="Explicitly specify the Monoco Workspace root directory."
    ),
):
    """
    Monoco Toolkit - The sensory and motor system for Monoco Agents.
    """
    # Capture command execution
    from monoco.core.telemetry import capture_event

    if ctx.invoked_subcommand:
        capture_event("cli_command_executed", {"command": ctx.invoked_subcommand})

    # Strict Workspace Resolution
    # Commands allowed to run without a workspace
    NO_WORKSPACE_COMMANDS = ["init", "clone"]

    # Initialize Config
    from monoco.core.config import get_config, find_monoco_root

    # If subcommand is not in whitelist, we enforce workspace
    require_workspace = False
    if ctx.invoked_subcommand and ctx.invoked_subcommand not in NO_WORKSPACE_COMMANDS:
        require_workspace = True

    try:
        # We pass root if provided. If require_workspace is True, get_config will throw if not found.
        # Note: If root is None, it defaults to CWD in get_config.

        # Auto-discover root if not provided
        config_root = root
        if config_root is None:
            discovered = find_monoco_root()
            # Only use discovered root if it actually has .monoco
            if (discovered / ".monoco").exists():
                config_root = str(discovered)

        get_config(project_root=config_root, require_project=require_workspace)
    except FileNotFoundError as e:
        # Graceful exit for workspace errors
        from rich.console import Console

        console = Console()
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print(
            "[yellow]Tip:[/yellow] Run this command in a Monoco Workspace root (containing .monoco), or use [bold]--root <path>[/bold]."
        )
        raise typer.Exit(code=1)


from monoco.core.setup import init_cli

app.command(name="init")(init_cli)

from monoco.core.sync import sync_command, uninstall_command

app.command(name="sync")(sync_command)
app.command(name="uninstall")(uninstall_command)


@app.command()
def info():
    """
    Show toolkit information and current mode.
    """
    from pydantic import BaseModel
    from monoco.core.config import get_config

    settings = get_config()

    class Status(BaseModel):
        version: str
        mode: str
        root: str
        project: str

    mode = "Agent (JSON)" if os.getenv("AGENT_FLAG") == "true" else "Human (Rich)"

    import importlib.metadata

    try:
        version = importlib.metadata.version("monoco-toolkit")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"

    status = Status(
        version=version,
        mode=mode,
        root=os.getcwd(),
        project=f"{settings.project.name} ({settings.project.key})",
    )

    print_output(status, title="Monoco Toolkit Status")

    if mode == "Human (Rich)":
        print_output(settings, title="Current Configuration")


# Register Feature Modules
# Register Feature Modules
from monoco.features.issue import commands as issue_cmd
from monoco.features.spike import commands as spike_cmd
from monoco.features.i18n import commands as i18n_cmd
from monoco.features.config import commands as config_cmd
from monoco.cli import project as project_cmd
from monoco.cli import workspace as workspace_cmd

app.add_typer(issue_cmd.app, name="issue", help="Manage development issues")
app.add_typer(spike_cmd.app, name="spike", help="Manage research spikes")
app.add_typer(i18n_cmd.app, name="i18n", help="Manage documentation i18n")
app.add_typer(config_cmd.app, name="config", help="Manage configuration")
app.add_typer(project_cmd.app, name="project", help="Manage projects")
app.add_typer(workspace_cmd.app, name="workspace", help="Manage workspace")

from monoco.features.scheduler import cli as scheduler_cmd

app.add_typer(scheduler_cmd.app, name="agent", help="Manage agent sessions")
app.add_typer(scheduler_cmd.role_app, name="role", help="Manage agent roles")


from monoco.daemon.commands import serve

app.command(name="serve")(serve)

if __name__ == "__main__":
    app()
