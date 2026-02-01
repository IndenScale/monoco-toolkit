from pathlib import Path
from typing import Dict
from monoco.core.loader import FeatureModule, FeatureMetadata
from monoco.core.feature import IntegrationData
from monoco.features.spike import core


class SpikeFeature(FeatureModule):
    """Spike (research) feature module with unified lifecycle support."""

    @property
    def metadata(self) -> FeatureMetadata:
        return FeatureMetadata(
            name="spike",
            version="1.0.0",
            description="Research spike management for external references",
            dependencies=["core"],
            priority=30,
        )

    def _on_mount(self, context: "FeatureContext") -> None:  # type: ignore
        """Initialize spike feature with workspace context."""
        root = context.root
        config = context.config
        spikes_name = config.get("paths", {}).get("spikes", ".references")
        core.init(root, spikes_name)

    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        """Provide integration data for agent environment."""
        # Determine language from config, default to 'en'
        lang = config.get("i18n", {}).get("source_lang", "en")
        base_dir = Path(__file__).parent / "resources"

        prompt_file = base_dir / lang / "AGENTS.md"
        if not prompt_file.exists():
            prompt_file = base_dir / "en" / "AGENTS.md"

        content = ""
        if prompt_file.exists():
            content = prompt_file.read_text(encoding="utf-8").strip()

        return IntegrationData(system_prompts={"Spike (Research)": content})
