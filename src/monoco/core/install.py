"""
Monoco Install - Simplified Resource Distribution

Distributes three types of resources:
- AGENTS.md: System prompts (via md-patch)
- skills/{name}/: Skill packages
- hooks/{name}/: Hook packages

Usage:
    monoco install          # Install all to project
    monoco install -g       # Install all globally
    monoco install skills   # Install only skills
"""

import typer
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List
from enum import Enum
from rich.console import Console

from monoco.core.config import get_config

console = Console()


class InstallModule(str, Enum):
    """Available installable modules."""
    AGENTS = "agents"
    SKILLS = "skills"
    HOOKS = "hooks"


class InstallScope(str, Enum):
    """Installation scope: global or project."""
    GLOBAL = "global"
    PROJECT = "project"


def _get_target_paths(scope: InstallScope, root: Path) -> dict:
    """Get installation paths based on scope."""
    if scope == InstallScope.GLOBAL:
        home = Path.home()
        return {
            "agents": home / ".config" / "agents" / "AGENTS.md",
            "skills": home / ".config" / "agents" / "skills",
            "hooks": home / ".monoco" / "hooks",
        }
    else:
        return {
            "agents": root / "AGENTS.md",
            "skills": root / ".agents" / "skills",
            "hooks": root / ".monoco" / "hooks",
        }


def _find_resource_dirs(root: Path) -> List[Path]:
    """Find all resources directories from features."""
    resource_dirs = []
    
    # Try finding in current package structure (installed mode)
    features_dir = Path(__file__).parent.parent / "features"
    
    # Fallback to dev mode (project root)
    if not features_dir.exists():
        features_dir = root / "src" / "monoco" / "features"
    
    if features_dir.exists():
        for feature_dir in features_dir.iterdir():
            if feature_dir.is_dir() and not feature_dir.name.startswith("_"):
                resources_dir = feature_dir / "resources"
                if resources_dir.exists():
                    resource_dirs.append(resources_dir)
    
    return resource_dirs


def _get_agents_md(resources_dir: Path) -> Optional[Path]:
    """Get AGENTS.md path (flat structure preferred, fallback to lang subdir)."""
    # Prefer flat structure
    flat_path = resources_dir / "AGENTS.md"
    if flat_path.exists():
        return flat_path
    
    # Fallback to zh (default lang)
    zh_path = resources_dir / "zh" / "AGENTS.md"
    if zh_path.exists():
        return zh_path
    
    # Fallback to en
    en_path = resources_dir / "en" / "AGENTS.md"
    if en_path.exists():
        return en_path
    
    return None


def _get_skills_dir(resources_dir: Path) -> Optional[Path]:
    """Get skills directory (flat structure preferred, fallback to lang subdir)."""
    # Prefer flat structure
    flat_path = resources_dir / "skills"
    if flat_path.exists():
        return flat_path
    
    # Fallback to zh
    zh_path = resources_dir / "zh" / "skills"
    if zh_path.exists():
        return zh_path
    
    # Fallback to en
    en_path = resources_dir / "en" / "skills"
    if en_path.exists():
        return en_path
    
    return None


def _get_hooks_dir(resources_dir: Path) -> Optional[Path]:
    """Get hooks directory (flat structure preferred, fallback to lang subdir)."""
    # Prefer flat structure
    flat_path = resources_dir / "hooks"
    if flat_path.exists():
        return flat_path
    
    # Fallback to zh
    zh_path = resources_dir / "zh" / "hooks"
    if zh_path.exists():
        return zh_path
    
    # Fallback to en
    en_path = resources_dir / "en" / "hooks"
    if en_path.exists():
        return en_path
    
    return None


def _install_agents(
    scope: InstallScope,
    root: Path,
    resource_dirs: List[Path],
    force: bool = False,
) -> bool:
    """Install AGENTS.md using md-patch."""
    console.print("[bold blue]Installing AGENTS.md...[/bold blue]")
    
    target = _get_target_paths(scope, root)["agents"]
    target.parent.mkdir(parents=True, exist_ok=True)
    
    # Find AGENTS.md from resource directories
    agents_contents = []
    for resources_dir in resource_dirs:
        agents_file = _get_agents_md(resources_dir)
        if agents_file:
            try:
                content = agents_file.read_text(encoding="utf-8")
                agents_contents.append((agents_file.parent.parent.name, content))
            except Exception as e:
                console.print(f"[red]  Failed to read {agents_file}: {e}[/red]")
    
    if not agents_contents:
        console.print("[yellow]  No AGENTS.md found[/yellow]")
        return False
    
    # Combine all AGENTS.md content
    combined_content = "\n\n---\n\n".join([f"<!-- From {name} -->\n{content}" for name, content in agents_contents])
    
    # Use md-patch or direct write with safety check
    try:
        if target.exists():
            # Check if file contains Monoco marker
            existing = target.read_text(encoding="utf-8")
            if "<!-- MONOCO_MANAGED_START -->" in existing and not force:
                # Use simple append/update strategy
                # Remove old managed block and add new one
                lines = existing.split("\n")
                new_lines = []
                in_managed = False
                for line in lines:
                    if "<!-- MONOCO_MANAGED_START -->" in line:
                        in_managed = True
                        continue
                    if "<!-- MONOCO_MANAGED_END -->" in line:
                        in_managed = False
                        continue
                    if not in_managed:
                        new_lines.append(line)
                
                # Add new managed block
                managed_content = f"<!-- MONOCO_MANAGED_START -->\n{combined_content}\n<!-- MONOCO_MANAGED_END -->"
                final_content = "\n".join(new_lines).rstrip() + "\n\n" + managed_content
            else:
                # File exists but no marker, prepend with marker
                managed_content = f"<!-- MONOCO_MANAGED_START -->\n{combined_content}\n<!-- MONOCO_MANAGED_END -->"
                final_content = managed_content + "\n\n" + existing
        else:
            # New file
            final_content = f"<!-- MONOCO_MANAGED_START -->\n{combined_content}\n<!-- MONOCO_MANAGED_END -->"
        
        target.write_text(final_content, encoding="utf-8")
        console.print(f"[green]  ✓ Updated {target}[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]  Failed to write {target}: {e}[/red]")
        return False


def _install_skills(
    scope: InstallScope,
    root: Path,
    resource_dirs: List[Path],
    force: bool = False,
) -> bool:
    """Install skills/{name}/ directories."""
    console.print("[bold blue]Installing skills...[/bold blue]")
    
    target_dir = _get_target_paths(scope, root)["skills"]
    target_dir.mkdir(parents=True, exist_ok=True)
    
    installed = 0
    for resources_dir in resource_dirs:
        skills_dir = _get_skills_dir(resources_dir)
        if not skills_dir:
            continue
        
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            target_skill = target_dir / skill_dir.name
            try:
                if target_skill.exists():
                    shutil.rmtree(target_skill)
                shutil.copytree(skill_dir, target_skill)
                console.print(f"[dim]  ✓ Installed skill: {skill_dir.name}[/dim]")
                installed += 1
            except Exception as e:
                console.print(f"[red]  Failed to install {skill_dir.name}: {e}[/red]")
    
    if installed > 0:
        console.print(f"[green]  ✓ Installed {installed} skills to {target_dir}[/green]")
        return True
    else:
        console.print("[yellow]  No skills found[/yellow]")
        return False


def _install_hooks(
    scope: InstallScope,
    root: Path,
    resource_dirs: List[Path],
    force: bool = False,
) -> bool:
    """Install hooks/{name}/ directories."""
    if scope == InstallScope.GLOBAL:
        console.print("[yellow]Skipping hooks for global scope (project-specific)[/yellow]")
        return False
    
    console.print("[bold blue]Installing hooks...[/bold blue]")
    
    target_dir = _get_target_paths(scope, root)["hooks"]
    target_dir.mkdir(parents=True, exist_ok=True)
    
    installed = 0
    for resources_dir in resource_dirs:
        hooks_dir = _get_hooks_dir(resources_dir)
        if not hooks_dir:
            continue
        
        for hook_dir in hooks_dir.iterdir():
            if not hook_dir.is_dir():
                continue
            
            target_hook = target_dir / hook_dir.name
            try:
                if target_hook.exists():
                    shutil.rmtree(target_hook)
                shutil.copytree(hook_dir, target_hook)
                console.print(f"[dim]  ✓ Installed hook: {hook_dir.name}[/dim]")
                installed += 1
            except Exception as e:
                console.print(f"[red]  Failed to install {hook_dir.name}: {e}[/red]")
    
    if installed > 0:
        console.print(f"[green]  ✓ Installed {installed} hooks to {target_dir}[/green]")
        return True
    else:
        console.print("[yellow]  No hooks found[/yellow]")
        return False


def _uninstall_agents(scope: InstallScope, root: Path) -> bool:
    """Remove Monoco managed content from AGENTS.md."""
    console.print("[bold blue]Removing AGENTS.md managed content...[/bold blue]")
    
    target = _get_target_paths(scope, root)["agents"]
    if not target.exists():
        console.print("[dim]  AGENTS.md not found[/dim]")
        return False
    
    try:
        content = target.read_text(encoding="utf-8")
        lines = content.split("\n")
        new_lines = []
        in_managed = False
        
        for line in lines:
            if "<!-- MONOCO_MANAGED_START -->" in line:
                in_managed = True
                continue
            if "<!-- MONOCO_MANAGED_END -->" in line:
                in_managed = False
                continue
            if not in_managed:
                new_lines.append(line)
        
        final_content = "\n".join(line for line in new_lines if line.strip())
        
        if final_content.strip():
            target.write_text(final_content + "\n", encoding="utf-8")
        else:
            target.unlink()
            console.print(f"[dim]  Removed empty {target}[/dim]")
            
        console.print("[green]  ✓ Removed managed content[/green]")
        return True
    except Exception as e:
        console.print(f"[red]  Failed: {e}[/red]")
        return False


def _uninstall_skills(scope: InstallScope, root: Path) -> bool:
    """Remove all installed skills."""
    console.print("[bold blue]Removing skills...[/bold blue]")
    
    target_dir = _get_target_paths(scope, root)["skills"]
    if not target_dir.exists():
        console.print("[dim]  Skills directory not found[/dim]")
        return False
    
    try:
        shutil.rmtree(target_dir)
        console.print(f"[green]  ✓ Removed {target_dir}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]  Failed: {e}[/red]")
        return False


def _uninstall_hooks(scope: InstallScope, root: Path) -> bool:
    """Remove all installed hooks."""
    console.print("[bold blue]Removing hooks...[/bold blue]")
    
    if scope == InstallScope.GLOBAL:
        console.print("[dim]  Skipping global hooks[/dim]")
        return False
    
    target_dir = _get_target_paths(scope, root)["hooks"]
    if not target_dir.exists():
        console.print("[dim]  Hooks directory not found[/dim]")
        return False
    
    try:
        shutil.rmtree(target_dir)
        console.print(f"[green]  ✓ Removed {target_dir}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]  Failed: {e}[/red]")
        return False


def install_command(
    ctx: typer.Context,
    modules: Optional[List[str]] = typer.Argument(
        None,
        help="Modules to install (agents, skills, hooks). If not specified, installs all.",
    ),
    global_scope: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Install to global scope (~/.config/agents/)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite existing files",
    ),
):
    """
    Install Monoco resources (AGENTS.md, skills, hooks).
    
    Examples:
        monoco install              # Install all to project
        monoco install -g           # Install all globally
        monoco install skills       # Install only skills
        monoco install agents hooks # Install specific modules
    """
    root = Path.cwd()
    config = get_config(str(root))
    
    # Determine scope
    scope = InstallScope.GLOBAL if global_scope else InstallScope.PROJECT
    
    # Determine modules to install
    if not modules:
        modules_to_install = list(InstallModule)
    else:
        modules_to_install = []
        for m in modules:
            try:
                modules_to_install.append(InstallModule(m.lower()))
            except ValueError:
                console.print(f"[red]Unknown module: {m}[/red]")
                raise typer.Exit(code=1)
    
    # Find resource directories
    resource_dirs = _find_resource_dirs(root)
    
    if not resource_dirs:
        console.print("[yellow]No resource directories found[/yellow]")
        raise typer.Exit(code=0)
    
    console.print(f"[bold]Installing to {scope.value} scope...[/bold]")
    console.print(f"[dim]Found {len(resource_dirs)} resource directories[/dim]")
    
    results = []
    
    for module in modules_to_install:
        if module == InstallModule.AGENTS:
            results.append(_install_agents(scope, root, resource_dirs, force))
        elif module == InstallModule.SKILLS:
            results.append(_install_skills(scope, root, resource_dirs, force))
        elif module == InstallModule.HOOKS:
            results.append(_install_hooks(scope, root, resource_dirs, force))
    
    if any(results):
        console.print("[bold green]Installation complete[/bold green]")
    else:
        console.print("[yellow]Nothing was installed[/yellow]")


def uninstall_command(
    ctx: typer.Context,
    modules: Optional[List[str]] = typer.Argument(
        None,
        help="Modules to uninstall (agents, skills, hooks). If not specified, uninstalls all.",
    ),
    global_scope: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Uninstall from global scope",
    ),
):
    """
    Uninstall Monoco resources.
    
    Examples:
        monoco uninstall        # Uninstall all from project
        monoco uninstall -g     # Uninstall all globally
        monoco uninstall skills # Uninstall only skills
    """
    root = Path.cwd()
    scope = InstallScope.GLOBAL if global_scope else InstallScope.PROJECT
    
    # Determine modules
    if not modules:
        modules_to_uninstall = list(InstallModule)
    else:
        modules_to_uninstall = []
        for m in modules:
            try:
                modules_to_uninstall.append(InstallModule(m.lower()))
            except ValueError:
                console.print(f"[red]Unknown module: {m}[/red]")
                raise typer.Exit(code=1)
    
    console.print(f"[bold]Uninstalling from {scope.value} scope...[/bold]")
    
    results = []
    
    for module in modules_to_uninstall:
        if module == InstallModule.AGENTS:
            results.append(_uninstall_agents(scope, root))
        elif module == InstallModule.SKILLS:
            results.append(_uninstall_skills(scope, root))
        elif module == InstallModule.HOOKS:
            results.append(_uninstall_hooks(scope, root))
    
    if any(results):
        console.print("[bold green]Uninstallation complete[/bold green]")
    else:
        console.print("[yellow]Nothing was uninstalled[/yellow]")
