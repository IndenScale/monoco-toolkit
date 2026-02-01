from pathlib import Path
from typing import Dict
from monoco.core.loader import FeatureModule, FeatureMetadata
from monoco.core.feature import IntegrationData


class MemoFeature(FeatureModule):
    """Memo (fleeting notes) feature module with unified lifecycle support."""

    @property
    def metadata(self) -> FeatureMetadata:
        return FeatureMetadata(
            name="memo",
            version="1.0.0",
            description="Fleeting notes and quick idea capture",
            dependencies=["core"],
            priority=40,
            lazy=True,  # Can be lazy loaded
        )

    def _on_mount(self, context: "FeatureContext") -> None:  # type: ignore
        """Memo feature doesn't require explicit initialization.

        The inbox is created on first use.
        """
        pass

    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        """Provide integration data for agent environment."""
        # Determine language from config, default to 'en'
        lang = config.get("i18n", {}).get("source_lang", "en")

        # Resource path: monoco/features/memo/resources/{lang}/AGENTS.md
        base_dir = Path(__file__).parent / "resources"

        # Try specific language, fallback to 'en'
        prompt_file = base_dir / lang / "AGENTS.md"
        if not prompt_file.exists():
            prompt_file = base_dir / "en" / "AGENTS.md"

        content = ""
        if prompt_file.exists():
            content = prompt_file.read_text(encoding="utf-8").strip()

        return IntegrationData(system_prompts={"Memo (Fleeting Notes)": content})
