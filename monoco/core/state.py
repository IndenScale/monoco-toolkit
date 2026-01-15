from pathlib import Path
from typing import Optional, Any, Dict
import json
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger("monoco.core.state")

class WorkspaceState(BaseModel):
    """
    Persisted state for a Monoco workspace (collection of projects).
    Stored in <workspace_root>/.monoco/state.json
    """
    last_active_project_id: Optional[str] = None
    
    @classmethod
    def load(cls, workspace_root: Path) -> "WorkspaceState":
        state_file = workspace_root / ".monoco" / "state.json"
        if not state_file.exists():
            return cls()
            
        try:
            content = state_file.read_text(encoding='utf-8')
            if not content.strip():
                return cls()
            data = json.loads(content)
            return cls(**data)
        except Exception as e:
            logger.error(f"Failed to load workspace state from {state_file}: {e}")
            return cls()

    def save(self, workspace_root: Path):
        state_file = workspace_root / ".monoco" / "state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # We merge with existing on disk if possible to preserve unknown keys
            current_data = {}
            if state_file.exists():
                try:
                    content = state_file.read_text(encoding='utf-8')
                    if content.strip():
                        current_data = json.loads(content)
                except:
                    pass
            
            new_data = self.model_dump(exclude_unset=True)
            current_data.update(new_data)
            
            state_file.write_text(json.dumps(current_data, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to save workspace state to {state_file}: {e}")
            raise
