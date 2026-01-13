import typer
import yaml
from pathlib import Path
from typing import Optional
from monoco.core.config import get_config, MonocoConfig
from monoco.core.output import print_output
from rich.console import Console

app = typer.Typer(help="Manage Monoco configuration")
console = Console()

@app.command()
def show():
    """Show current configuration."""
    settings = get_config()
    print_output(settings, title="Current Configuration")

@app.command(name="set")
def set_val(
    key: str = typer.Argument(..., help="Config key (e.g. telemetry.enabled)"),
    value: str = typer.Argument(..., help="Value to set"),
    scope: str = typer.Option("global", "--scope", "-s", help="Configuration scope: global or project")
):
    """Set a configuration value."""
    # This is a simplified implementation of config setting
    # In a real system, we'd want to validate the key against the schema
    
    if scope == "global":
        config_path = Path.home() / ".monoco" / "config.yaml"
    else:
        # Check project root
        cwd = Path.cwd()
        config_path = cwd / ".monoco" / "config.yaml"
        if not (cwd / ".monoco").exists():
             config_path = cwd / "monoco.yaml"

    config_data = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f) or {}

    # Simple nested key support (e.g. telemetry.enabled)
    parts = key.split(".")
    target = config_data
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]
    
    # Type conversion
    if value.lower() in ("true", "yes", "on"):
        val = True
    elif value.lower() in ("false", "no", "off"):
        val = False
    else:
        try:
            val = int(value)
        except ValueError:
            val = value

    target[parts[-1]] = val

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    console.print(f"[green]✓ Set {key} = {val} in {scope} config.[/green]")

if __name__ == "__main__":
    app()
