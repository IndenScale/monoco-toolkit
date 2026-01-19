from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class IntegrationData:
    """
    Data collection returned by a feature for integration into the Agent environment.
    """

    # System Prompts to be injected into agent configuration (e.g., .cursorrules)
    # Key: Section Title (e.g., "Issue Management"), Value: Markdown Content
    system_prompts: Dict[str, str] = field(default_factory=dict)

    # Paths to skill directories or files to be copied/symlinked
    # DEPRECATED: Skill distribution is cancelled. Only prompts are synced.
    skills: List[Path] = field(default_factory=list)


class MonocoFeature(ABC):
    """
    Abstract base class for all Monoco features.
    Features must implement this protocol to participate in init and sync lifecycles.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the feature (e.g., 'issue', 'spike')."""
        pass

    @abstractmethod
    def initialize(self, root: Path, config: Dict) -> None:
        """
        Lifecycle hook: Physical Structure Initialization.
        Called during `monoco init`.
        Responsible for creating necessary directories, files, and config templates.

        Args:
            root: The root directory of the project.
            config: The full project configuration dictionary.
        """
        pass

    @abstractmethod
    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        """
        Lifecycle hook: Agent Environment Integration.
        Called during `monoco sync`.
        Responsible for returning data (prompts, skills) needed for the Agent Setup.

        Args:
            root: The root directory of the project.
            config: The full project configuration dictionary.

        Returns:
            IntegrationData object containing prompts and skills.
        """
        pass
