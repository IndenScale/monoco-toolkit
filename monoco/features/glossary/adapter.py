from pathlib import Path
from typing import Dict
from monoco.core.loader import FeatureModule, FeatureMetadata
from monoco.core.feature import IntegrationData


class GlossaryFeature(FeatureModule):
    """Glossary feature module with unified lifecycle support."""

    @property
    def metadata(self) -> FeatureMetadata:
        return FeatureMetadata(
            name="glossary",
            version="1.0.0",
            description="Terminology and glossary management",
            dependencies=["core"],
            priority=60,
            lazy=True,  # Can be lazy loaded - not critical for startup
        )

    def _on_mount(self, context: "FeatureContext") -> None:  # type: ignore
        """Glossary does not require file initialization in the workspace."""
        pass

    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        """Provide integration data for agent environment."""
        # Determine language from config, default to 'en'
        lang = config.get("i18n", {}).get("source_lang", "en")

        # Resource path: monoco/features/glossary/resources/{lang}/AGENTS.md
        base_dir = Path(__file__).parent / "resources"

        # Try specific language, fallback to 'en'
        prompt_file = base_dir / lang / "AGENTS.md"
        if not prompt_file.exists():
            prompt_file = base_dir / "en" / "AGENTS.md"

        content = ""
        if prompt_file.exists():
            content = prompt_file.read_text(encoding="utf-8").strip()

        return IntegrationData(system_prompts={"Glossary": content})
