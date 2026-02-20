"""
Core functionality for pretty-markdown feature.
"""

import json
import shutil
from pathlib import Path
from typing import Optional


# Template configurations
TEMPLATES = {
    "prettier": {
        ".prettierrc": "prettier/.prettierrc",
        ".prettierignore": "prettier/.prettierignore",
        "package.json": "prettier/package.json",
    },
    "markdownlint": {
        ".markdownlint.json": "markdownlint/.markdownlint.json",
        ".markdownlintignore": "markdownlint/.markdownlintignore",
    },
}


def get_template_path() -> Path:
    """Get the path to configuration templates."""
    # Find the project root by looking for pyproject.toml or .git
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            template_path = current / "resources" / "config-templates"
            if template_path.exists():
                return template_path
        current = current.parent
    
    # Fallback: try relative to this file
    return Path(__file__).parent.parent.parent.parent / "resources" / "config-templates"


def find_project_root(start_path: Optional[Path] = None) -> Path:
    """Find the project root by looking for .monoco directory."""
    if start_path is None:
        start_path = Path.cwd()
    
    current = start_path.resolve()
    while current != current.parent:
        if (current / ".monoco").exists():
            return current
        current = current.parent
    
    # Fallback to current directory
    return start_path


def sync_config(
    project_root: Optional[Path] = None,
    force: bool = False,
    templates: Optional[list[str]] = None,
) -> dict:
    """
    Sync configuration templates to the project.
    
    Args:
        project_root: Project root directory (auto-detected if None)
        force: Overwrite existing files if True
        templates: List of templates to sync ("prettier", "markdownlint", or None for all)
    
    Returns:
        Dict with sync results
    """
    if project_root is None:
        project_root = find_project_root()
    
    template_path = get_template_path()
    results = {
        "synced": [],
        "skipped": [],
        "errors": [],
    }
    
    templates_to_sync = templates or list(TEMPLATES.keys())
    
    for template_name in templates_to_sync:
        if template_name not in TEMPLATES:
            results["errors"].append(f"Unknown template: {template_name}")
            continue
        
        files = TEMPLATES[template_name]
        for target_name, source_rel_path in files.items():
            source_path = template_path / source_rel_path
            target_path = project_root / target_name
            
            if not source_path.exists():
                results["errors"].append(f"Source not found: {source_path}")
                continue
            
            if target_path.exists() and not force:
                results["skipped"].append(str(target_path.relative_to(project_root)))
                continue
            
            try:
                shutil.copy2(source_path, target_path)
                results["synced"].append(str(target_path.relative_to(project_root)))
            except Exception as e:
                results["errors"].append(f"Failed to copy {target_name}: {e}")
    
    return results


def check_config(project_root: Optional[Path] = None) -> dict:
    """
    Check if project configuration matches templates.
    
    Args:
        project_root: Project root directory (auto-detected if None)
    
    Returns:
        Dict with check results including diffs
    """
    if project_root is None:
        project_root = find_project_root()
    
    template_path = get_template_path()
    results = {
        "consistent": [],
        "different": [],
        "missing": [],
        "extras": [],
    }
    
    for template_name, files in TEMPLATES.items():
        for target_name, source_rel_path in files.items():
            source_path = template_path / source_rel_path
            target_path = project_root / target_name
            
            if not target_path.exists():
                results["missing"].append(target_name)
                continue
            
            if not source_path.exists():
                continue
            
            try:
                source_content = source_path.read_text()
                target_content = target_path.read_text()
                
                # Normalize JSON content for comparison
                if target_name.endswith(".json"):
                    try:
                        source_content = json.dumps(
                            json.loads(source_content), 
                            sort_keys=True, 
                            indent=2
                        )
                        target_content = json.dumps(
                            json.loads(target_content), 
                            sort_keys=True, 
                            indent=2
                        )
                    except json.JSONDecodeError:
                        pass  # Compare as text if JSON parsing fails
                
                if source_content.strip() == target_content.strip():
                    results["consistent"].append(target_name)
                else:
                    results["different"].append(target_name)
            except Exception as e:
                results["different"].append(f"{target_name} (error: {e})")
    
    # Check for extra config files that might be managed
    for target_name in [".prettierrc", ".prettierignore", ".markdownlint.json", ".markdownlintignore"]:
        target_path = project_root / target_name
        if target_path.exists():
            is_managed = any(
                target_name in files 
                for files in TEMPLATES.values()
            )
            if is_managed and target_name not in results["consistent"] and target_name not in results["different"]:
                # This shouldn't happen, but just in case
                pass
    
    return results


def enable_hook(project_root: Optional[Path] = None) -> bool:
    """
    Enable the pretty-markdown hook.
    
    Args:
        project_root: Project root directory
    
    Returns:
        True if successful
    """
    if project_root is None:
        project_root = find_project_root()
    
    hooks_dir = project_root / ".monoco" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Find the built-in hook - try multiple paths for different installation scenarios
    # Path 1: Development mode (src/monoco/features/hooks/resources/)
    builtin_hook = (
        Path(__file__).parent.parent / "hooks" / "resources" / "pretty-markdown.sh"
    )
    
    if not builtin_hook.exists():
        # Path 2: Alternative dev path
        builtin_hook = (
            Path(__file__).parent.parent.parent.parent / "src" / "monoco" / "features" / "hooks" / "resources" / "pretty-markdown.sh"
        )
    
    if not builtin_hook.exists():
        # Path 3: From project root
        builtin_hook = project_root / "src" / "monoco" / "features" / "hooks" / "resources" / "pretty-markdown.sh"
    
    if not builtin_hook.exists():
        return False
    
    target_hook = hooks_dir / "pretty-markdown.sh"
    
    try:
        shutil.copy2(builtin_hook, target_hook)
        # Make executable
        target_hook.chmod(0o755)
        return True
    except Exception:
        return False


def disable_hook(project_root: Optional[Path] = None) -> bool:
    """
    Disable the pretty-markdown hook.
    
    Args:
        project_root: Project root directory
    
    Returns:
        True if successful
    """
    if project_root is None:
        project_root = find_project_root()
    
    hook_path = project_root / ".monoco" / "hooks" / "pretty-markdown.sh"
    
    if hook_path.exists():
        try:
            hook_path.unlink()
            return True
        except Exception:
            return False
    
    return True  # Already disabled
