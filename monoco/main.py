import os
import typer
from typing import Optional
from monoco.core.output import print_output

app = typer.Typer(
    name="monoco",
    help="Monoco Agent Native Toolkit",
    add_completion=False,
    no_args_is_help=True
)


def version_callback(value: bool):
    if value:
        import importlib.metadata
        try:
            version = importlib.metadata.version("monoco-toolkit")
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
        print(f"Monoco Toolkit v{version}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Show version and exit", callback=version_callback, is_eager=True
    ),
):
    """
    Monoco Toolkit - The sensory and motor system for Monoco Agents.
    """
    # Capture command execution
    from monoco.core.telemetry import capture_event
    if ctx.invoked_subcommand:
        capture_event("cli_command_executed", {"command": ctx.invoked_subcommand})

from monoco.core.setup import init_cli
app.command(name="init")(init_cli)

from monoco.core.sync import sync_command, uninstall_command
app.command(name="sync")(sync_command)
app.command(name="uninstall")(uninstall_command)

@app.command(name="doctor")
def doctor_cmd(
    force: bool = typer.Option(False, "--force", "-f", help="Force refresh of agent state")
):
    """
    Diagnose Agent Environment.
    """
    from monoco.features.agent.doctor import doctor
    doctor(force)

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
        project=f"{settings.project.name} ({settings.project.key})"
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

app.add_typer(issue_cmd.app, name="issue", help="Manage development issues")
app.add_typer(spike_cmd.app, name="spike", help="Manage research spikes")
app.add_typer(i18n_cmd.app, name="i18n", help="Manage documentation i18n")
app.add_typer(config_cmd.app, name="config", help="Manage configuration")

from monoco.features.agent import commands as agent_cmd
app.add_typer(agent_cmd.app, name="agent", help="Delegate tasks to Agent CLIs")

from monoco.daemon.commands import serve
app.command(name="serve")(serve)

@app.command()
def pty(
    host: str = "127.0.0.1",
    port: int = 3124,
    cwd: Optional[str] = None
):
    """
    Start the Monoco PTY Daemon (WebSocket).
    """
    from monoco.features.pty.server import run_pty_server
    from pathlib import Path
    
    path = Path(cwd) if cwd else None
    run_pty_server(host, port, path)

if __name__ == "__main__":
    app()
