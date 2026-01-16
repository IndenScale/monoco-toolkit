import typer
from pathlib import Path
from typing import Optional, Annotated
from rich.console import Console
from rich.table import Table
import yaml
import json
import os

from monoco.core.workspace import find_projects, is_project_root
from monoco.core.config import get_config
from monoco.core.output import AgentOutput, OutputManager

app = typer.Typer(help="Manage Monoco Projects")
console = Console()

@app.command("list")
def list_projects(
    json: AgentOutput = False,
    root: Optional[str] = typer.Option(None, "--root", help="Workspace root")
):
    """List all discovered projects in the workspace."""
    cwd = Path(root).resolve() if root else Path.cwd()
    projects = find_projects(cwd)
    
    if OutputManager.is_agent_mode():
        data = [
            {
                "id": p.id,
                "name": p.name,
                "path": str(p.path),
                "key": p.config.project.key if p.config.project else ""
            }
            for p in projects
        ]
        OutputManager.print(data)
    else:
        table = Table(title=f"Projects in {cwd}")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Key", style="green")
        table.add_column("Path", style="dim")
        
        for p in projects:
            path_str = str(p.path.relative_to(cwd)) if p.path.is_relative_to(cwd) else str(p.path)
            if path_str == ".":
                path_str = "(root)"
            key = p.config.project.key if p.config.project else "N/A"
            table.add_row(p.id, p.name, key, path_str)
            
        console.print(table)

@app.command("init")
def init_project(
    name: str = typer.Option(..., "--name", "-n", help="Project Name"),
    key: str = typer.Option(..., "--key", "-k", help="Project Key"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
    json: AgentOutput = False,
):
    """Initialize a new project in the current directory."""
    cwd = Path.cwd()
    project_config_path = cwd / ".monoco" / "project.yaml"
    
    if project_config_path.exists() and not force:
        OutputManager.error(f"Project already initialized in {cwd}. Use --force to overwrite.")
        raise typer.Exit(code=1)
        
    cwd.mkdir(parents=True, exist_ok=True)
    (cwd / ".monoco").mkdir(exist_ok=True)
    
    config = {
        "project": {
            "name": name,
            "key": key
        }
    }
    
    with open(project_config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
        
    OutputManager.print({
        "status": "initialized",
        "name": name,
        "key": key,
        "path": str(cwd),
        "config_file": str(project_config_path)
    })
