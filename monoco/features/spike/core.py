import os
import shutil
import subprocess
import yaml
from pathlib import Path
from typing import Dict, Optional, List, Any
from rich.console import Console

from monoco.core.config import get_config

console = Console()

def run_git_command(cmd: List[str], cwd: Path) -> bool:
    """Run a git command in the specified directory."""
    try:
        subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Git Error:[/red] {' '.join(cmd)}\n{e.stderr}")
        return False
    except FileNotFoundError:
        console.print("[red]Error:[/red] git command not found.")
        return False

def get_config_file_path(root: Path) -> Path:
    """Determine the config file to update."""
    # Standard: .monoco/project.yaml
    hidden = root / ".monoco" / "project.yaml"
    
    # Ensure parent exists
    hidden.parent.mkdir(exist_ok=True)
    return hidden

def update_config_repos(root: Path, repo_name: str, repo_url: str, remove: bool = False):
    """Update the repos list in the config file."""
    config_path = get_config_file_path(root)
    
    data = {}
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            data = {}
            
    # Ensure structure exists
    if "project" not in data:
        data["project"] = {}
    if "spike_repos" not in data["project"]:
        data["project"]["spike_repos"] = {}
        
    if remove:
        if repo_name in data["project"]["spike_repos"]:
            del data["project"]["spike_repos"][repo_name]
    else:
        data["project"]["spike_repos"][repo_name] = repo_url
        
    with open(config_path, "w") as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False)

def ensure_gitignore(root: Path, target_dir_name: str):
    """Ensure the target directory is in .gitignore."""
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(f"{target_dir_name}/\n")
        return

    content = gitignore.read_text()
    if f"{target_dir_name}/" not in content and f"{target_dir_name}" not in content:
        # Avoid redundant newlines if file ends with one
        prefix = "\n" if content and not content.endswith("\n") else ""
        with open(gitignore, "a") as f:
            f.write(f"{prefix}{target_dir_name}/\n")

def sync_repo(root: Path, spikes_dir: Path, name: str, url: str):
    """Clone or Pull a repo."""
    target_path = spikes_dir / name
    
    if target_path.exists() and (target_path / ".git").exists():
        console.print(f"Updating [bold]{name}[/bold]...")
        run_git_command(["git", "pull"], cwd=target_path)
    else:
        # If dir exists but not a git repo, warn or error? 
        # For safety, if non-empty and not git, skip or error.
        if target_path.exists() and any(target_path.iterdir()):
             console.print(f"[yellow]Skipping {name}:[/yellow] Directory exists and is not empty, but not a git repo.")
             return

        console.print(f"Cloning [bold]{name}[/bold]...")
        target_path.mkdir(parents=True, exist_ok=True)
        run_git_command(["git", "clone", url, "."], cwd=target_path)

def remove_repo_dir(spikes_dir: Path, name: str):
    """Physically remove the repo directory."""
    target_path = spikes_dir / name

    if target_path.exists():
        shutil.rmtree(target_path)

SKILL_CONTENT = """---
name: git-repo-spike
description: Manage external Git repositories as References in `.reference/`.
---

# Git Repo Spike (Reference Management)

This skill normalizes how we introduce external code repositories.

## Core Principles
1. **Read-Only**: Code in `.reference/` is for reference only.
2. **Isolation**: All external repos sit within `.reference/`.
3. **VCS Hygiene**: `.reference/` is gitignored. We track the intent to clone, not the files.

## Workflow
1. **Add**: `monoco spike add <url>`
2. **Sync**: `monoco spike sync` (Clones/Pulls all repos)
3. **Remove**: `monoco spike remove <name>`
"""

def init(root: Path, spikes_dir_name: str):
    """Initialize Spike environment."""
    ensure_gitignore(root, spikes_dir_name)
    (root / spikes_dir_name).mkdir(exist_ok=True)

    return {
        "skills": {
            "git-repo-spike": SKILL_CONTENT
        },
        "prompts": {} # Handled by adapter via resource files
    }
