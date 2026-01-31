from pathlib import Path
from typing import Dict
from monoco.core.feature import MonocoFeature, IntegrationData
from monoco.features.glossary.core import GlossaryManager

class GlossaryFeature(MonocoFeature):
    @property
    def name(self) -> str:
        return "glossary"

    def initialize(self, root: Path, config: Dict) -> None:
        # Glossary does not require file initialization in the workspace
        pass

    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        # Determine language from config, default to 'en'
        lang = config.get("i18n", {}).get("source_lang", "en")
        
        manager = GlossaryManager()
        content = manager.get_glossary_content(lang)
        
        return IntegrationData(system_prompts={"Glossary": content})
