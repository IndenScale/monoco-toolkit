from pathlib import Path
from typing import Dict
from monoco.core.loader import FeatureModule, FeatureMetadata
from monoco.core.feature import IntegrationData


class BrowserFeature(FeatureModule):
    """
    Intelligent Browser integration for Monoco.
    
    Provides agent-browser CLI guidance and smart hooks for web-related tasks.
    """

    @property
    def metadata(self) -> FeatureMetadata:
        return FeatureMetadata(
            name="browser",
            version="1.0.0",
            description="Intelligent browser integration and smart hooks",
            dependencies=["core"],
            priority=50,
        )

    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        """Provide integration data (Skills) for the agent environment."""
        # Find the skill file (usually in .claude/skills/monoco_browser/SKILL.md)
        # However, for features, we can also maintain a copy of the skill in resources.
        
        # For now, we reuse the existing skill path if it exists, 
        # but the primary value here is the Hooks distribution which happens automatically
        # by the hook scanner looking into resources/hooks.
        return IntegrationData()
