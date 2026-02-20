import typer
import yaml
import json
from typing import Any
from rich.console import Console
from rich.syntax import Syntax
from pydantic import ValidationError

from monoco.core.config import (
    get_config,
    MonocoConfig,
    load_raw_config,
    save_raw_config,
)
from monoco.core.output import AgentOutput, OutputManager

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
    output: str = typer.Option(
        "yaml", "--output", "-o", help="Output format: yaml or json"
    ),
    json_output: AgentOutput = False,
):
    """Show the currently active (merged) configuration."""
    config = get_config()
    # Pydantic v1/v2 compat: use dict() or model_dump()
    data = config.dict()

    if OutputManager.is_agent_mode():
        OutputManager.print(data)
        return

    if output == "json":
        print(json.dumps(data, indent=2))
    else:
        yaml_str = yaml.dump(data, default_flow_style=False)
        syntax = Syntax(yaml_str, "yaml")
        console.print(syntax)


@app.command()
def get(
    key: str = typer.Argument(..., help="Configuration key (e.g. project.name)"),
    json_output: AgentOutput = False,
):
    """Get a specific configuration value."""
    config = get_config()
    data = config.dict()

    parts = key.split(".")
    current = data

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            OutputManager.error(f"Key '{key}' not found.")
            raise typer.Exit(code=1)

    if OutputManager.is_agent_mode():
        OutputManager.print({"key": key, "value": current})
    else:
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
    json_output: AgentOutput = False,
):
    """Set a configuration value in ~/.monoco/config.yaml."""
    # 1. Load Raw Config
    raw_data = load_raw_config()

    # 2. Parse Key & Update Data
    parts = key.split(".")
    target = raw_data

    # Context management for nested updates
    for i, part in enumerate(parts[:-1]):
        if part not in target:
            target[part] = {}
        target = target[part]
        if not isinstance(target, dict):
            parent_key = ".".join(parts[: i + 1])
            OutputManager.error(
                f"Cannot set '{key}': '{parent_key}' is not a dictionary ({type(target)})."
            )
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
        OutputManager.error(f"Validation failed for key '{key}':\n{e}")
        raise typer.Exit(code=1)
    except Exception as e:
        OutputManager.error(f"Unexpected validation error: {e}")
        raise typer.Exit(code=1)

    # 4. Save
    save_raw_config(raw_data)

    if OutputManager.is_agent_mode():
        OutputManager.print(
            {
                "status": "updated",
                "key": key,
                "value": parsed_val,
            }
        )
    else:
        console.print(
            f"[green]✓ Set {key} = {parsed_val} in config.[/green]"
        )


if __name__ == "__main__":
    app()
