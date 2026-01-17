import shutil
import os
from pathlib import Path
from typing import List
try:
    from importlib.resources import files
except ImportError:
    # Fallback for python < 3.9
    from importlib_resources import files

def init_agent_resources(project_root: Path):
    """
    Initialize Agent resources (prompts) in the project workspace.
    """
    actions_dir = project_root / ".monoco" / "actions"
    actions_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine language from config, default to 'en'
    # We need to load config to know the language. 
    # But this function might be called before full config load?
    # Helper to peek at config or default to 'en'
    from monoco.core.config import get_config
    try:
        settings = get_config(str(project_root), require_project=False) # Best effort
        lang = settings.core.language or "en"
    except Exception:
        lang = "en"

    # Define source path relative to this module
    try:
        current_dir = Path(__file__).parent
        
        # Try specific language, fallback to 'en'
        source_dir = current_dir / "resources" / lang
        if not source_dir.exists():
             source_dir = current_dir / "resources" / "en"
        
        if source_dir.exists():
            for item in source_dir.glob("*.prompty"):
                target = actions_dir / item.name
                # Copy if not exists, or overwrite? 
                # Ideally init should be safe to run multiple times (idempotent)
                # But user might have customized them.
                if not target.exists():
                     shutil.copy2(item, target)
    except Exception as e:
        # Fallback or Log?
        pass
