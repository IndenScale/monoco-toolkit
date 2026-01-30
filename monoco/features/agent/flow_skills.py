"""
Flow Skills Manager for Monoco Scheduler.

This module provides management and injection of standard Agent workflow skills
(Flow Skills) following the Kimi CLI Flow Skill format.

Note: This module is now a thin wrapper around SkillManager for backward compatibility.
New code should use SkillManager directly for multi-skill architecture support.

Key Responsibilities:
1. Discover flow skills from resources/skills/ directory
2. Inject flow skills to target agent framework directories
3. Handle .gitignore updates for injected skills
"""

import shutil
from pathlib import Path
from typing import List, Set
from rich.console import Console

console = Console()

# Prefix for injected flow skills to avoid conflicts
FLOW_SKILL_PREFIX = "monoco_flow_"

# Gitignore pattern for flow skills
GITIGNORE_PATTERN = f"{FLOW_SKILL_PREFIX}*/"


def discover_flow_skills(resources_dir: Path) -> List[Path]:
    """
    Discover all flow skill directories in the resources/skills/ directory.

    Flow skills are identified by either:
    1. Directory name starting with "flow_" (legacy pattern)
    2. SKILL.md containing "type: flow" in front matter (new pattern)

    Args:
        resources_dir: Path to the resources directory (e.g., monoco/features/scheduler/resources/)

    Returns:
        List of paths to flow skill directories
    """
    skills_dir = resources_dir / "skills"
    if not skills_dir.exists():
        return []

    flow_skills = []
    for item in skills_dir.iterdir():
        if not item.is_dir():
            continue

        skill_file = item / "SKILL.md"
        if not skill_file.exists():
            continue

        # Check legacy pattern: directory starts with "flow_"
        if item.name.startswith("flow_"):
            flow_skills.append(item)
            continue

        # Check new pattern: SKILL.md contains "type: flow" in front matter
        try:
            content = skill_file.read_text(encoding="utf-8")
            # Look for type: flow in front matter (between --- markers)
            if content.startswith("---"):
                front_matter_end = content.find("---", 3)
                if front_matter_end != -1:
                    front_matter = content[3:front_matter_end]
                    if "type: flow" in front_matter:
                        flow_skills.append(item)
        except Exception:
            pass  # Skip files that can't be read

    return sorted(flow_skills)


def inject_flow_skill(
    skill_dir: Path, target_dir: Path, prefix: str = FLOW_SKILL_PREFIX
) -> bool:
    """
    Inject a single flow skill to the target directory.

    Args:
        skill_dir: Source flow skill directory (e.g., .../flow_engineer/)
        target_dir: Target directory for skill injection (e.g., .agent/skills/)
        prefix: Prefix to add to the skill directory name

    Returns:
        True if injection successful, False otherwise
    """
    try:
        # Calculate target skill name with prefix
        # e.g., flow_engineer -> monoco_flow_engineer
        target_skill_name = f"{prefix}{skill_dir.name}"
        target_skill_dir = target_dir / target_skill_name

        # Remove existing skill directory if present
        if target_skill_dir.exists():
            shutil.rmtree(target_skill_dir)

        # Copy skill directory
        shutil.copytree(skill_dir, target_skill_dir)

        console.print(f"[green]  ✓ Injected {target_skill_name}/[/green]")
        return True

    except Exception as e:
        console.print(f"[red]  ✗ Failed to inject {skill_dir.name}: {e}[/red]")
        return False


def sync_flow_skills(
    resources_dir: Path,
    target_dir: Path,
    prefix: str = FLOW_SKILL_PREFIX,
    force: bool = False,
) -> dict:
    """
    Synchronize all flow skills from resources to target directory.

    This function:
    1. Discovers all flow skills in resources/skills/
    2. Injects them to target_dir with the specified prefix
    3. Optionally removes skills that no longer exist in source

    Args:
        resources_dir: Path to the resources directory
        target_dir: Target directory for skill injection (e.g., .agent/skills/)
        prefix: Prefix to add to skill directory names
        force: Force re-injection even if skills already exist

    Returns:
        Dictionary with 'injected', 'failed', 'removed' counts
    """
    results = {"injected": 0, "failed": 0, "removed": 0}

    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # Discover flow skills
    flow_skills = discover_flow_skills(resources_dir)

    if not flow_skills:
        console.print("[yellow]No flow skills found in resources[/yellow]")
        return results

    console.print(f"[dim]Found {len(flow_skills)} flow skill(s)[/dim]")

    # Track expected skill names
    expected_skills: Set[str] = set()

    # Inject each flow skill
    for skill_dir in flow_skills:
        target_skill_name = f"{prefix}{skill_dir.name}"
        expected_skills.add(target_skill_name)

        # Check if already exists and not force
        target_skill_dir = target_dir / target_skill_name
        if target_skill_dir.exists() and not force:
            # Check if source is newer
            source_mtime = (skill_dir / "SKILL.md").stat().st_mtime
            target_mtime = (target_skill_dir / "SKILL.md").stat().st_mtime

            if source_mtime <= target_mtime:
                console.print(f"[dim]  = {target_skill_name}/ is up to date[/dim]")
                continue

        if inject_flow_skill(skill_dir, target_dir, prefix):
            results["injected"] += 1
        else:
            results["failed"] += 1

    # Clean up orphaned skills (optional, when force=True)
    if force:
        for item in target_dir.iterdir():
            if item.is_dir() and item.name.startswith(prefix):
                if item.name not in expected_skills:
                    shutil.rmtree(item)
                    console.print(f"[dim]  - Removed orphaned {item.name}/[/dim]")
                    results["removed"] += 1

    return results


def update_gitignore(project_root: Path, pattern: str = GITIGNORE_PATTERN) -> bool:
    """
    Add flow skill pattern to .gitignore if not present.

    Args:
        project_root: Project root directory
        pattern: Gitignore pattern to add

    Returns:
        True if .gitignore was updated or already contains pattern
    """
    gitignore_path = project_root / ".gitignore"

    try:
        # Read existing content
        if gitignore_path.exists():
            content = gitignore_path.read_text(encoding="utf-8")
            lines = content.splitlines()
        else:
            lines = []

        # Check if pattern already exists
        for line in lines:
            if line.strip() == pattern or line.strip() == f"/{pattern}":
                return True

        # Add pattern with comment
        comment = "# Monoco Flow Skills (auto-generated)"
        new_lines = [comment, pattern, ""]

        # Append to file
        with open(gitignore_path, "a", encoding="utf-8") as f:
            # Add newline if file doesn't end with one
            if lines and not content.endswith("\n"):
                f.write("\n")
            f.write("\n".join(new_lines))

        console.print(f"[green]  ✓ Updated .gitignore with {pattern}[/green]")
        return True

    except Exception as e:
        console.print(f"[red]  ✗ Failed to update .gitignore: {e}[/red]")
        return False


def remove_flow_skills(target_dir: Path, prefix: str = FLOW_SKILL_PREFIX) -> int:
    """
    Remove all injected flow skills from target directory.

    Args:
        target_dir: Target directory (e.g., .agent/skills/)
        prefix: Prefix used for flow skill directories

    Returns:
        Number of skills removed
    """
    if not target_dir.exists():
        return 0

    removed_count = 0
    for item in target_dir.iterdir():
        if item.is_dir() and item.name.startswith(prefix):
            shutil.rmtree(item)
            console.print(f"[green]  ✓ Removed {item.name}/[/green]")
            removed_count += 1

    return removed_count


def get_flow_skill_commands(target_dir: Path, prefix: str = FLOW_SKILL_PREFIX) -> List[str]:
    """
    Get list of available flow skill commands.

    In Kimi CLI, flow skills are invoked via /flow:<role> command.
    This function extracts the role names from injected flow skills.

    Args:
        target_dir: Target directory (e.g., .agent/skills/)
        prefix: Prefix used for flow skill directories

    Returns:
        List of available /flow:<role> commands
    """
    if not target_dir.exists():
        return []

    commands = []
    for item in target_dir.iterdir():
        if item.is_dir() and item.name.startswith(prefix):
            # Extract role from directory name
            # e.g., monoco_flow_engineer -> engineer
            role = item.name[len(prefix) + 5:]  # Remove prefix + "flow_"
            if role:
                commands.append(f"/flow:{role}")

    return sorted(commands)
