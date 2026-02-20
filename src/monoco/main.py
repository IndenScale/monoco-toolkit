import os
import typer
from typing import Optional
from pathlib import Path
from monoco.core.output import print_output
from monoco.core.loader import FeatureLoader, FeatureContext

# Global feature loader for CLI lifecycle management
_feature_loader: Optional[FeatureLoader] = None


def get_feature_loader() -> FeatureLoader:
    """Get or initialize the global feature loader."""
    global _feature_loader
    if _feature_loader is None:
        _feature_loader = FeatureLoader()
        # Discover features but defer loading until needed
        _feature_loader.discover()
    return _feature_loader


app = typer.Typer(
    name="monoco",
    help="The Headless Operating System for Agentic Engineering",
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
            # src/monoco/main.py -> ../../pyproject.toml
            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
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

        print(f"Monoco v{version}")
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
        None, "--root", help="Explicitly specify the Monoco Project root directory."
    ),
):
    """
    Monoco - The sensory and motor system for Monoco Agents.
    """
    # Capture command execution
    from monoco.core.telemetry import capture_event

    if ctx.invoked_subcommand:
        capture_event("cli_command_executed", {"command": ctx.invoked_subcommand})

    # Strict Project Resolution
    # Commands allowed to run without a project
    NO_PROJECT_COMMANDS = ["init", "clone"]

    # Initialize Config
    from monoco.core.config import get_config, find_monoco_root

    # If subcommand is not in whitelist, we enforce project
    require_project = False
    if ctx.invoked_subcommand and ctx.invoked_subcommand not in NO_PROJECT_COMMANDS:
        require_project = True

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

        config = get_config(project_root=config_root, require_project=require_project)
        
        # Initialize FeatureLoader and mount features when project is available
        if require_project and config_root:
            loader = get_feature_loader()
            # Load all features (with lazy loading for non-critical features)
            loader.load_all(lazy=True)
            # Create feature context and mount all features
            feature_context = FeatureContext(
                root=Path(config_root),
                config=config.model_dump(),
                registry=loader.registry,
            )
            errors = loader.mount_all(feature_context)
            if errors:
                from rich.console import Console
                console = Console()
                for name, error in errors.items():
                    console.print(f"[yellow]Warning: Failed to mount feature '{name}': {error}[/yellow]")
                    
    except FileNotFoundError as e:
        # Graceful exit for workspace errors
        from rich.console import Console

        console = Console()
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print(
            "[yellow]Tip:[/yellow] Run this command in a Monoco Project root (containing .monoco), or use [bold]--root <path>[/bold]."
        )
        raise typer.Exit(code=1)


from monoco.core.setup import init_cli

app.command(name="init")(init_cli)

from monoco.core.install import install_command, sync_command, uninstall_command

app.command(name="install")(install_command)
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

    from monoco.core.registry import get_inventory
    inventory = get_inventory()
    project_count = len(inventory.list())

    status = Status(
        version=version,
        mode=mode,
        root=os.getcwd(),
        project=f"{settings.project.name} ({settings.project.key})",
    )
    
    # Add inventory info if in human mode or for agents
    status_data = status.model_dump()
    status_data["global_projects"] = project_count

    print_output(status_data, title="Monoco Status")

    if mode == "Human (Rich)":
        print_output(settings, title="Current Configuration")


# Register Feature Modules
# Register Feature Modules
from monoco.features.issue import commands as issue_cmd
from monoco.features.spike import commands as spike_cmd
from monoco.features.i18n import commands as i18n_cmd
from monoco.features.config import commands as config_cmd
from monoco.features.hooks import commands as hooks_cmd
from monoco.cli import project as project_cmd
from monoco.features.doc_extractor import commands as doc_extractor_cmd

app.add_typer(issue_cmd.app, name="issue", help="Manage development issues")
app.add_typer(spike_cmd.app, name="spike", help="Manage research spikes")
app.add_typer(i18n_cmd.app, name="i18n", help="Manage documentation i18n")
app.add_typer(config_cmd.app, name="config", help="Manage configuration")
app.add_typer(hooks_cmd.app, name="hook", help="Manage git hooks for development workflow")
app.add_typer(project_cmd.app, name="project", help="Manage projects")
app.add_typer(doc_extractor_cmd.app, name="doc-extractor", help="Extract and render documents to WebP pages")

from monoco.features.agent import cli as scheduler_cmd

app.add_typer(scheduler_cmd.app, name="agent", help="Manage agent sessions and roles")

from monoco.features.memo import app as memo_app

app.add_typer(memo_app, name="memo", help="Manage fleeting notes (memos)")

from monoco.features.mailbox import commands as mailbox_cmd

app.add_typer(mailbox_cmd.app, name="mailbox", help="Manage messages (Mailbox)")

from monoco.features.courier import commands as courier_cmd

app.add_typer(courier_cmd.app, name="courier", help="Manage Courier service (message transport)")

from monoco.features.channel import commands as channel_cmd

app.add_typer(channel_cmd.app, name="channel", help="Manage notification channels (DingTalk, Lark, Email)")

from monoco.features.ralph import cli as ralph_cmd

app.add_typer(ralph_cmd.app, name="ralph", help="Ralph Loop - Agent session relay for long-running issues")

from monoco.features.pretty_markdown import commands as pretty_markdown_cmd

app.add_typer(pretty_markdown_cmd.app, name="pretty-markdown", help="Markdown formatting and linting utilities")

from monoco.daemon.commands import serve_app, serve

app.add_typer(serve_app, name="serve", help="Manage Monoco Daemon server")
# Keep legacy 'serve' command for backward compatibility
app.command(name="serve", hidden=True)(serve)

if __name__ == "__main__":
    app()
