from pathlib import Path
from typing import Dict
from monoco.core.feature import MonocoFeature, IntegrationData
from monoco.features.issue import core


class IssueFeature(MonocoFeature):
    @property
    def name(self) -> str:
        return "issue"

    def initialize(self, root: Path, config: Dict) -> None:
        issues_path = root / config.get("paths", {}).get("issues", "Issues")
        core.init(issues_path)

    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        # Determine language from config, default to 'en'
        lang = config.get("i18n", {}).get("source_lang", "en")

        # Current file is in monoco/features/issue/adapter.py
        # Resource path: monoco/features/issue/resources/{lang}/AGENTS.md
        base_dir = Path(__file__).parent / "resources"

        # Try specific language, fallback to 'en'
        prompt_file = base_dir / lang / "AGENTS.md"
        if not prompt_file.exists():
            prompt_file = base_dir / "en" / "AGENTS.md"

        content = ""
        if prompt_file.exists():
            content = prompt_file.read_text(encoding="utf-8").strip()

        return IntegrationData(system_prompts={"Issue Management": content})
