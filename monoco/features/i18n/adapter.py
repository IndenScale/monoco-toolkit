from pathlib import Path
from typing import Dict
from monoco.core.feature import MonocoFeature, IntegrationData
from monoco.features.i18n import core

class I18nFeature(MonocoFeature):
    @property
    def name(self) -> str:
        return "i18n"

    def initialize(self, root: Path, config: Dict) -> None:
        core.init(root)

    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        # Determine language from config, default to 'en'
        lang = config.get("i18n", {}).get("source_lang", "en")
        base_dir = Path(__file__).parent / "resources"
        
        prompt_file = base_dir / lang / "AGENTS.md"
        if not prompt_file.exists():
            prompt_file = base_dir / "en" / "AGENTS.md"
            
        content = ""
        if prompt_file.exists():
            content = prompt_file.read_text(encoding="utf-8").strip()

        return IntegrationData(
            system_prompts={"Documentation I18n": content}
        )
