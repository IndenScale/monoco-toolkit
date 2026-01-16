import typer
from pathlib import Path
from rich.console import Console
from typing import Annotated
import yaml
import json

from monoco.core.output import AgentOutput, OutputManager

app = typer.Typer(help="Manage Monoco Workspace")
console = Console()

@app.command("init")
def init_workspace(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
    json: AgentOutput = False,
):
    """Initialize a workspace environment in the current directory."""
    cwd = Path.cwd()
    workspace_config_path = cwd / ".monoco" / "workspace.yaml"
    
    if workspace_config_path.exists() and not force:
        OutputManager.error(f"Workspace already initialized in {cwd}. Use --force to overwrite.")
        raise typer.Exit(code=1)

    cwd.mkdir(parents=True, exist_ok=True)
    (cwd / ".monoco").mkdir(exist_ok=True)
    
    # Default workspace config
    config = {
        "paths": {
            "issues": "Issues", # Default
            "spikes": ".references",
            "specs": "SPECS"
        }
    }
    
    with open(workspace_config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
        
    OutputManager.print({
        "status": "initialized",
        "path": str(cwd),
        "config_file": str(workspace_config_path)
    })

