import os
import re
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console

console = Console()

def init(root: Path, resources: List[Dict[str, Any]]):
    """
    Initialize the Skills module.
    
    Args:
        root: Project root directory.
        resources: List of resource dicts from modules. 
                   Expected format: 
                   {
                       "skills": { "name": "content" },
                       "prompts": { "name": "content" } 
                   }
    """
    skills_root = root / "Toolkit" / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    
    # 1. Write Skills
    for res in resources:
        if "skills" in res:
            for name, content in res["skills"].items():
                target_dir = skills_root / name
                target_dir.mkdir(exist_ok=True)
                target_file = target_dir / "SKILL.md"
                # Idempotency: Overwrite if content is different? Or just always overwrite?
                # User asked for "scaffold", implies creation. 
                # Let's overwrite to ensure extensive "Repair" capability.
                target_file.write_text(content, encoding="utf-8")
                console.print(f"[dim]  - Scaffolding skill:[/dim] {name}")

    # 2. Update Agent Docs
    update_agent_docs(root, resources)

def update_agent_docs(root: Path, resources: List[Dict[str, Any]]):
    """
    Inject prompts into AGENTS.md, GEMINI.md, CLAUDE.md.
    """
    target_files = ["AGENTS.md", "GEMINI.md", "CLAUDE.md"]
    
    # Aggregate Prompts
    aggregated_prompt = "\n\n".join([
        res["prompts"][name] 
        for res in resources 
        if "prompts" in res 
        for name in res["prompts"]
    ])
    
    injection_content = f"""
## Monoco Toolkit

The following tools and skills are available in this environment.

{aggregated_prompt}
"""

    for filename in target_files:
        _inject_section(root / filename, injection_content)

def _inject_section(file_path: Path, content: str):
    if not file_path.exists():
        # Create if not exists? User said "Edit AGENTS.md...", implies existence.
        # But if we init in a fresh repo, maybe we should create them?
        # Let's create if missing.
        file_path.write_text(f"# Project Guidelines\n{content}", encoding="utf-8")
        console.print(f"[green]✔[/green] Created {file_path.name}")
        return

    original_content = file_path.read_text(encoding="utf-8")
    
    # Regex to find existing section
    # Matches ## Monoco Toolkit ... until next ## or End of String
    pattern = r"(## Monoco Toolkit.*?)(\n## |\Z)"
    
    # Check if section exists
    if re.search(pattern, original_content, re.DOTALL):
        # Replace
        new_content = re.sub(pattern, f"{content.strip()}\n\n\\2", original_content, flags=re.DOTALL)
        if new_content != original_content:
            file_path.write_text(new_content, encoding="utf-8")
            console.print(f"[green]✔[/green] Updated {file_path.name}")
        else:
            console.print(f"[dim]  - {file_path.name} is up to date.[/dim]")
    else:
        # Append
        with open(file_path, "a", encoding="utf-8") as f:
            if not original_content.endswith("\n"):
                f.write("\n")
            f.write(content)
        console.print(f"[green]✔[/green] Appended to {file_path.name}")
