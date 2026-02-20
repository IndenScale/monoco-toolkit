"""DocExtractor feature adapter."""

from pathlib import Path
from typing import Dict

from monoco.core.loader import FeatureModule, FeatureMetadata
from monoco.core.feature import IntegrationData


class DocExtractorFeature(FeatureModule):
    """DocExtractor feature module for document extraction and rendering."""

    @property
    def metadata(self) -> FeatureMetadata:
        return FeatureMetadata(
            name="doc_extractor",
            version="1.0.0",
            description="Document extraction and rendering to WebP pages",
            dependencies=["core"],
            priority=40,
        )

    def _on_mount(self, context: "FeatureContext") -> None:  # type: ignore
        """Initialize doc-extractor feature with project context."""
        # DocExtractor is self-contained, no special initialization needed
        pass

    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        """Provide integration data for agent environment."""
        # Determine language from config, default to 'en'
        lang = config.get("i18n", {}).get("source_lang", "en")
        base_dir = Path(__file__).parent / "resources"

        # Try specific language, fallback to 'en'
        prompt_file = base_dir / lang / "AGENTS.md"
        if not prompt_file.exists():
            prompt_file = base_dir / "en" / "AGENTS.md"

        content = ""
        if prompt_file.exists():
            content = prompt_file.read_text(encoding="utf-8").strip()

        return IntegrationData(system_prompts={"Doc-Extractor": content})
