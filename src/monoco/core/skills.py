"""
Skill Manager for Monoco Toolkit.

This module provides centralized management and distribution of Agent Skills
following the standardized architecture:
- Atom Skills: monoco_atom_{name} - Atomic capabilities
- Workflow Skills: monoco_workflow_{name} - Orchestration of atoms
- Role Skills: monoco_role_{name} - Configuration layer

Key Responsibilities:
1. Discover skills from features (monoco/features/{feature}/resources/)
2. Validate skill structure and metadata
3. Distribute skills to target agent framework directories
4. Support i18n for skill content

Architecture Principle:
- Core is framework-only, no skills
- All skills are defined in Features (value delivery atoms)
- All skills follow naming convention: monoco_{type}_{name}
"""

import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, ValidationError
from rich.console import Console
import yaml

# Import new skill framework
from monoco.core.skill_framework import (
    SkillLoader,
    AtomSkillMetadata,
    WorkflowSkillMetadata,
    RoleSkillMetadata,
    SkillType,
    SkillMode,
)
from monoco.core.workflow_converter import WorkflowDistributor

console = Console()


class SkillMetadata(BaseModel):
    """
    Legacy skill metadata from YAML frontmatter.
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
    type: Optional[str] = Field(
        default="standard", description="Skill type: standard, flow, workflow, atom, role"
    )
    role: Optional[str] = Field(
        default=None, description="Role identifier for Flow Skills (e.g., engineer, manager)"
    )
    domain: Optional[str] = Field(
        default=None, description="Domain identifier for Workflow Skills (e.g., issue, spike)"
    )


class Skill:
    """
    Represents a single skill with its metadata and file paths.
    
    Directory structure: resources/{lang}/skills/{name}/SKILL.md
    Example: resources/en/skills/monoco_core/SKILL.md
    """

    def __init__(
        self,
        root_dir: Path,
        skill_name: str,
        resources_dir: Path,
    ):
        self.root_dir = root_dir
        self.skill_name = skill_name
        self.resources_dir = resources_dir
        self.name = skill_name
        self.metadata: Optional[SkillMetadata] = None
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load and validate skill metadata from SKILL.md frontmatter."""
        skill_file = self._get_first_available_skill_file()
        
        if not skill_file:
            return

        try:
            content = skill_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    metadata_dict = yaml.safe_load(frontmatter)
                    self.metadata = SkillMetadata(**metadata_dict)
        except ValidationError as e:
            console.print(f"[red]Invalid metadata in {skill_file}: {e}[/red]")
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to parse metadata from {skill_file}: {e}[/yellow]"
            )

    def _get_first_available_skill_file(self) -> Optional[Path]:
        """Get the first available SKILL.md file from language subdirectories."""
        if not self.resources_dir.exists():
            return None
            
        for lang_dir in sorted(self.resources_dir.iterdir()):
            if lang_dir.is_dir() and len(lang_dir.name) == 2:
                skill_file = lang_dir / "skills" / self.skill_name / "SKILL.md"
                if skill_file.exists():
                    return skill_file
        return None

    def get_skill_file(self, lang: str) -> Optional[Path]:
        """Get the SKILL.md file path for a specific language."""
        skill_file = self.resources_dir / lang / "skills" / self.skill_name / "SKILL.md"
        if skill_file.exists():
            return skill_file
        return None

    def is_valid(self) -> bool:
        """Check if the skill has valid metadata."""
        return self.metadata is not None

    def get_type(self) -> str:
        """Get skill type, defaults to 'standard'."""
        return self.metadata.type if self.metadata and self.metadata.type else "standard"

    def get_role(self) -> Optional[str]:
        """Get skill role (for Flow Skills)."""
        return self.metadata.role if self.metadata else None

    def get_languages(self) -> List[str]:
        """Detect available language versions of this skill."""
        languages = []

        if not self.resources_dir.exists():
            return languages

        for lang_dir in self.resources_dir.iterdir():
            if lang_dir.is_dir() and len(lang_dir.name) == 2:
                lang_skill_file = lang_dir / "skills" / self.skill_name / "SKILL.md"
                if lang_skill_file.exists():
                    languages.append(lang_dir.name)

        return sorted(languages)

    def get_checksum(self, lang: str) -> str:
        """Calculate checksum for the skill content."""
        target_file = self.get_skill_file(lang)

        if not target_file:
            return ""

        content = target_file.read_bytes()
        return hashlib.sha256(content).hexdigest()


class SkillManager:
    """
    Central manager for Monoco skills.
    
    Architecture:
    - Atom Skills: resources/{lang}/skills/monoco_atom_*/SKILL.md or resources/atoms/*.yaml
    - Workflow Skills: resources/{lang}/skills/monoco_workflow_*/SKILL.md or resources/workflows/*.yaml
    - Role Skills: resources/{lang}/roles/monoco_role_*.yaml
    
    All skills follow the naming convention: monoco_{type}_{name}
    """

    # Prefix for standardized skill naming
    ATOM_PREFIX = "monoco_atom_"
    WORKFLOW_PREFIX = "monoco_workflow_"
    ROLE_PREFIX = "monoco_role_"

    def __init__(
        self,
        root: Path,
        features: Optional[List] = None,
    ):
        self.root = root
        self.features = features or []
        
        # Skills discovered from resources/{lang}/skills/monoco_*/SKILL.md
        self.skills: Dict[str, Skill] = {}
        
        # Three-level architecture skills
        self._skill_loaders: Dict[str, SkillLoader] = {}
        self._atoms: Dict[str, AtomSkillMetadata] = {}
        self._workflows: Dict[str, WorkflowSkillMetadata] = {}
        self._roles: Dict[str, RoleSkillMetadata] = {}

        # Discover skills from features only (core is framework-only, no skills)
        if self.features:
            self._discover_skills_from_features()
            self._discover_three_level_skills()


    def _discover_skills_from_features(self) -> None:
        """Discover skills from Feature resources."""
        from monoco.core.feature import MonocoFeature

        for feature in self.features:
            if not isinstance(feature, MonocoFeature):
                continue

            module_parts = feature.__class__.__module__.split(".")
            if (
                len(module_parts) >= 3
                and module_parts[0] == "monoco"
                and module_parts[1] == "features"
            ):
                feature_name = module_parts[2]

                feature_dir = self.root / "monoco" / "features" / feature_name
                resources_dir = feature_dir / "resources"

                if not resources_dir.exists():
                    continue

                self._discover_skills_in_resources(resources_dir, feature_name)

    def _discover_skills_in_resources(self, resources_dir: Path, feature_name: str) -> None:
        """Discover skills from resources/{lang}/skills/ directories."""
        if not resources_dir.exists():
            return

        skill_folders: Set[Path] = set()

        for lang_dir in resources_dir.iterdir():
            if not lang_dir.is_dir() or len(lang_dir.name) != 2:
                continue

            skills_dir = lang_dir / "skills"
            if not skills_dir.exists():
                continue

            for skill_subdir in skills_dir.iterdir():
                if skill_subdir.is_dir() and (skill_subdir / "SKILL.md").exists():
                    # print(f"DEBUG: Found skill folder {skill_subdir.name} in feature {feature_name}")
                    skill_folders.add(skill_subdir)

        for skill_dir in skill_folders:
            skill_name = skill_dir.name
            skill = Skill(
                root_dir=self.root,
                skill_name=skill_name,
                resources_dir=resources_dir,
            )

            if not skill.is_valid():
                console.print(
                    f"[yellow]Warning: Skill {skill_name} has invalid metadata, skipping[/yellow]"
                )
                continue

            # Naming Logic: All skills must follow monoco_{type}_{name} convention
            # The skill_key is the folder name (which should match the metadata name)
            if skill_name.startswith("monoco_"):
                skill_key = skill_name
            else:
                # Non-compliant skills are skipped (should not happen after standardization)
                console.print(
                    f"[yellow]Warning: Skill {skill_name} does not follow monoco_{{type}}_{{name}} naming, skipping[/yellow]"
                )
                continue

            skill.name = skill_key
            self.skills[skill_key] = skill

    def _discover_three_level_skills(self) -> None:
        """Discover skills from the new three-level architecture in resources/{atoms,workflows,roles}/."""
        from monoco.core.feature import MonocoFeature
        
        for feature in self.features:
            if not isinstance(feature, MonocoFeature):
                continue
                
            module_parts = feature.__class__.__module__.split(".")
            if (
                len(module_parts) >= 3
                and module_parts[0] == "monoco"
                and module_parts[1] == "features"
            ):
                feature_name = module_parts[2]
                resources_dir = self.root / "monoco" / "features" / feature_name / "resources"
                
                if not resources_dir.exists():
                    continue
                
                # Discover atoms from resources/atoms/*.yaml
                atoms_dir = resources_dir / "atoms"
                if atoms_dir.exists():
                    for atom_file in atoms_dir.glob("*.yaml"):
                        try:
                            data = yaml.safe_load(atom_file.read_text())
                            atom = AtomSkillMetadata(**data)
                            
                            # Ensure name follows monoco_atom_ prefix
                            atom_key = atom.name
                            if not atom_key.startswith(self.ATOM_PREFIX):
                                atom_key = f"{self.ATOM_PREFIX}{atom_key}"
                            
                            self._atoms[atom_key] = atom
                        except Exception as e:
                            console.print(f"[red]Failed to load atom skill {atom_file}: {e}[/red]")
                
                # Discover workflows from resources/workflows/*.yaml
                workflows_dir = resources_dir / "workflows"
                if workflows_dir.exists():
                    for workflow_file in workflows_dir.glob("*.yaml"):
                        try:
                            data = yaml.safe_load(workflow_file.read_text())
                            workflow = WorkflowSkillMetadata(**data)
                            
                            # Ensure name follows monoco_workflow_ prefix
                            workflow_key = workflow.name
                            if not workflow_key.startswith(self.WORKFLOW_PREFIX):
                                workflow_key = f"{self.WORKFLOW_PREFIX}{workflow_key}"
                            
                            self._workflows[workflow_key] = workflow
                        except Exception as e:
                            console.print(f"[red]Failed to load workflow skill {workflow_file}: {e}[/red]")
                
                # Discover roles from resources/{lang}/roles/*.yaml
                for lang_dir in resources_dir.iterdir():
                    if not lang_dir.is_dir() or len(lang_dir.name) != 2:
                        continue
                    
                    roles_dir = lang_dir / "roles"
                    if not roles_dir.exists():
                        continue
                    
                    for role_file in roles_dir.glob("*.yaml"):
                        try:
                            data = yaml.safe_load(role_file.read_text())
                            role = RoleSkillMetadata(**data)
                            
                            # Ensure name follows monoco_role_ prefix
                            role_key = role.name
                            if not role_key.startswith(self.ROLE_PREFIX):
                                role_key = f"{self.ROLE_PREFIX}{role_key}"
                            
                            self._roles[role_key] = role
                        except Exception as e:
                            console.print(f"[red]Failed to load role skill {role_file}: {e}[/red]")

    # ========================================================================
    # Legacy Skill API (backward compatible)
    # ========================================================================

    def list_skills(self) -> List[Skill]:
        """Get all available legacy skills."""
        return list(self.skills.values())

    def list_skills_by_type(self, skill_type: str) -> List[Skill]:
        """Get skills filtered by type."""
        return [s for s in self.skills.values() if s.get_type() == skill_type]

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a specific legacy skill by name."""
        return self.skills.get(name)

    def get_flow_skills(self) -> List[Skill]:
        """Get all Flow Skills."""
        return self.list_skills_by_type("flow")

    # ========================================================================
    # Three-Level Architecture API
    # ========================================================================

    def get_atom(self, name: Optional[str]) -> Optional[AtomSkillMetadata]:
        """Get an atom skill by name."""
        if not name:
            return None
        # Handle both prefixed and unprefixed names
        if not name.startswith(self.ATOM_PREFIX):
            name = f"{self.ATOM_PREFIX}{name}"
        return self._atoms.get(name)

    def get_workflow(self, name: str) -> Optional[WorkflowSkillMetadata]:
        """Get a workflow skill by name."""
        if not name.startswith(self.WORKFLOW_PREFIX):
            name = f"{self.WORKFLOW_PREFIX}{name}"
        return self._workflows.get(name)

    def get_role(self, name: str) -> Optional[RoleSkillMetadata]:
        """Get a role skill by name."""
        if not name.startswith(self.ROLE_PREFIX):
            name = f"{self.ROLE_PREFIX}{name}"
        return self._roles.get(name)

    def list_atoms(self) -> List[AtomSkillMetadata]:
        """List all atom skills."""
        return list(self._atoms.values())

    def list_workflows(self) -> List[WorkflowSkillMetadata]:
        """List all workflow skills."""
        return list(self._workflows.values())

    def list_roles(self) -> List[RoleSkillMetadata]:
        """List all role skills."""
        return list(self._roles.values())

    def resolve_role_workflow(self, role_name: str) -> Optional[WorkflowSkillMetadata]:
        """Resolve a role to its workflow."""
        role = self.get_role(role_name)
        if role:
            return self.get_workflow(role.workflow)
        return None

    def validate_workflow(self, workflow_name: str) -> List[str]:
        """Validate a workflow's dependencies are satisfied."""
        errors = []
        workflow = self.get_workflow(workflow_name)
        if not workflow:
            return [f"Workflow '{workflow_name}' not found"]

        for dep in workflow.dependencies:
            if not self.get_atom(dep):
                errors.append(f"Missing atom skill dependency: {dep}")

        for stage in workflow.stages:
            # Skip virtual stages (decision points without atom skills)
            if not stage.atom_skill:
                continue
                
            atom = self.get_atom(stage.atom_skill)
            if not atom:
                errors.append(f"Stage '{stage.name}' uses unknown atom skill: {stage.atom_skill}")
                continue
                
            if stage.operation:
                op_names = [op.name for op in atom.operations]
                if stage.operation not in op_names:
                    errors.append(
                        f"Stage '{stage.name}' uses unknown operation '{stage.operation}' "
                        f"in atom skill '{stage.atom_skill}'"
                    )

        return errors

    # ========================================================================
    # Distribution
    # ========================================================================

    def distribute(
        self, target_dir: Path, lang: str, force: bool = False
    ) -> Dict[str, bool]:
        """
        Distribute all skills to a target directory.
        
        This includes:
        - Legacy skills (SKILL.md files)
        - Three-level skills (generated SKILL.md from YAML)
        """
        results = {}

        target_dir.mkdir(parents=True, exist_ok=True)

        # Distribute legacy skills
        for skill_name, skill in self.skills.items():
            try:
                success = self._distribute_legacy_skill(skill, target_dir, lang, force)
                results[skill_name] = success
            except Exception as e:
                console.print(
                    f"[red]Failed to distribute skill {skill_name}: {e}[/red]"
                )
                results[skill_name] = False

        # Distribute three-level skills (generate SKILL.md from YAML)
        for role_name, role in self._roles.items():
            try:
                success = self._distribute_role_skill(role, target_dir, lang, force)
                results[role_name] = success
            except Exception as e:
                console.print(
                    f"[red]Failed to distribute role skill {role_name}: {e}[/red]"
                )
                results[role_name] = False

        return results

    def _distribute_legacy_skill(
        self, skill: Skill, target_dir: Path, lang: str, force: bool
    ) -> bool:
        """Distribute a legacy skill to target directory."""
        available_languages = skill.get_languages()
        
        if lang not in available_languages:
            if 'en' in available_languages:
                console.print(
                    f"[yellow]Skill {skill.name} does not have {lang} version, falling back to 'en'[/yellow]"
                )
                lang = 'en'
            else:
                console.print(
                    f"[red]Skill {skill.name} does not have {lang} or 'en' version, skipping[/red]"
                )
                return False

        source_file = skill.get_skill_file(lang)
        if not source_file:
            console.print(
                f"[red]Source file not found for {skill.name}/{lang}[/red]"
            )
            return False

        target_skill_dir = target_dir / skill.name
        target_skill_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_skill_dir / "SKILL.md"

        if target_file.exists() and not force:
            source_checksum = skill.get_checksum(lang)
            target_content = target_file.read_bytes()
            target_checksum = hashlib.sha256(target_content).hexdigest()

            if source_checksum == target_checksum:
                console.print(f"[dim]  = {skill.name}/SKILL.md is up to date[/dim]")
                return True

        shutil.copy2(source_file, target_file)
        console.print(f"[green]  ✓ Distributed {skill.name}/SKILL.md ({lang})[/green]")

        self._copy_skill_resources(skill.resources_dir, skill.skill_name, target_skill_dir, lang)

        return True

    def _distribute_role_skill(
        self, role: RoleSkillMetadata, target_dir: Path, lang: str, force: bool
    ) -> bool:
        """
        Generate and distribute a role skill as SKILL.md.
        
        This generates a comprehensive SKILL.md that includes:
        - Role configuration
        - Workflow stages
        - Atom operations
        """
        target_skill_dir = target_dir / role.name
        target_file = target_skill_dir / "SKILL.md"

        # Check if update is needed
        if target_file.exists() and not force:
            # Simple check: compare role version
            try:
                existing_content = target_file.read_text()
                if f"version: {role.version}" in existing_content:
                    console.print(f"[dim]  = {role.name}/SKILL.md is up to date[/dim]")
                    return True
            except:
                pass

        # Generate SKILL.md content
        content = self._generate_role_skill_content(role, lang)
        
        target_skill_dir.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content, encoding="utf-8")
        
        console.print(f"[green]  ✓ Generated {role.name}/SKILL.md ({lang})[/green]")
        return True

    def _generate_role_skill_content(self, role: RoleSkillMetadata, lang: str) -> str:
        """Generate SKILL.md content from role metadata."""
        workflow = self.get_workflow(role.workflow)
        
        lines = [
            "---",
            f"name: {role.name}",
            f"description: {role.description}",
            f"type: role",
            f"version: {role.version}",
        ]
        if role.author:
            lines.append(f"author: {role.author}")
        lines.append("---")
        lines.append("")
        
        # Title
        role_title = role.name.replace("role-", "").replace("-", " ").title()
        lines.append(f"# {role_title} Role")
        lines.append("")
        lines.append(role.description)
        lines.append("")
        
        # System prompt
        if role.system_prompt:
            lines.append(role.system_prompt)
            lines.append("")
        
        # Workflow section
        if workflow:
            lines.append(f"## Workflow: {workflow.name}")
            lines.append("")
            lines.append(workflow.description)
            lines.append("")
            
            # Mode configuration
            lines.append("### Execution Mode")
            lines.append("")
            lines.append(f"**Default Mode**: {role.default_mode.value}")
            lines.append("")
            
            if workflow.mode_config:
                for mode, config in workflow.mode_config.items():
                    lines.append(f"#### {mode.value.title()} Mode")
                    lines.append("")
                    lines.append(config.behavior)
                    lines.append("")
                    if config.pause_on:
                        lines.append("**Pause Points**:")
                        for pause in config.pause_on:
                            lines.append(f"- {pause}")
                        lines.append("")
            
            # Stages
            lines.append("### Workflow Stages")
            lines.append("")
            
            for i, stage in enumerate(workflow.stages, 1):
                lines.append(f"#### {i}. {stage.name.title()}")
                lines.append("")
                if stage.description:
                    lines.append(stage.description)
                    lines.append("")
                
                # Atom operation details (skip for virtual stages)
                if stage.atom_skill and stage.operation:
                    atom = self.get_atom(stage.atom_skill)
                    if atom:
                        operation = next(
                            (op for op in atom.operations if op.name == stage.operation),
                            None
                        )
                        if operation:
                            lines.append(f"**Operation**: `{atom.name}.{operation.name}`")
                            lines.append("")
                            lines.append(f"{operation.description}")
                            lines.append("")
                            
                            if operation.reminder:
                                lines.append(f"> 💡 **Reminder**: {operation.reminder}")
                                lines.append("")
                            
                            if operation.checkpoints:
                                lines.append("**Checkpoints**:")
                                for checkpoint in operation.checkpoints:
                                    lines.append(f"- [ ] {checkpoint}")
                                lines.append("")
                
                if stage.reminder:
                    lines.append(f"> ⚠️ **Stage Reminder**: {stage.reminder}")
                    lines.append("")
        
        # Preferences
        if role.preferences:
            lines.append("## Mindset & Preferences")
            lines.append("")
            for pref in role.preferences:
                lines.append(f"- {pref}")
            lines.append("")
        
        return "\n".join(lines)

    def _copy_skill_resources(
        self, resources_dir: Path, skill_name: str, target_dir: Path, lang: str
    ) -> None:
        """Copy additional skill resources."""
        resource_dirs = ["scripts", "examples", "resources"]
        source_base = resources_dir / lang / "skills" / skill_name

        if not source_base.exists():
            return

        for resource_name in resource_dirs:
            source_resource = source_base / resource_name
            if source_resource.exists() and source_resource.is_dir():
                target_resource = target_dir / resource_name

                if target_resource.exists():
                    shutil.rmtree(target_resource)

                shutil.copytree(source_resource, target_resource)
                console.print(
                    f"[dim]    Copied {resource_name}/ for {skill_name}/{lang}[/dim]"
                )

    def cleanup(self, target_dir: Path) -> None:
        """Remove distributed skills from a target directory."""
        if not target_dir.exists():
            console.print(f"[dim]Target directory does not exist: {target_dir}[/dim]")
            return

        removed_count = 0

        # Remove legacy skills
        for skill_name in self.skills.keys():
            skill_target = target_dir / skill_name
            if skill_target.exists():
                shutil.rmtree(skill_target)
                console.print(f"[green]  ✓ Removed {skill_name}[/green]")
                removed_count += 1

        # Remove three-level skills
        for role_name in self._roles.keys():
            skill_target = target_dir / role_name
            if skill_target.exists():
                shutil.rmtree(skill_target)
                console.print(f"[green]  ✓ Removed {role_name}[/green]")
                removed_count += 1

        if target_dir.exists() and not any(target_dir.iterdir()):
            target_dir.rmdir()
            console.print(f"[dim]  Removed empty directory: {target_dir}[/dim]")

        if removed_count == 0:
            console.print(f"[dim]No skills to remove from {target_dir}[/dim]")

    def get_flow_skill_commands(self) -> List[str]:
        """Get list of available flow skill commands."""
        commands = []
        
        # Workflow/Flow skills with role attribute from legacy skills
        for skill in self.skills.values():
            if skill.get_type() in ["flow", "workflow"]:
                role = skill.get_role()
                if role:
                    commands.append(f"/flow:{role}")
        
        # Role skills from three-level architecture
        for role_name in self._roles.keys():
            short_name = role_name.replace(self.ROLE_PREFIX, "")
            commands.append(f"/flow:{short_name}")
                        
        return sorted(set(commands))

    # ========================================================================
    # Workflow Distribution (for Antigravity IDE compatibility)
    # ========================================================================

    def distribute_workflows(self, force: bool = False, lang: str = "zh") -> Dict[str, bool]:
        """
        Convert and distribute Flow Skills as Antigravity Workflows.
        
        Flow Skills are converted to Antigravity Workflow format and saved
        to .agent/workflows/ directory for IDE compatibility.
        
        Args:
            force: Overwrite existing files even if unchanged
            lang: Language code for Flow Skills (default: "zh")
            
        Returns:
            Dictionary mapping workflow filenames to success status
        """
        distributor = WorkflowDistributor(self.root)
        return distributor.distribute(force=force, lang=lang)

    def cleanup_workflows(self, lang: str = "zh") -> int:
        """
        Remove distributed Antigravity Workflows.
        
        Args:
            lang: Language code for Flow Skills (default: "zh")
            
        Returns:
            Number of workflow files removed
        """
        distributor = WorkflowDistributor(self.root)
        return distributor.cleanup(lang=lang)
