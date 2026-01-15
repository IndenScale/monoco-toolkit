"""
Agent State Management.

Handles persistence and retrieval of agent availability state.
"""

import yaml
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("monoco.core.agent.state")

class AgentProviderState(BaseModel):
    available: bool
    path: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None

class AgentState(BaseModel):
    last_checked: datetime
    providers: Dict[str, AgentProviderState]

    @property
    def is_stale(self) -> bool:
        """Check if the state is older than 7 days."""
        delta = datetime.now(timezone.utc) - self.last_checked
        return delta.days > 7

class AgentStateManager:
    def __init__(self, state_path: Path = Path.home() / ".monoco" / "agent_state.yaml"):
        self.state_path = state_path
        self._state: Optional[AgentState] = None

    def load(self) -> Optional[AgentState]:
        """Load state from file, returning None if missing or invalid."""
        if not self.state_path.exists():
            return None
        
        try:
            with open(self.state_path, "r") as f:
                data = yaml.safe_load(f)
                if not data:
                    return None
                # Handle ISO string to datetime conversion if needed provided by Pydantic mostly
                return AgentState(**data)
        except Exception as e:
            logger.warning(f"Failed to load agent state: {e}")
            return None

    def get_or_refresh(self, force: bool = False) -> AgentState:
        """Get current state, refreshing if missing, stale, or forced."""
        if not force:
            self._state = self.load()
            if self._state and not self._state.is_stale:
                return self._state
        
        return self.refresh()

    def refresh(self) -> AgentState:
        """Run the diagnostic script and update state file."""
        logger.info("Refreshing agent state...")
        
        # Locate the shell script
        # Assuming monoco is installed as a package, we need to find where the script lives.
        # For dev environment: Toolkit/scripts/check_agents.sh
        # For production: It might need to be packaged or generated.
        
        # Current strategy: Look in known relative locations
        script_path = self._find_script()
        if not script_path:
            raise FileNotFoundError("Could not find check_agents.sh script")

        try:
            # Ensure the directory exists
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            
            subprocess.run(
                [str(script_path), str(self.state_path)], 
                check=True, 
                capture_output=True,
                text=True
            )
            
            # Reload to get the object
            state = self.load()
            if not state:
                raise ValueError("Script ran but state file is invalid or empty")
            
            self._state = state
            return state
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Agent check script failed: {e.stderr}")
            raise RuntimeError(f"Agent check failed: {e.stderr}") from e

    def _find_script(self) -> Optional[Path]:
        """Find the check_agents.sh script."""
        # Check dev path relative to this file
        # this file: monoco/core/agent/state.py
        # root: monoco/../../
        
        current_file = Path(__file__).resolve()
        
        # Strategy 1: Development logic (Toolkit/scripts/check_agents.sh)
        dev_path = current_file.parents[3] / "scripts" / "check_agents.sh"
        if dev_path.exists():
            return dev_path
            
        # Strategy 2: If installed in site-packages, maybe we package scripts nearby?
        # TODO: Define packaging strategy for scripts
        
        return None
