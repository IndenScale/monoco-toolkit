import typer
import yaml
import json
from pathlib import Path
from typing import Optional, Any
from rich.console import Console
from rich.syntax import Syntax
from pydantic import ValidationError

from monoco.core.config import (
    get_config,
    MonocoConfig,
    ConfigScope,
    load_raw_config,
    save_raw_config,
    get_config_path
)

app = typer.Typer(help="Manage Monoco configuration")
console = Console()

def _parse_value(value: str) -> Any:
    """Parse string value into appropriate type (bool, int, float, str)."""
    if value.lower() in ("true", "yes", "on"):
        return True
    if value.lower() in ("false", "no", "off"):
        return False
    if value.lower() == "null":
        return None
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value

@app.command()
def show(
    output: str = typer.Option("yaml", "--output", "-o", help="Output format: yaml or json"),
):
    """Show the currently active (merged) configuration."""
    config = get_config()
    # Pydantic v1/v2 compat: use dict() or model_dump()
    data = config.dict()
    
    if output == "json":
        print(json.dumps(data, indent=2))
    else:
        yaml_str = yaml.dump(data, default_flow_style=False)
        syntax = Syntax(yaml_str, "yaml")
        console.print(syntax)

@app.command()
def get(key: str = typer.Argument(..., help="Configuration key (e.g. project.name)")):
    """Get a specific configuration value."""
    config = get_config()
    data = config.dict()
    
    parts = key.split(".")
    current = data
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            console.print(f"[red]Key '{key}' not found.[/red]")
            raise typer.Exit(code=1)
            
    if isinstance(current, (dict, list)):
        if isinstance(current, dict):
            print(yaml.dump(current, default_flow_style=False))
        else:
            print(json.dumps(current))
    else:
        print(current)

@app.command(name="set")
def set_val(
    key: str = typer.Argument(..., help="Config key (e.g. telemetry.enabled)"),
    value: str = typer.Argument(..., help="Value to set"),
    global_scope: bool = typer.Option(False, "--global", "-g", help="Update global configuration"),
):
    """Set a configuration value in specific scope (project by default)."""
    scope = ConfigScope.GLOBAL if global_scope else ConfigScope.PROJECT
    
    # 1. Load Raw Config for the target scope
    raw_data = load_raw_config(scope)
    
    # 2. Parse Key & Update Data
    parts = key.split(".")
    target = raw_data
    
    # Context management for nested updates
    for i, part in enumerate(parts[:-1]):
        if part not in target:
            target[part] = {}
        target = target[part]
        if not isinstance(target, dict):
            parent_key = ".".join(parts[:i+1])
            console.print(f"[red]Cannot set '{key}': '{parent_key}' is not a dictionary ({type(target)}).[/red]")
            raise typer.Exit(code=1)
            
    parsed_val = _parse_value(value)
    target[parts[-1]] = parsed_val
    
    # 3. Validate against Schema
    # We simulate a full load by creating a temporary MonocoConfig with these overrides.
    # Note: This validation is "active" - we want to ensure the resulting config WOULD be valid.
    # However, raw_data is partial. Pydantic models with defaults will accept partials.
    try:
        # We can try to validate just the relevant model part if we knew which one it was.
        # But simpler is to check if MonocoConfig accepts this structure.
        MonocoConfig(**raw_data)
    except ValidationError as e:
        console.print(f"[red]Validation failed for key '{key}':[/red]")
        console.print(e)
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Unexpected validation error: {e}[/red]")
        raise typer.Exit(code=1)

    # 4. Save
    save_raw_config(scope, raw_data)
    
    scope_display = "Global" if global_scope else "Project"
    console.print(f"[green]✓ Set {key} = {parsed_val} in {scope_display} config.[/green]")

if __name__ == "__main__":
    app()
