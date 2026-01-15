import os
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel

class ExecutionProfile(BaseModel):
    name: str
    source: str # "Global" or "Project"
    path: str
    content: Optional[str] = None

def scan_execution_profiles(project_root: Optional[Path] = None) -> List[ExecutionProfile]:
    """
    Scan for execution profiles (SOPs) in global and project scopes.
    """
    profiles = []
    
    # 1. Global Scope
    global_path = Path.home() / ".monoco" / "execution"
    if global_path.exists():
        profiles.extend(_scan_dir(global_path, "Global"))
        
    # 2. Project Scope
    if project_root:
        project_path = project_root / ".monoco" / "execution"
        if project_path.exists():
            profiles.extend(_scan_dir(project_path, "Project"))
            
    return profiles

def _scan_dir(base_path: Path, source: str) -> List[ExecutionProfile]:
    profiles = []
    if not base_path.is_dir():
        return profiles
        
    for item in base_path.iterdir():
        if item.is_dir():
            sop_path = item / "SOP.md"
            if sop_path.exists():
                profiles.append(ExecutionProfile(
                    name=item.name,
                    source=source,
                    path=str(sop_path.absolute())
                ))
    return profiles

def get_profile_detail(profile_path: str) -> Optional[ExecutionProfile]:
    path = Path(profile_path)
    if not path.exists():
        return None
        
    # Determine source (rough heuristic)
    source = "Project"
    if str(path).startswith(str(Path.home() / ".monoco")):
        source = "Global"
        
    return ExecutionProfile(
        name=path.parent.name,
        source=source,
        path=str(path.absolute()),
        content=path.read_text(encoding='utf-8')
    )
