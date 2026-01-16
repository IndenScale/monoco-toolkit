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
        """Run diagnostics on all integrations and update state."""
        logger.info("Refreshing agent state...")
        
        from monoco.core.integrations import get_all_integrations
        from monoco.core.config import get_config
        
        # Load config to get possible overrides
        # Determine root (hacky for now, should be passed)
        root = Path.cwd()
        config = get_config(str(root))
        
        integrations = get_all_integrations(config_overrides=config.agent.integrations, enabled_only=True)
        
        providers = {}
        for key, integration in integrations.items():
            if not integration.bin_name:
                continue # Skip integrations that don't have a binary component
            
            health = integration.check_health()
            providers[key] = AgentProviderState(
                available=health.available,
                path=health.path,
                error=health.error,
                latency_ms=health.latency_ms
            )
            
        state = AgentState(
            last_checked=datetime.now(timezone.utc),
            providers=providers
        )
        
        # Save state
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            yaml.dump(state.model_dump(mode='json'), f)
            
        self._state = state
        return state

    def _find_script(self) -> Optional[Path]:
        """[Deprecated] No longer used."""
        return None
