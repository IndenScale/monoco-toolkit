import typer
from pathlib import Path
from rich.console import Console
from typing import Annotated

from monoco.core.config import get_config
from monoco.core.output import AgentOutput, OutputManager
from . import core

app = typer.Typer(help="Spike & Repo Management.")

@app.command("init")
def init(
    json: AgentOutput = False,
):
    """Initialize the Spike environment (gitignore setup)."""
    config = get_config()
    root_dir = Path(config.paths.root)
    spikes_dir_name = config.paths.spikes
    
    core.ensure_gitignore(root_dir, spikes_dir_name)
    
    # Create the directory
    (root_dir / spikes_dir_name).mkdir(exist_ok=True)
    
    OutputManager.print({
        "status": "initialized",
        "directory": spikes_dir_name,
        "gitignore_updated": True
    })

@app.command("add")
def add_repo(
    url: str = typer.Argument(..., help="Git Repository URL"),
    json: AgentOutput = False,
):
    """Add a new research repository."""
    config = get_config()
    root_dir = Path(config.paths.root)
    
    # Infer name from URL
    # e.g., https://github.com/foo/bar.git -> bar
    # e.g., git@github.com:foo/bar.git -> bar
    name = url.split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
        
    core.update_config_repos(root_dir, name, url)
    OutputManager.print({
        "status": "added",
        "name": name,
        "url": url,
        "message": f"Run 'monoco spike sync' to download content."
    })

@app.command("remove")
def remove_repo(
    name: str = typer.Argument(..., help="Repository Name"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete physical directory without asking"),
    json: AgentOutput = False,
):
    """Remove a repository from configuration."""
    config = get_config()
    root_dir = Path(config.paths.root)
    spikes_dir = root_dir / config.paths.spikes
    
    if name not in config.project.spike_repos:
        OutputManager.error(f"Repo {name} not found in configuration.")
        return

    # Remove from config
    core.update_config_repos(root_dir, name, "", remove=True)
    
    target_path = spikes_dir / name
    deleted = False
    if target_path.exists():
        if force or typer.confirm(f"Do you want to delete the directory {target_path}?", default=False):
            core.remove_repo_dir(spikes_dir, name)
            deleted = True
        else:
            deleted = False
            
    OutputManager.print({
        "status": "removed",
        "name": name,
        "directory_deleted": deleted
    })

@app.command("sync")
def sync_repos(
    json: AgentOutput = False,
):
    """Sync (Clone/Pull) all configured repositories."""
    # Force reload config to get latest updates
    config = get_config()
    
    root_dir = Path(config.paths.root)
    spikes_dir = root_dir / config.paths.spikes
    spikes_dir.mkdir(exist_ok=True)
    
    repos = config.project.spike_repos
    
    if not repos:
        OutputManager.print({"status": "empty", "message": "No repositories configured."}, title="Sync")
        return
        
    results = []
    
    for name, url in repos.items():
        try:
            core.sync_repo(root_dir, spikes_dir, name, url)
            results.append({"name": name, "status": "synced", "url": url})
        except Exception as e:
             results.append({"name": name, "status": "failed", "error": str(e), "url": url})
        
    OutputManager.print(results, title="Sync Results")

@app.command("list")
def list_repos(
    json: AgentOutput = False,
):
    """List configured repositories."""
    config = get_config()
    repos = config.project.spike_repos
    
    if not repos:
        OutputManager.print([], title="Repositories")
        return
        
    data = [{"name": name, "url": url} for name, url in repos.items()]
    OutputManager.print(data, title="Repositories")
