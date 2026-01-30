import os
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Optional

import typer
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import Window, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console

console = Console()


def get_git_user() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def generate_key(name: str) -> str:
    """Generate a 3-4 letter uppercase key from name."""
    # Strategy 1: Upper case of first letters of words
    parts = name.split()
    if len(parts) >= 2:
        candidate = "".join(p[0] for p in parts[:4]).upper()
        if len(candidate) >= 2:
            return candidate

    # Strategy 2: First 3 letters
    return name[:3].upper()


def ask_with_selection(message: str, default: str) -> str:
    """Provides a selection-based prompt for stable rendering."""
    options = [f"{default} (Default)", "Custom Input..."]
    selected_index = 0

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def _(event):
        nonlocal selected_index
        selected_index = (selected_index - 1) % len(options)

    @kb.add("down")
    @kb.add("j")
    def _(event):
        nonlocal selected_index
        selected_index = (selected_index + 1) % len(options)

    @kb.add("enter")
    def _(event):
        event.app.exit(result=selected_index)

    @kb.add("c-c")
    def _(event):
        console.print("\n[red]Aborted by user.[/red]")
        sys.exit(0)

    def get_text():
        # Render the menu with explicit highlighting
        res = [("class:message", f"{message}:\n")]
        for i, opt in enumerate(options):
            if i == selected_index:
                res.append(("class:selected", f" ➔ {opt}\n"))
            else:
                res.append(("class:unselected", f"   {opt}\n"))
        return res

    style = Style.from_dict(
        {
            "message": "bold #ffffff",
            "selected": "bold #00ff00",  # High contrast green
            "unselected": "#888888",
        }
    )

    # Run a mini application to handle the selection
    app = Application(
        layout=Layout(
            HSplit(
                [
                    Window(
                        content=FormattedTextControl(get_text), height=len(options) + 1
                    )
                ]
            )
        ),
        key_bindings=kb,
        style=style,
        full_screen=False,
    )

    # Flush stdout to ensure previous output is visible
    sys.stdout.flush()

    choice = app.run()

    if choice == 0:
        return default
    else:
        # Prompt for custom input
        from prompt_toolkit import prompt

        return prompt(f"Enter custom {message.lower()}: ").strip() or default


def init_cli(
    ctx: typer.Context,
    global_only: bool = typer.Option(
        False, "--global", help="Only configure global user settings"
    ),
    project_only: bool = typer.Option(
        False, "--project", help="Only configure current project"
    ),
    # Non-interactive arguments
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Project Name"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Project Key"),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Author Name"),
    telemetry: Optional[bool] = typer.Option(
        None, "--telemetry/--no-telemetry", help="Enable/Disable telemetry"
    ),
):
    """
    Initialize Monoco configuration (Global and/or Project).
    """
    # Force non-interactive for now as requested
    interactive = False

    home_dir = Path.home() / ".monoco"
    global_config_path = home_dir / "config.yaml"

    # --- 1. Global Configuration ---
    if not project_only:
        if not global_config_path.exists() or global_only:
            console.rule("[bold blue]Global Setup[/bold blue]")

            # Ensure ~/.monoco exists
            home_dir.mkdir(parents=True, exist_ok=True)

            default_author = get_git_user() or os.getenv("USER", "developer")

            if author is None:
                if interactive:
                    author = ask_with_selection(
                        "Your Name (for issue tracking)", default_author
                    )
                else:
                    # Fallback or Error?
                    # For global author, we can use default if not provided, or error?
                    # User said "Directly error saying what field is missing"
                    # But author has a reasonable default. Let's try to use default if available, else error.
                    if not default_author:
                        console.print(
                            "[red]Error:[/red] Missing required field: --author"
                        )
                        raise typer.Exit(code=1)
                    author = default_author

            if telemetry is None:
                if interactive:
                    from rich.prompt import Confirm

                    telemetry = Confirm.ask(
                        "Enable anonymous telemetry to help improve Monoco?",
                        default=True,
                    )
                else:
                    # Default to True or False? Let's default to False for non-interactive safety or True?
                    # Usually explicit is better. Let's assume False if not specified in non-interactive.
                    # Or maybe we just skip it if not provided?
                    # Let's check user intent: "Report what field is missing".
                    # Telemetry is optional. Let's set it to False if missing.
                    telemetry = False

            user_config = {
                "core": {
                    "author": author,
                },
                "telemetry": {"enabled": telemetry},
            }

            with open(global_config_path, "w") as f:
                yaml.dump(user_config, f, default_flow_style=False)

            console.print(
                f"[green]✓ Global config saved to {global_config_path}[/green]\n"
            )

    if global_only:
        return

    # --- 2. Project Configuration ---
    cwd = Path.cwd()
    project_config_dir = cwd / ".monoco"
    workspace_config_path = project_config_dir / "workspace.yaml"
    project_config_path = project_config_dir / "project.yaml"

    project_initialized = False

    # Check if we should init project
    if workspace_config_path.exists() or project_config_path.exists():
        if interactive:
            from rich.prompt import Confirm

            if not Confirm.ask(
                f"Project/Workspace config already exists in [dim]{project_config_dir}[/dim]. Overwrite?"
            ):
                console.print("[dim]Skipping configuration overwrite.[/dim]")
                project_initialized = True
        else:
            console.print(
                f"[dim]Project/Workspace config already exists in {project_config_dir}. skipping generation.[/dim]"
            )
            project_initialized = True

        # Load existing config for downstream usage
        if workspace_config_path.exists():
            try:
                with open(workspace_config_path, "r") as f:
                    workspace_config = yaml.safe_load(f) or {}
            except Exception:
                workspace_config = {}
        else:
            workspace_config = {}

    if not project_initialized:
        console.rule("[bold blue]Project Setup[/bold blue]")

        default_name = cwd.name

        if name is None:
            if interactive:
                name = ask_with_selection("Project Name", default_name)
            else:
                console.print("[red]Error:[/red] Missing required field: --name")
                raise typer.Exit(code=1)

        project_name = name

        default_key = generate_key(project_name)

        if key is None:
            if interactive:
                key = ask_with_selection("Project Key (prefix for issues)", default_key)
            else:
                console.print("[red]Error:[/red] Missing required field: --key")
                raise typer.Exit(code=1)

        project_key = key

        project_config_dir.mkdir(exist_ok=True)

        # 2a. Create project.yaml (Identity)
        project_config = {"project": {"name": project_name, "key": project_key}}

        with open(project_config_path, "w") as f:
            yaml.dump(project_config, f, default_flow_style=False)

        # 2b. Create workspace.yaml (Environment)
        workspace_config = {
            "paths": {"issues": "Issues", "spikes": ".references"},
            "hooks": {"pre-commit": "monoco issue lint --recursive"},
        }

        with open(workspace_config_path, "w") as f:
            yaml.dump(workspace_config, f, default_flow_style=False)

        # 2c. Generate Config Template (Optional - might need update)
        # For now, let's skip template generation or update it later.
        # Or generate a workspace_template.yaml

        console.print(f"[green]✓ Project initialized in {cwd}[/green]")
        console.print("[dim]  - Identity: .monoco/project.yaml[/dim]")
        console.print("[dim]  - Environment: .monoco/workspace.yaml[/dim]")

    # Common Post-Init Logic (Idempotent)

    # Retrieve project key if we skipped initialization
    if project_initialized:
        # Try to read project key from file or just fallback
        if project_config_path.exists():
            try:
                with open(project_config_path, "r") as f:
                    p_conf = yaml.safe_load(f)
                    project_key = p_conf.get("project", {}).get("key", "MON")
            except:
                project_key = "MON"
        else:
            project_key = "MON"

    # Check for issue feature init (this logic was implicit in caller?)
    # No, init_cli is the main logic.

    # Initialize basic directories
    (cwd / "Issues").mkdir(exist_ok=True)
    (cwd / ".references").mkdir(exist_ok=True)

    # Initialize Agent Resources (Deprecated)
    # Removing reference to monoco.features.agent
    # try:
    #     from monoco.features.agent.core import init_agent_resources
    #     init_agent_resources(cwd)
    #     console.print(f"[dim]  - Agent Resources: .monoco/actions/*.prompty[/dim]")
    # except Exception as e:
    #     console.print(f"[yellow]Warning: Failed to init agent resources: {e}[/yellow]")

    # Initialize Hooks
    try:
        from monoco.core.githooks import install_hooks

        # Re-load config to get the just-written hooks (or default ones)
        # Actually we have the dict right here in workspace_config['hooks']
        hooks_config = workspace_config.get("hooks", {})
        if hooks_config:
            install_hooks(cwd, hooks_config)
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to install hooks: {e}[/yellow]")

    console.print("\n[bold green]✓ Monoco Project Initialized![/bold green]")
    console.print(
        f"Access configured! issues will be created as [bold]{project_key}-XXX[/bold]"
    )
