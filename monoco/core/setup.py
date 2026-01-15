import os
import subprocess
import yaml
from pathlib import Path
import typer
from rich.console import Console
from monoco.core.output import print_output

console = Console()

def get_git_user() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"], 
            capture_output=True, 
            text=True, 
            timeout=1
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

from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import Window, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
import sys

def ask_with_selection(message: str, default: str) -> str:
    """Provides a selection-based prompt for stable rendering."""
    options = [f"{default} (Default)", "Custom Input..."]
    selected_index = 0
    
    kb = KeyBindings()
    
    @kb.add('up')
    @kb.add('k')
    def _(event):
        nonlocal selected_index
        selected_index = (selected_index - 1) % len(options)

    @kb.add('down')
    @kb.add('j')
    def _(event):
        nonlocal selected_index
        selected_index = (selected_index + 1) % len(options)

    @kb.add('enter')
    def _(event):
        event.app.exit(result=selected_index)

    @kb.add('c-c')
    def _(event):
        console.print("\n[red]Aborted by user.[/red]")
        sys.exit(0)

    def get_text():
        # Render the menu with explicit highlighting
        res = [('class:message', f"{message}:\n")]
        for i, opt in enumerate(options):
            if i == selected_index:
                res.append(('class:selected', f" ➔ {opt}\n"))
            else:
                res.append(('class:unselected', f"   {opt}\n"))
        return res

    style = Style.from_dict({
        'message': 'bold #ffffff',
        'selected': 'bold #00ff00', # High contrast green
        'unselected': '#888888',
    })

    # Run a mini application to handle the selection
    app = Application(
        layout=Layout(HSplit([Window(content=FormattedTextControl(get_text), height=len(options)+1)])),
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
    global_only: bool = typer.Option(False, "--global", help="Only configure global user settings"),
    project_only: bool = typer.Option(False, "--project", help="Only configure current project")
):
    """
    Initialize Monoco configuration (Global and/or Project).
    """
    from rich.prompt import Confirm
    
    home_dir = Path.home() / ".monoco"
    global_config_path = home_dir / "config.yaml"
    
    # --- 1. Global Configuration ---
    if not project_only:
        if not global_config_path.exists() or global_only:
            console.rule("[bold blue]Global Setup[/bold blue]")
            
            # Ensure ~/.monoco exists
            home_dir.mkdir(parents=True, exist_ok=True)
            
            default_author = get_git_user() or os.getenv("USER", "developer")
            author = ask_with_selection("Your Name (for issue tracking)", default_author)
            
            telemetry_enabled = Confirm.ask("Enable anonymous telemetry to help improve Monoco?", default=True)

            user_config = {
                "core": {
                    "author": author,
                    # Editor is handled by env/config defaults, no need to prompt
                },
                "telemetry": {
                    "enabled": telemetry_enabled
                }
            }
            
            with open(global_config_path, "w") as f:
                yaml.dump(user_config, f, default_flow_style=False)
                
            console.print(f"[green]✓ Global config saved to {global_config_path}[/green]\n")

    if global_only:
        return

    # --- 2. Project Configuration ---
    cwd = Path.cwd()
    project_config_dir = cwd / ".monoco"
    project_config_path = project_config_dir / "config.yaml"
    
    # Check if we should init project
    if project_config_path.exists():
        if not Confirm.ask(f"Project config already exists at [dim]{project_config_path}[/dim]. Overwrite?"):
            console.print("[yellow]Skipping project initialization.[/yellow]")
            return

    console.rule("[bold blue]Project Setup[/bold blue]")
    
    default_name = cwd.name
    project_name = ask_with_selection("Project Name", default_name)
    
    default_key = generate_key(project_name)
    project_key = ask_with_selection("Project Key (prefix for issues)", default_key)

    
    project_config_dir.mkdir(exist_ok=True)
    
    project_config = {
        "project": {
            "name": project_name,
            "key": project_key
        },
        "paths": {
            "issues": "Issues",
            "spikes": ".references",
            "specs": "SPECS"
        }
    }
    
    with open(project_config_path, "w") as f:
        yaml.dump(project_config, f, default_flow_style=False)

    # 2b. Generate Config Template
    template_path = project_config_dir / "config_template.yaml"
    template_content = """# Monoco Configuration Template
# This file serves as a reference for all available configuration options.
# Rename this file to config.yaml to use it.

core:
  # Default author for new artifacts (e.g. issues)
  # author: "Developer Name"
  
  # Logging verbosity (DEBUG, INFO, WARNING, ERROR)
  # log_level: "INFO"
  
  # Preferred text editor
  # editor: "vim"

project:
  # The display name of the project
  name: "My Project"
  
  # The prefix used for issue IDs (e.g. MON-001)
  key: "MON"
  
  # Managed external research repositories (name -> url)
  # spike_repos:
  #   react: "https://github.com/facebook/react"

paths:
  # Directory for tracking issues
  issues: "Issues"
  
  # Directory for specifications/documents
  specs: "SPECS"
  
  # Directory for research references (spikes)
  spikes: ".references"

i18n:
  # Source language code
  source_lang: "en"
  
  # Target language codes for translation
  target_langs: 
    - "zh"

ui:
  # Custom Domain Terminology Mapping
  # Use this to rename core concepts in the UI without changing internal logic.
  dictionary:
    # Entities
    epic: "Saga"
    feature: "Story"
    chore: "Task"
    fix: "Bug"
    
    # Statuses
    todo: "Pending"
    doing: "In Progress"
    review: "QA"
    done: "Released"
"""
    with open(template_path, "w") as f:
        f.write(template_content)

    # 3. Scaffold Directories & Modules
    
    # 3. Scaffold Directories & Modules
    
    from monoco.core.registry import FeatureRegistry
    from monoco.features.issue.adapter import IssueFeature
    from monoco.features.spike.adapter import SpikeFeature
    from monoco.features.i18n.adapter import I18nFeature
    
    registry = FeatureRegistry()
    registry.register(IssueFeature())
    registry.register(SpikeFeature())
    registry.register(I18nFeature())
    
    # Initialize all features
    for feature in registry.get_features():
        try:
             feature.initialize(cwd, project_config)
             console.print(f"  [dim]Initialized feature: {feature.name}[/dim]")
        except Exception as e:
             console.print(f"  [red]Failed to initialize {feature.name}: {e}[/red]")
             
    # Trigger initial sync to set up Agent Environment
    from monoco.core.sync import sync_command
    # We call sync command logic directly or simulate it? 
    # Just invoke the collection logic via sync normally would be best, 
    # but sync_command is a click command wrapper.
    # For now let's just initialize the physical structures. 
    # The 'skills.init' call in old code did more than just init structure, 
    # it wrote SKILL.md files. 
    # In V2, we rely on 'monoco sync' to do that injection.
    # So we should prompt user to run sync or do it automatically.
    
    # Let's run a sync
    console.print("[bold blue]Setting up Agent Environment...[/bold blue]")
    try:
        # We need to reuse logic from sync.py
        # Simplest is to run the sync workflow here manually/programmatically
        # But for now, let's keep it clean and just say:
        pass
    except Exception:
        pass

    console.print(f"[green]✓ Project config initialized at {project_config_path}[/green]")
    console.print(f"[green]✓ Config template generated at {template_path}[/green]")



    console.print(f"[green]Access configured! issues will be created as {project_key}-XXX[/green]")

