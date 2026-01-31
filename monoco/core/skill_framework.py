"""
Skill Framework for Monoco Toolkit - Three-Level Architecture

This module implements the Role-Workflow-Atom three-level skill architecture:

1. Atom Skills (atom): Atomic capabilities that perform single operations
   - atom-issue-lifecycle: Issue lifecycle operations (create, start, submit, close)
   - atom-code-dev: Code development operations (investigate, implement, test, document)
   - atom-knowledge: Knowledge management operations (capture, process, convert, archive)
   - atom-review: Review operations (checkout, verify, challenge, feedback)

2. Workflow Skills (workflow): Orchestration of atom skills into workflows
   - workflow-dev: Development workflow (setup → investigate → implement → test → submit)
   - workflow-issue-create: Issue creation workflow (extract → classify → create)
   - workflow-review: Review workflow (checkout → verify → challenge → decide)

3. Role Skills (role): Configuration layer defining default workflow and preferences
   - role-engineer: Engineer role (uses workflow-dev, autopilot mode)
   - role-manager: Manager role (uses workflow-planning, copilot mode)
   - role-planner: Planner role (uses workflow-design, copilot mode)
   - role-reviewer: Reviewer role (uses workflow-review, autopilot mode)

Key Design Principles:
- Single Responsibility: Each atom skill does one thing
- Composition over Inheritance: Workflows compose atoms
- Mode Agnostic: Same workflow supports both copilot and autopilot modes
- Convention over Configuration: System constraints defined once in atom layer
"""

from __future__ import annotations
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, model_validator
import yaml


class SkillMode(str, Enum):
    """Execution mode for skills."""
    COPILOT = "copilot"      # Human-led, AI-assisted
    AUTOPILOT = "autopilot"  # AI-led, automatic execution


class SkillType(str, Enum):
    """Skill type in the three-level architecture."""
    ATOM = "atom"        # Atomic capability
    WORKFLOW = "workflow"  # Workflow orchestration
    ROLE = "role"        # Role configuration


class ComplianceRule(BaseModel):
    """A compliance rule."""
    rule: str = Field(..., description="Rule description")
    severity: str = Field(default="warning", description="Rule severity: error, warning, info")
    check: Optional[str] = Field(default=None, description="Check command or condition")
    command: Optional[str] = Field(default=None, description="Associated CLI command")
    mindset: Optional[str] = Field(default=None, description="Related mindset/principle")
    fail_if: Optional[str] = Field(default=None, description="Condition that causes failure")


class AtomOperation(BaseModel):
    """An operation within an atom skill."""
    name: str = Field(..., description="Operation name (e.g., 'create', 'start')")
    description: str = Field(..., description="What this operation does")
    command: Optional[str] = Field(default=None, description="Associated CLI command")
    reminder: Optional[str] = Field(default=None, description="Reminder text for this operation")
    compliance_rules: List[ComplianceRule] = Field(default_factory=list, description="Compliance rules for this operation")
    checkpoints: List[str] = Field(default_factory=list, description="Checkpoints for this operation")
    output: Optional[str] = Field(default=None, description="Expected output")


class Checkpoint(BaseModel):
    """A checkpoint in a workflow stage."""
    description: str = Field(..., description="What to check")
    atom_skill: str = Field(..., description="Atom skill to use")
    operation: str = Field(..., description="Operation to invoke")
    reminder: Optional[str] = Field(default=None, description="Reminder at this checkpoint")


class WorkflowStage(BaseModel):
    """A stage in a workflow."""
    name: str = Field(..., description="Stage name")
    atom_skill: Optional[str] = Field(default=None, description="Atom skill to use (optional for virtual stages)")
    operation: Optional[str] = Field(default=None, description="Operation to invoke (optional for virtual stages)")
    description: Optional[str] = Field(default=None, description="Stage description")
    reminder: Optional[str] = Field(default=None, description="Reminder for this stage")
    checkpoints: List[Checkpoint] = Field(default_factory=list, description="Checkpoints within this stage")
    next_stages: Dict[str, str] = Field(default_factory=dict, description="Conditional next stages")


class ModeConfig(BaseModel):
    """Configuration for a specific execution mode."""
    behavior: str = Field(..., description="Behavior description")
    pause_on: List[str] = Field(default_factory=list, description="Stages to pause on")
    auto_execute: bool = Field(default=False, description="Whether to auto-execute stages")


# ============================================================================
# Atom Skill Models
# ============================================================================

class AtomSkillMetadata(BaseModel):
    """Metadata for an atom skill."""
    name: str = Field(..., description="Unique atom skill name (e.g., 'atom-issue-lifecycle')")
    type: str = Field(default="atom", description="Skill type (always 'atom')")
    domain: str = Field(..., description="Domain (e.g., 'issue', 'code', 'knowledge', 'review')")
    description: str = Field(..., description="What this atom skill provides")
    version: str = Field(default="1.0.0", description="Skill version")
    author: Optional[str] = Field(default=None, description="Skill author")
    
    operations: List[AtomOperation] = Field(..., description="Available operations")
    compliance_rules: List[ComplianceRule] = Field(default_factory=list, description="System-level compliance rules")


# ============================================================================
# Workflow Skill Models
# ============================================================================

class WorkflowSkillMetadata(BaseModel):
    """Metadata for a workflow skill."""
    name: str = Field(..., description="Unique workflow skill name (e.g., 'workflow-dev')")
    type: str = Field(default="workflow", description="Skill type (always 'workflow')")
    description: str = Field(..., description="What this workflow orchestrates")
    version: str = Field(default="1.0.0", description="Skill version")
    author: Optional[str] = Field(default=None, description="Skill author")
    
    dependencies: List[str] = Field(..., description="Required atom skills")
    stages: List[WorkflowStage] = Field(..., description="Workflow stages")
    
    mode_config: Dict[SkillMode, ModeConfig] = Field(
        default_factory=dict,
        description="Configuration for copilot and autopilot modes"
    )


# ============================================================================
# Role Skill Models
# ============================================================================

class RolePreference(BaseModel):
    """A preference for a role."""
    category: str = Field(..., description="Preference category")
    value: str = Field(..., description="Preference value")


class RoleSkillMetadata(BaseModel):
    """Metadata for a role skill."""
    name: str = Field(..., description="Unique role name (e.g., 'role-engineer')")
    type: str = Field(default="role", description="Skill type (always 'role')")
    description: str = Field(..., description="Role description")
    version: str = Field(default="1.0.0", description="Skill version")
    author: Optional[str] = Field(default=None, description="Skill author")
    
    workflow: str = Field(..., description="Default workflow skill to use")
    default_mode: SkillMode = Field(default=SkillMode.COPILOT, description="Default execution mode")
    
    preferences: List[str] = Field(default_factory=list, description="Role preferences/mindset")
    system_prompt: Optional[str] = Field(default=None, description="System prompt for this role")
    trigger: Optional[str] = Field(default=None, description="When to trigger this role")
    goal: Optional[str] = Field(default=None, description="Goal of this role")


# ============================================================================
# Unified Skill Loader
# ============================================================================

class SkillLoader:
    """Loader for the three-level skill architecture."""
    
    def __init__(self, resources_dir: Path):
        self.resources_dir = resources_dir
        self._atoms: Dict[str, AtomSkillMetadata] = {}
        self._workflows: Dict[str, WorkflowSkillMetadata] = {}
        self._roles: Dict[str, RoleSkillMetadata] = {}
    
    def load_all(self) -> None:
        """Load all skills from resources directory."""
        self._load_atoms()
        self._load_workflows()
        self._load_roles()
    
    def _load_atoms(self) -> None:
        """Load atom skills from resources/atoms/."""
        atoms_dir = self.resources_dir / "atoms"
        if not atoms_dir.exists():
            return
        
        for skill_file in atoms_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(skill_file.read_text())
                atom = AtomSkillMetadata(**data)
                self._atoms[atom.name] = atom
            except Exception as e:
                print(f"Failed to load atom skill {skill_file}: {e}")
    
    def _load_workflows(self) -> None:
        """Load workflow skills from resources/workflows/."""
        workflows_dir = self.resources_dir / "workflows"
        if not workflows_dir.exists():
            return
        
        for skill_file in workflows_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(skill_file.read_text())
                workflow = WorkflowSkillMetadata(**data)
                self._workflows[workflow.name] = workflow
            except Exception as e:
                print(f"Failed to load workflow skill {skill_file}: {e}")
    
    def _load_roles(self) -> None:
        """Load role skills from resources/roles/."""
        roles_dir = self.resources_dir / "roles"
        if not roles_dir.exists():
            return
        
        for skill_file in roles_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(skill_file.read_text())
                role = RoleSkillMetadata(**data)
                self._roles[role.name] = role
            except Exception as e:
                print(f"Failed to load role skill {skill_file}: {e}")
    
    def get_atom(self, name: str) -> Optional[AtomSkillMetadata]:
        """Get an atom skill by name."""
        return self._atoms.get(name)
    
    def get_workflow(self, name: str) -> Optional[WorkflowSkillMetadata]:
        """Get a workflow skill by name."""
        return self._workflows.get(name)
    
    def get_role(self, name: str) -> Optional[RoleSkillMetadata]:
        """Get a role skill by name."""
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
            # Virtual stages (decision points) don't need atom skills
            if not stage.atom_skill or not stage.operation:
                continue
                
            atom = self.get_atom(stage.atom_skill)
            if not atom:
                errors.append(f"Stage '{stage.name}' uses unknown atom skill: {stage.atom_skill}")
            else:
                op_names = [op.name for op in atom.operations]
                if stage.operation not in op_names:
                    errors.append(
                        f"Stage '{stage.name}' uses unknown operation '{stage.operation}' "
                        f"in atom skill '{stage.atom_skill}'"
                    )
        
        return errors
