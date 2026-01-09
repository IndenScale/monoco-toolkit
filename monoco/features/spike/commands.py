import typer
from pathlib import Path
from rich.console import Console

from monoco.core.config import get_config
from . import core

app = typer.Typer(help="Spike & Repo Management.")
console = Console()

@app.command("init")
def init():
    """Initialize the Spike environment (gitignore setup)."""
    config = get_config()
    root_dir = Path(config.paths.root)
    spikes_dir_name = config.paths.spikes
    
    core.ensure_gitignore(root_dir, spikes_dir_name)
    
    # Create the directory
    (root_dir / spikes_dir_name).mkdir(exist_ok=True)
    
    console.print(f"[green]✔[/green] Initialized Spike environment. Added '{spikes_dir_name}/' to .gitignore.")

@app.command("add")
def add_repo(
    url: str = typer.Argument(..., help="Git Repository URL"),
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
    console.print(f"[green]✔[/green] Added repo [bold]{name}[/bold] ({url}) to configuration.")
    console.print("Run [bold]monoco spike sync[/bold] to download content.")

@app.command("remove")
def remove_repo(
    name: str = typer.Argument(..., help="Repository Name"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete physical directory without asking"),
):
    """Remove a repository from configuration."""
    config = get_config()
    root_dir = Path(config.paths.root)
    spikes_dir = root_dir / config.paths.spikes
    
    if name not in config.project.spike_repos:
        console.print(f"[yellow]![/yellow] Repo [bold]{name}[/bold] not found in configuration.")
        return

    # Remove from config
    core.update_config_repos(root_dir, name, "", remove=True)
    console.print(f"[green]✔[/green] Removed [bold]{name}[/bold] from configuration.")
    
    target_path = spikes_dir / name
    if target_path.exists():
        if force or typer.confirm(f"Do you want to delete the directory {target_path}?", default=False):
            core.remove_repo_dir(spikes_dir, name)
            console.print(f"[gray]✔[/gray] Deleted directory {target_path}.")
        else:
            console.print(f"[gray]ℹ[/gray] Directory {target_path} kept.")

@app.command("sync")
def sync_repos():
    """Sync (Clone/Pull) all configured repositories."""
    # Force reload config to get latest updates
    config = get_config()
    # Note: get_config is a singleton, so for 'add' then 'sync' in same process, 
    # we rely on 'add' writing to disk and us reading from memory? 
    # Actually, if we run standard CLI "monoco spike add" then "monoco spike sync", 
    # they are separate processes, so config loads fresh.
    
    root_dir = Path(config.paths.root)
    spikes_dir = root_dir / config.paths.spikes
    spikes_dir.mkdir(exist_ok=True)
    
    repos = config.project.spike_repos
    
    if not repos:
        console.print("[yellow]No repositories configured.[/yellow] Use 'monoco spike add <url>' first.")
        return
        
    console.print(f"Syncing {len(repos)} repositories...")
    
    for name, url in repos.items():
        core.sync_repo(root_dir, spikes_dir, name, url)
        
    console.print("[green]✔[/green] Sync complete.")

# Alias for list (showing configured repos) could be useful but not strictly asked for.
# Let's add a simple list command to see what we have.
@app.command("list")
def list_repos():
    """List configured repositories."""
    config = get_config()
    repos = config.project.spike_repos
    
    if not repos:
        console.print("[yellow]No repositories configured.[/yellow]")
        return
        
    for name, url in repos.items():
        console.print(f"- [bold]{name}[/bold]: {url}")
