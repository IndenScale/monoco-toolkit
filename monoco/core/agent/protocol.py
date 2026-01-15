"""
Protocol definition for Agent Clients.
"""

from typing import Protocol, List, Optional
from pathlib import Path

class AgentClient(Protocol):
    """Protocol for interacting with CLI-based agents."""
    
    @property
    def name(self) -> str:
        """Name of the agent provider (e.g. 'gemini', 'claude')."""
        ...

    async def available(self) -> bool:
        """Check if the agent is available in the current environment."""
        ...

    async def execute(self, prompt: str, context_files: List[Path] = []) -> str:
        """
        Execute a prompt against the agent.
        
        Args:
            prompt: The main instructions.
            context_files: List of files to provide as context.
            
        Returns:
            The raw string response from the agent.
        """
        ...
