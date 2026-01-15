from pathlib import Path
from typing import List, Optional

def is_project_root(path: Path) -> bool:
    """
    Check if a directory serves as a Monoco project root.
    Criteria:
    - has .monoco/ directory
    """
    if not path.is_dir():
        return False
        
    return (path / ".monoco").is_dir()

def find_projects(workspace_root: Path) -> List[Path]:
    """
    Scan for projects in a workspace.
    Returns list of paths that are project roots.
    """
    projects = []
    
    # 1. Check workspace root itself
    if is_project_root(workspace_root):
        projects.append(workspace_root)
    
    # 2. Check first-level subdirectories
    # Prevent scanning giant node_modules or .git
    for item in workspace_root.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            if is_project_root(item):
                # If workspace root is also a project, we might deduce duplicates
                # But here we just append items. 
                # If workspace_root == item (impossible for iterdir child), no risk.
                projects.append(item)
                
    return projects
