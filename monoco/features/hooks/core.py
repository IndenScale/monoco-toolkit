"""
Core logic for Git Hooks management.

Implements the distributed hooks + aggregator pattern:
- Each Feature stores its hooks in resources/hooks/{hook-type}.sh
- This module discovers, sorts by priority, and generates final hooks
"""

import os
import stat
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console

console = Console()


class HookType(str, Enum):
    """Supported git hook types."""

    PRE_COMMIT = "pre-commit"
    PRE_PUSH = "pre-push"
    POST_CHECKOUT = "post-checkout"
    PRE_REBASE = "pre-rebase"
    COMMIT_MSG = "commit-msg"


@dataclass
class HookDeclaration:
    """
    Metadata for a hook script contributed by a Feature.

    Attributes:
        hook_type: Type of git hook (pre-commit, pre-push, etc.)
        script_path: Path to the hook script file
        feature_name: Name of the contributing Feature
        priority: Execution priority (lower = earlier, default 100)
    """

    hook_type: HookType
    script_path: Path
    feature_name: str
    priority: int = 100


@dataclass
class HookConfig:
    """Configuration for hooks feature."""

    enabled: bool = True
    enabled_features: Dict[str, bool] = field(default_factory=dict)
    # Global hook enable/disable by type
    enabled_hooks: Dict[str, bool] = field(default_factory=lambda: {
        "pre-commit": True,
        "pre-push": False,  # Disabled by default
        "post-checkout": False,
    })


class GitHooksManager:
    """
    Manages discovery, aggregation, and installation of git hooks.

    This class implements the aggregator pattern in the distributed hooks architecture:
    1. Discovers hooks from all Features in resources/hooks/
    2. Sorts them by priority
    3. Generates combined hook scripts
    4. Installs them to .git/hooks/
    """

    # Header marker to identify Monoco-managed hooks
    MONOCO_MARKER = "# Monoco Managed Hook - Auto-generated. Do not edit manually."

    def __init__(self, project_root: Path, config: Optional[HookConfig] = None):
        """
        Initialize the hooks manager.

        Args:
            project_root: Root directory of the project (contains .git/)
            config: Optional hooks configuration
        """
        self.project_root = project_root
        self.config = config or HookConfig()
        self.git_dir = project_root / ".git"
        self.hooks_dir = self.git_dir / "hooks"

    def is_git_repo(self) -> bool:
        """Check if project root is a git repository."""
        return self.git_dir.exists() and self.git_dir.is_dir()

    def collect_hooks(
        self, features_dir: Optional[Path] = None
    ) -> Dict[HookType, List[HookDeclaration]]:
        """
        Discover all hook scripts from Features.

        Scans features/{feature}/resources/hooks/ for hook scripts.

        Args:
            features_dir: Root directory containing features (defaults to monoco/features/)

        Returns:
            Dictionary mapping hook types to sorted list of hook declarations
        """
        if features_dir is None:
            # Default to monoco/features/ relative to this file
            features_dir = Path(__file__).parent.parent

        hooks_by_type: Dict[HookType, List[HookDeclaration]] = {
            hook_type: [] for hook_type in HookType
        }

        if not features_dir.exists():
            return hooks_by_type

        for feature_dir in features_dir.iterdir():
            if not feature_dir.is_dir() or feature_dir.name.startswith("_"):
                continue

            feature_name = feature_dir.name

            # Check if this feature is enabled in config
            if self.config.enabled_features.get(feature_name, True) is False:
                continue

            hooks_dir = feature_dir / "resources" / "hooks"
            if not hooks_dir.exists():
                continue

            # Discover hook scripts
            for hook_script in hooks_dir.iterdir():
                if not hook_script.is_file():
                    continue

                # Parse hook type from filename (e.g., pre-commit.sh -> pre-commit)
                hook_type = self._parse_hook_type(hook_script.name)
                if hook_type is None:
                    continue

                # Check if this hook type is globally enabled
                if not self.config.enabled_hooks.get(hook_type.value, True):
                    continue

                # Get feature priority from adapter if available
                priority = self._get_feature_priority(features_dir, feature_name)

                declaration = HookDeclaration(
                    hook_type=hook_type,
                    script_path=hook_script,
                    feature_name=feature_name,
                    priority=priority,
                )
                hooks_by_type[hook_type].append(declaration)

        # Sort each list by priority
        for hook_type in hooks_by_type:
            hooks_by_type[hook_type].sort(key=lambda h: h.priority)

        return hooks_by_type

    def _parse_hook_type(self, filename: str) -> Optional[HookType]:
        """Parse hook type from filename (e.g., 'pre-commit.sh' -> HookType.PRE_COMMIT)."""
        # Remove extension
        name = filename
        for ext in [".sh", ".py", ".bash"]:
            if name.endswith(ext):
                name = name[: -len(ext)]
                break

        try:
            return HookType(name)
        except ValueError:
            return None

    def _get_feature_priority(self, features_dir: Path, feature_name: str) -> int:
        """Get feature priority from its adapter metadata."""
        adapter_path = features_dir / feature_name / "adapter.py"
        if not adapter_path.exists():
            return 100

        try:
            # Import the adapter module
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                f"monoco.features.{feature_name}.adapter", adapter_path
            )
            if spec is None or spec.loader is None:
                return 100

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for Feature class with metadata
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if hasattr(attr, "metadata"):
                    metadata = attr.metadata
                    if hasattr(metadata, "priority"):
                        return metadata.priority
        except Exception:
            pass

        return 100

    def generate_hook_script(self, declarations: List[HookDeclaration]) -> str:
        """
        Generate a combined hook script from multiple declarations.

        Args:
            declarations: List of hook declarations to combine

        Returns:
            Generated shell script content
        """
        lines = [
            "#!/bin/sh",
            self.MONOCO_MARKER,
            "# Generated by Monoco Toolkit",
            "",
            "# Store the original exit code",
            "OVERALL_EXIT=0",
            "",
        ]

        # Add virtual environment detection
        lines.extend([
            "# Detect virtual environment",
            'if [ -n "$VIRTUAL_ENV" ]; then',
            '    PYTHON_CMD="$VIRTUAL_ENV/bin/python"',
            'elif [ -f "./.venv/bin/python" ]; then',
            '    PYTHON_CMD="./.venv/bin/python"',
            'elif [ -f "./venv/bin/python" ]; then',
            '    PYTHON_CMD="./venv/bin/python"',
            'else',
            '    PYTHON_CMD="python3"',
            'fi',
            '',
            "# Detect monoco command",
            'MONOCO_CMD="$PYTHON_CMD -m monoco"',
            "",
        ])

        for decl in declarations:
            lines.extend([
                f"# --- Hook from {decl.feature_name} (priority: {decl.priority}) ---",
                f'echo "[Monoco] Running {decl.hook_type.value} hook: {decl.feature_name}"',
            ])

            # Read and include the hook script content
            try:
                content = decl.script_path.read_text(encoding="utf-8")
                # Remove shebang if present since we're in a combined script
                lines_content = content.splitlines()
                if lines_content and lines_content[0].startswith("#!/"):
                    lines_content = lines_content[1:]

                for line in lines_content:
                    lines.append(line)
            except Exception as e:
                lines.append(f'echo "[Monoco] Error reading hook: {e}" >&2')

            lines.extend([
                "# Capture exit code",
                "HOOK_EXIT=$?",
                'if [ $HOOK_EXIT -ne 0 ]; then',
                '    echo "[Monoco] Hook failed with exit code $HOOK_EXIT"',
                "    OVERALL_EXIT=$HOOK_EXIT",
                "fi",
                "",
            ])

        lines.extend([
            "# Exit with the first non-zero exit code",
            "exit $OVERALL_EXIT",
            "",
        ])

        return "\n".join(lines)

    def install(self, features_dir: Optional[Path] = None) -> Dict[HookType, bool]:
        """
        Install all discovered hooks to .git/hooks/.

        Args:
            features_dir: Root directory containing features

        Returns:
            Dictionary mapping hook types to success status
        """
        results = {}

        if not self.is_git_repo():
            console.print("[yellow]Warning: Not a git repository. Skipping hook installation.[/yellow]")
            return results

        self.hooks_dir.mkdir(exist_ok=True)

        # Collect all hooks
        hooks_by_type = self.collect_hooks(features_dir)

        for hook_type, declarations in hooks_by_type.items():
            if not declarations:
                continue

            # Check if hook type is enabled
            if not self.config.enabled_hooks.get(hook_type.value, True):
                continue

            hook_path = self.hooks_dir / hook_type.value

            # Check for existing non-monoco hook
            if hook_path.exists():
                try:
                    content = hook_path.read_text(encoding="utf-8")
                    if self.MONOCO_MARKER not in content:
                        console.print(
                            f"[yellow]Warning: {hook_type.value} already exists and is not managed by Monoco. Skipping.[/yellow]"
                        )
                        results[hook_type] = False
                        continue
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Cannot read existing {hook_type.value}: {e}. Skipping.[/yellow]"
                    )
                    results[hook_type] = False
                    continue

            # Generate and write hook script
            script_content = self.generate_hook_script(declarations)

            try:
                hook_path.write_text(script_content, encoding="utf-8")
                # Make executable
                hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                console.print(f"[green]✓ Installed {hook_type.value} hook ({len(declarations)} scripts)[/green]")
                results[hook_type] = True
            except Exception as e:
                console.print(f"[red]✗ Failed to install {hook_type.value}: {e}[/red]")
                results[hook_type] = False

        return results

    def uninstall(self) -> Dict[HookType, bool]:
        """
        Uninstall all Monoco-managed hooks from .git/hooks/.

        Returns:
            Dictionary mapping hook types to success status
        """
        results = {}

        if not self.is_git_repo():
            console.print("[yellow]Warning: Not a git repository.[/yellow]")
            return results

        for hook_type in HookType:
            hook_path = self.hooks_dir / hook_type.value

            if not hook_path.exists():
                continue

            try:
                content = hook_path.read_text(encoding="utf-8")
                if self.MONOCO_MARKER in content:
                    hook_path.unlink()
                    console.print(f"[green]✓ Removed {hook_type.value} hook[/green]")
                    results[hook_type] = True
                else:
                    console.print(
                        f"[dim]Skipping {hook_type.value}: not managed by Monoco[/dim]"
                    )
                    results[hook_type] = False
            except Exception as e:
                console.print(f"[red]✗ Failed to remove {hook_type.value}: {e}[/red]")
                results[hook_type] = False

        return results

    def get_status(self, features_dir: Optional[Path] = None) -> Dict[str, any]:
        """
        Get current hooks installation status.

        Args:
            features_dir: Root directory containing features

        Returns:
            Status dictionary with installed hooks and discovered scripts
        """
        status = {
            "is_git_repo": self.is_git_repo(),
            "hooks_dir": str(self.hooks_dir) if self.is_git_repo() else None,
            "installed": {},
            "discovered": {},
            "config": {
                "enabled": self.config.enabled,
                "enabled_features": self.config.enabled_features,
                "enabled_hooks": self.config.enabled_hooks,
            },
        }

        if not self.is_git_repo():
            return status

        # Check installed hooks
        for hook_type in HookType:
            hook_path = self.hooks_dir / hook_type.value
            if hook_path.exists():
                try:
                    content = hook_path.read_text(encoding="utf-8")
                    is_monoco = self.MONOCO_MARKER in content
                    status["installed"][hook_type.value] = {
                        "exists": True,
                        "managed_by_monoco": is_monoco,
                    }
                except Exception:
                    status["installed"][hook_type.value] = {
                        "exists": True,
                        "managed_by_monoco": False,
                        "error": "Cannot read file",
                    }
            else:
                status["installed"][hook_type.value] = {"exists": False}

        # Discover available hooks
        hooks_by_type = self.collect_hooks(features_dir)
        for hook_type, declarations in hooks_by_type.items():
            if declarations:
                status["discovered"][hook_type.value] = [
                    {
                        "feature": d.feature_name,
                        "path": str(d.script_path),
                        "priority": d.priority,
                    }
                    for d in declarations
                ]

        return status
