"""
Skill Manager for Monoco Toolkit.

This module provides centralized management and distribution of Agent Skills
following the agentskills.io standard.

Key Responsibilities:
1. Discover skills from the source directory (Toolkit/skills/)
2. Validate skill structure and metadata (YAML frontmatter)
3. Distribute skills to target agent framework directories
4. Support i18n for skill content
"""

import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError
from rich.console import Console
import yaml

console = Console()


class SkillMetadata(BaseModel):
    """
    Skill metadata from YAML frontmatter.
    Based on agentskills.io standard.
    """

    name: str = Field(..., description="Unique skill identifier (lowercase, hyphens)")
    description: str = Field(
        ..., description="Clear description of what the skill does and when to use it"
    )
    version: Optional[str] = Field(default=None, description="Skill version")
    author: Optional[str] = Field(default=None, description="Skill author")
    tags: Optional[List[str]] = Field(
        default=None, description="Skill tags for categorization"
    )


class Skill:
    """
    Represents a single skill with its metadata and file paths.
    """

    def __init__(self, root_dir: Path, skill_dir: Path):
        """
        Initialize a Skill instance.

        Args:
            root_dir: Project root directory
            skill_dir: Path to the skill directory (e.g., Toolkit/skills/issues-management)
        """
        self.root_dir = root_dir
        self.skill_dir = skill_dir
        self.name = skill_dir.name
        self.skill_file = skill_dir / "SKILL.md"
        self.metadata: Optional[SkillMetadata] = None
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load and validate skill metadata from SKILL.md frontmatter."""
        # Try to load from language subdirectories first (Feature resources pattern)
        # Then fallback to root SKILL.md (legacy pattern)
        skill_file_to_use = None

        # Check language subdirectories
        if self.skill_dir.exists():
            for item in sorted(self.skill_dir.iterdir()):
                if item.is_dir() and len(item.name) == 2:  # 2-letter lang code
                    candidate = item / "SKILL.md"
                    if candidate.exists():
                        skill_file_to_use = candidate
                        break

        # Fallback to root SKILL.md
        if not skill_file_to_use and self.skill_file.exists():
            skill_file_to_use = self.skill_file

        if not skill_file_to_use:
            return

        try:
            content = skill_file_to_use.read_text(encoding="utf-8")
            # Extract YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    metadata_dict = yaml.safe_load(frontmatter)

                    # Validate against schema
                    self.metadata = SkillMetadata(**metadata_dict)
        except ValidationError as e:
            console.print(f"[red]Invalid metadata in {skill_file_to_use}: {e}[/red]")
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to parse metadata from {skill_file_to_use}: {e}[/yellow]"
            )

    def is_valid(self) -> bool:
        """Check if the skill has valid metadata."""
        return self.metadata is not None

    def get_languages(self) -> List[str]:
        """
        Detect available language versions of this skill.

        Returns:
            List of language codes (e.g., ['en', 'zh'])
        """
        languages = []

        # Check for language subdirectories (Feature resources pattern)
        # resources/en/SKILL.md, resources/zh/SKILL.md
        for item in self.skill_dir.iterdir():
            if item.is_dir() and len(item.name) == 2:  # Assume 2-letter lang codes
                lang_skill_file = item / "SKILL.md"
                if lang_skill_file.exists():
                    languages.append(item.name)

        # Fallback: check for root SKILL.md (legacy Toolkit/skills pattern)
        # We don't assume a default language, just return what we found
        if not languages and self.skill_file.exists():
            # For legacy pattern, we can't determine the language from structure
            # Return empty to indicate this skill uses legacy pattern
            pass

        return languages

    def get_checksum(self, lang: str) -> str:
        """
        Calculate checksum for the skill content.

        Args:
            lang: Language code

        Returns:
            SHA256 checksum of the skill file
        """
        # Try language subdirectory first (Feature resources pattern)
        target_file = self.skill_dir / lang / "SKILL.md"

        # Fallback to root SKILL.md (legacy pattern)
        if not target_file.exists():
            target_file = self.skill_file

        if not target_file.exists():
            return ""

        content = target_file.read_bytes()
        return hashlib.sha256(content).hexdigest()


class SkillManager:
    """
    Central manager for Monoco skills.

    Responsibilities:
    - Collect skills from Feature resources
    - Validate skill structure
    - Distribute skills to agent framework directories
    """

    def __init__(self, root: Path, features: Optional[List] = None):
        """
        Initialize SkillManager.

        Args:
            root: Project root directory
            features: List of MonocoFeature instances (if None, will load from registry)
        """
        self.root = root
        self.features = features or []
        self.skills: Dict[str, Skill] = {}

        if self.features:
            self._discover_skills_from_features()

        # Also discover core skill (monoco/core/resources/)
        self._discover_core_skill()

    def _discover_core_skill(self) -> None:
        """
        Discover skill from monoco/core/resources/.

        Core is special - it's not a Feature but still has a skill.
        """
        core_resources_dir = self.root / "monoco" / "core" / "resources"

        if not core_resources_dir.exists():
            return

        # Check for SKILL.md in language directories
        for lang_dir in core_resources_dir.iterdir():
            if lang_dir.is_dir() and (lang_dir / "SKILL.md").exists():
                skill = Skill(self.root, core_resources_dir)

                # Use the skill's metadata name if available
                if skill.metadata and skill.metadata.name:
                    skill.name = skill.metadata.name.replace("-", "_")
                else:
                    skill.name = "monoco_core"

                if skill.is_valid():
                    self.skills[skill.name] = skill
                break  # Only need to detect once

    def _discover_skills_from_features(self) -> None:
        """
        Discover skills from Feature resources.

        Each feature should have:
        - monoco/features/{feature}/resources/{lang}/SKILL.md
        """
        from monoco.core.feature import MonocoFeature

        for feature in self.features:
            if not isinstance(feature, MonocoFeature):
                continue

            # Determine feature module path
            # feature.__class__.__module__ is like 'monoco.features.issue.adapter'
            module_parts = feature.__class__.__module__.split(".")
            if (
                len(module_parts) >= 3
                and module_parts[0] == "monoco"
                and module_parts[1] == "features"
            ):
                feature_name = module_parts[2]

                # Construct path to feature resources
                # monoco/features/{feature}/resources/
                feature_dir = self.root / "monoco" / "features" / feature_name
                resources_dir = feature_dir / "resources"

                if not resources_dir.exists():
                    continue

                # Check for SKILL.md in language directories
                for lang_dir in resources_dir.iterdir():
                    if lang_dir.is_dir() and (lang_dir / "SKILL.md").exists():
                        # Create a Skill instance
                        # We need to adapt the Skill class to work with feature resources
                        skill = self._create_skill_from_feature(
                            feature_name, resources_dir
                        )
                        if skill and skill.is_valid():
                            # Use feature name as skill identifier
                            skill_key = f"{feature_name}"
                            if skill_key not in self.skills:
                                self.skills[skill_key] = skill
                        break  # Only need to detect once per feature

    def _create_skill_from_feature(
        self, feature_name: str, resources_dir: Path
    ) -> Optional[Skill]:
        """
        Create a Skill instance from a feature's resources directory.

        Args:
            feature_name: Name of the feature (e.g., 'issue', 'spike')
            resources_dir: Path to the feature's resources directory

        Returns:
            Skill instance or None if creation fails
        """
        # Use the resources directory as the skill directory
        # The Skill class expects a directory with SKILL.md or {lang}/SKILL.md
        skill = Skill(self.root, resources_dir)

        # Use the skill's metadata name if available (e.g., 'monoco-issue')
        # Convert to snake_case for directory name (e.g., 'monoco_issue')
        if skill.metadata and skill.metadata.name:
            # Convert kebab-case to snake_case for directory name
            skill.name = skill.metadata.name.replace("-", "_")
        else:
            # Fallback to feature name
            skill.name = f"monoco_{feature_name}"

        return skill

    def list_skills(self) -> List[Skill]:
        """
        Get all available skills.

        Returns:
            List of Skill instances
        """
        return list(self.skills.values())

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a specific skill by name.

        Args:
            name: Skill name

        Returns:
            Skill instance or None if not found
        """
        return self.skills.get(name)

    def distribute(
        self, target_dir: Path, lang: str, force: bool = False
    ) -> Dict[str, bool]:
        """
        Distribute skills to a target directory.

        Args:
            target_dir: Target directory for skill distribution (e.g., .cursor/skills/)
            lang: Language code to distribute (e.g., 'en', 'zh')
            force: Force overwrite even if checksum matches

        Returns:
            Dictionary mapping skill names to success status
        """
        results = {}

        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        for skill_name, skill in self.skills.items():
            try:
                # Check if this skill has the requested language
                available_languages = skill.get_languages()

                if lang not in available_languages:
                    console.print(
                        f"[yellow]Skill {skill_name} does not have {lang} version, skipping[/yellow]"
                    )
                    results[skill_name] = False
                    continue

                # Distribute the specific language version
                self._distribute_skill_language(skill, target_dir, lang, force)
                results[skill_name] = True

            except Exception as e:
                console.print(
                    f"[red]Failed to distribute skill {skill_name}: {e}[/red]"
                )
                results[skill_name] = False

        return results

    def _distribute_skill_language(
        self, skill: Skill, target_dir: Path, lang: str, force: bool
    ) -> None:
        """
        Distribute a specific language version of a skill.

        Args:
            skill: Skill instance
            target_dir: Target directory (e.g., .cursor/skills/)
            lang: Language code
            force: Force overwrite
        """
        # Determine source file (try language subdirectory first)
        source_file = skill.skill_dir / lang / "SKILL.md"

        # Fallback to root SKILL.md (legacy pattern)
        if not source_file.exists():
            source_file = skill.skill_file

        if not source_file.exists():
            console.print(
                f"[yellow]Source file not found for {skill.name}/{lang}[/yellow]"
            )
            return

        # Target path: {target_dir}/{skill_name}/SKILL.md (no language subdirectory)
        target_skill_dir = target_dir / skill.name

        # Create target directory
        target_skill_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_skill_dir / "SKILL.md"

        # Check if update is needed
        if target_file.exists() and not force:
            source_checksum = skill.get_checksum(lang)
            target_content = target_file.read_bytes()
            target_checksum = hashlib.sha256(target_content).hexdigest()

            if source_checksum == target_checksum:
                console.print(f"[dim]  = {skill.name}/SKILL.md is up to date[/dim]")
                return

        # Copy the file
        shutil.copy2(source_file, target_file)
        console.print(f"[green]  ✓ Distributed {skill.name}/SKILL.md ({lang})[/green]")

        # Copy additional resources if they exist
        self._copy_skill_resources(skill.skill_dir, target_skill_dir, lang)

    def _copy_skill_resources(
        self, source_dir: Path, target_dir: Path, lang: str
    ) -> None:
        """
        Copy additional skill resources (scripts, examples, etc.).

        Args:
            source_dir: Source skill directory
            target_dir: Target skill directory
            lang: Language code
        """
        # Define resource directories to copy
        resource_dirs = ["scripts", "examples", "resources"]

        # Try language subdirectory first (Feature resources pattern)
        source_base = source_dir / lang

        # Fallback to root directory (legacy pattern)
        if not source_base.exists():
            source_base = source_dir

        for resource_name in resource_dirs:
            source_resource = source_base / resource_name
            if source_resource.exists() and source_resource.is_dir():
                target_resource = target_dir / resource_name

                # Remove existing and copy fresh
                if target_resource.exists():
                    shutil.rmtree(target_resource)

                shutil.copytree(source_resource, target_resource)
                console.print(
                    f"[dim]    Copied {resource_name}/ for {source_dir.name}/{lang}[/dim]"
                )

    def cleanup(self, target_dir: Path) -> None:
        """
        Remove distributed skills from a target directory.

        Args:
            target_dir: Target directory to clean
        """
        if not target_dir.exists():
            console.print(f"[dim]Target directory does not exist: {target_dir}[/dim]")
            return

        removed_count = 0

        for skill_name in self.skills.keys():
            skill_target = target_dir / skill_name
            if skill_target.exists():
                shutil.rmtree(skill_target)
                console.print(f"[green]  ✓ Removed {skill_name}[/green]")
                removed_count += 1

        # Remove empty parent directory if no skills remain
        if target_dir.exists() and not any(target_dir.iterdir()):
            target_dir.rmdir()
            console.print(f"[dim]  Removed empty directory: {target_dir}[/dim]")

        if removed_count == 0:
            console.print(f"[dim]No skills to remove from {target_dir}[/dim]")
