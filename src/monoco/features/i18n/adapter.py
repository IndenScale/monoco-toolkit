from pathlib import Path
from typing import Dict
from monoco.core.loader import FeatureModule, FeatureMetadata
from monoco.core.feature import IntegrationData
from monoco.features.i18n import core


class I18nFeature(FeatureModule):
    """Internationalization feature module with unified lifecycle support."""

    @property
    def metadata(self) -> FeatureMetadata:
        return FeatureMetadata(
            name="i18n",
            version="1.0.0",
            description="Documentation internationalization support",
            dependencies=["core"],
            priority=50,
            lazy=True,  # Can be lazy loaded - not critical for startup
        )

    def _on_mount(self, context: "FeatureContext") -> None:  # type: ignore
        """Initialize i18n feature with project context."""
        root = context.root
        core.init(root)

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

        return IntegrationData(system_prompts={"Documentation I18n": content})
