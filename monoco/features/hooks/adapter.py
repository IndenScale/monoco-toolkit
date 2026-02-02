"""
Feature adapter for Git Hooks management.

Integrates with Monoco's feature loading system.
"""

from pathlib import Path
from typing import Dict

from monoco.core.loader import FeatureModule, FeatureMetadata
from monoco.core.feature import IntegrationData

from .core import GitHooksManager, HookConfig


class HooksFeature(FeatureModule):
    """Git Hooks management feature module."""

    @property
    def metadata(self) -> FeatureMetadata:
        return FeatureMetadata(
            name="hooks",
            version="1.0.0",
            description="Git hooks management for Monoco development workflow",
            dependencies=["core"],
            priority=5,  # Load early to be available for other features
        )

    def _on_mount(self, context: "FeatureContext") -> None:  # type: ignore
        """Initialize hooks feature with workspace context."""
        # Hooks are installed on-demand via CLI commands
        pass

    def integrate(self, root: Path, config: Dict) -> IntegrationData:
        """Provide integration data for agent environment."""
        # Read hooks-specific prompts if available
        base_dir = Path(__file__).parent / "resources"
        prompt_file = base_dir / "AGENTS.md"

        content = ""
        if prompt_file.exists():
            content = prompt_file.read_text(encoding="utf-8").strip()

        return IntegrationData(system_prompts={"Git Hooks": content})

    def create_manager(self, project_root: Path, config: Dict) -> GitHooksManager:
        """
        Create a GitHooksManager instance from configuration.

        Args:
            project_root: Project root directory
            config: Configuration dictionary (from workspace.yaml)

        Returns:
            Configured GitHooksManager instance
        """
        hooks_config = config.get("hooks", {})
        hook_config = HookConfig(
            enabled=hooks_config.get("enabled", True),
            enabled_features=hooks_config.get("features", {}),
            enabled_hooks=hooks_config.get("hooks", {
                "pre-commit": True,
                "pre-push": False,
                "post-checkout": False,
            }),
        )
        return GitHooksManager(project_root, hook_config)
