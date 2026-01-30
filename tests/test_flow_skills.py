"""
Unit tests for Flow Skills manager.

Tests cover:
- Flow skill discovery
- Skill injection
- Gitignore handling
- Skill removal
- Command generation
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from monoco.features.agent.flow_skills import (
    discover_flow_skills,
    inject_flow_skill,
    sync_flow_skills,
    update_gitignore,
    remove_flow_skills,
    get_flow_skill_commands,
    FLOW_SKILL_PREFIX,
    GITIGNORE_PATTERN,
)


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_flow_skill(temp_project):
    """Create a sample flow skill directory."""
    skills_dir = temp_project / "resources" / "skills" / "flow_test"
    skills_dir.mkdir(parents=True)

    skill_content = """---
name: flow-test
description: Test flow skill
type: flow
role: test
---

# Test Flow

```mermaid
stateDiagram-v2
    [*] --> Start
    Start --> End
    End --> [*]
```
"""
    (skills_dir / "SKILL.md").write_text(skill_content)
    return skills_dir


@pytest.fixture
def multiple_flow_skills(temp_project):
    """Create multiple flow skill directories."""
    resources_dir = temp_project / "resources"

    skills = ["flow_engineer", "flow_manager", "flow_reviewer"]
    for skill_name in skills:
        skill_dir = resources_dir / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(f"---\nname: {skill_name}\ntype: flow\n---\n")

    return resources_dir


class TestDiscoverFlowSkills:
    """Tests for discover_flow_skills function."""

    def test_discover_single_skill(self, temp_project, sample_flow_skill):
        """Test discovering a single flow skill."""
        resources_dir = temp_project / "resources"
        skills = discover_flow_skills(resources_dir)

        assert len(skills) == 1
        assert skills[0].name == "flow_test"

    def test_discover_multiple_skills(self, temp_project, multiple_flow_skills):
        """Test discovering multiple flow skills."""
        skills = discover_flow_skills(multiple_flow_skills)

        assert len(skills) == 3
        skill_names = {s.name for s in skills}
        assert skill_names == {"flow_engineer", "flow_manager", "flow_reviewer"}

    def test_discover_no_skills(self, temp_project):
        """Test discovering when no flow skills exist."""
        resources_dir = temp_project / "resources"
        skills = discover_flow_skills(resources_dir)

        assert len(skills) == 0

    def test_discover_skills_directory_missing(self, temp_project):
        """Test discovering when skills directory doesn't exist."""
        resources_dir = temp_project / "resources"
        skills = discover_flow_skills(resources_dir)

        assert len(skills) == 0

    def test_discover_non_flow_directories_ignored(self, temp_project):
        """Test that non-flow directories are ignored."""
        resources_dir = temp_project / "resources"

        # Create flow skill
        flow_dir = resources_dir / "skills" / "flow_valid"
        flow_dir.mkdir(parents=True)
        (flow_dir / "SKILL.md").write_text("---\ntype: flow\n---\n")

        # Create non-flow directory
        other_dir = resources_dir / "skills" / "other_skill"
        other_dir.mkdir(parents=True)
        (other_dir / "SKILL.md").write_text("---\ntype: other\n---\n")

        skills = discover_flow_skills(resources_dir)

        assert len(skills) == 1
        assert skills[0].name == "flow_valid"

    def test_discover_skills_without_skill_md_ignored(self, temp_project):
        """Test that directories without SKILL.md are ignored."""
        resources_dir = temp_project / "resources"

        # Create flow skill with SKILL.md
        valid_dir = resources_dir / "skills" / "flow_valid"
        valid_dir.mkdir(parents=True)
        (valid_dir / "SKILL.md").write_text("---\ntype: flow\n---\n")

        # Create flow skill without SKILL.md
        invalid_dir = resources_dir / "skills" / "flow_invalid"
        invalid_dir.mkdir(parents=True)

        skills = discover_flow_skills(resources_dir)

        assert len(skills) == 1
        assert skills[0].name == "flow_valid"

    def test_discover_new_pattern_type_flow(self, temp_project):
        """Test discovering skills with 'type: flow' front matter (new pattern)."""
        resources_dir = temp_project / "resources"

        # Create skill with new pattern (not starting with flow_)
        new_pattern_dir = resources_dir / "skills" / "i18n_workflow"
        new_pattern_dir.mkdir(parents=True)
        (new_pattern_dir / "SKILL.md").write_text(
            "---\nname: i18n-workflow\ntype: flow\ndomain: i18n\n---\n\n# I18n Workflow\n"
        )

        # Create skill with legacy pattern
        legacy_dir = resources_dir / "skills" / "flow_engineer"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "SKILL.md").write_text("---\ntype: flow\n---\n")

        # Create non-flow skill
        non_flow_dir = resources_dir / "skills" / "regular_skill"
        non_flow_dir.mkdir(parents=True)
        (non_flow_dir / "SKILL.md").write_text("---\ntype: command\n---\n")

        skills = discover_flow_skills(resources_dir)

        assert len(skills) == 2
        skill_names = {s.name for s in skills}
        assert skill_names == {"i18n_workflow", "flow_engineer"}

    def test_discover_new_pattern_without_front_matter_ignored(self, temp_project):
        """Test that skills without 'type: flow' front matter are ignored."""
        resources_dir = temp_project / "resources"

        # Create skill without front matter
        no_front_dir = resources_dir / "skills" / "no_front_matter"
        no_front_dir.mkdir(parents=True)
        (no_front_dir / "SKILL.md").write_text("# Just a regular skill\n")

        # Create skill with front matter but wrong type
        wrong_type_dir = resources_dir / "skills" / "wrong_type"
        wrong_type_dir.mkdir(parents=True)
        (wrong_type_dir / "SKILL.md").write_text("---\ntype: command\n---\n")

        skills = discover_flow_skills(resources_dir)

        assert len(skills) == 0


class TestInjectFlowSkill:
    """Tests for inject_flow_skill function."""

    def test_inject_single_skill(self, temp_project, sample_flow_skill):
        """Test injecting a single flow skill."""
        target_dir = temp_project / ".agent" / "skills"

        result = inject_flow_skill(sample_flow_skill, target_dir)

        assert result is True
        assert (target_dir / f"{FLOW_SKILL_PREFIX}flow_test" / "SKILL.md").exists()

    def test_inject_with_custom_prefix(self, temp_project, sample_flow_skill):
        """Test injecting with a custom prefix."""
        target_dir = temp_project / ".agent" / "skills"
        custom_prefix = "custom_"

        result = inject_flow_skill(sample_flow_skill, target_dir, custom_prefix)

        assert result is True
        assert (target_dir / "custom_flow_test" / "SKILL.md").exists()

    def test_inject_overwrites_existing(self, temp_project, sample_flow_skill):
        """Test that injection overwrites existing skill."""
        target_dir = temp_project / ".agent" / "skills"
        target_skill_dir = target_dir / f"{FLOW_SKILL_PREFIX}flow_test"
        target_skill_dir.mkdir(parents=True)

        # Create old content
        old_file = target_skill_dir / "SKILL.md"
        old_file.write_text("old content")

        # Inject new content
        result = inject_flow_skill(sample_flow_skill, target_dir)

        assert result is True
        content = (target_skill_dir / "SKILL.md").read_text()
        assert "name: flow-test" in content
        assert "old content" not in content

    def test_inject_preserves_directory_structure(self, temp_project):
        """Test that injection preserves subdirectory structure."""
        resources_dir = temp_project / "resources"
        skill_dir = resources_dir / "skills" / "flow_complex"
        skill_dir.mkdir(parents=True)

        # Create SKILL.md
        (skill_dir / "SKILL.md").write_text("---\ntype: flow\n---\n")

        # Create subdirectory with extra file
        subdir = skill_dir / "examples"
        subdir.mkdir()
        (subdir / "example.py").write_text("# example")

        target_dir = temp_project / ".agent" / "skills"
        result = inject_flow_skill(skill_dir, target_dir)

        assert result is True
        assert (target_dir / f"{FLOW_SKILL_PREFIX}flow_complex" / "examples" / "example.py").exists()


class TestSyncFlowSkills:
    """Tests for sync_flow_skills function."""

    def test_sync_multiple_skills(self, temp_project, multiple_flow_skills):
        """Test synchronizing multiple flow skills."""
        target_dir = temp_project / ".agent" / "skills"

        results = sync_flow_skills(multiple_flow_skills, target_dir)

        assert results["injected"] == 3
        assert results["failed"] == 0
        assert (target_dir / f"{FLOW_SKILL_PREFIX}flow_engineer").exists()
        assert (target_dir / f"{FLOW_SKILL_PREFIX}flow_manager").exists()
        assert (target_dir / f"{FLOW_SKILL_PREFIX}flow_reviewer").exists()

    def test_sync_skips_up_to_date(self, temp_project, multiple_flow_skills):
        """Test that sync skips skills that are up to date."""
        target_dir = temp_project / ".agent" / "skills"

        # First sync
        sync_flow_skills(multiple_flow_skills, target_dir)

        # Second sync should skip
        results = sync_flow_skills(multiple_flow_skills, target_dir)

        assert results["injected"] == 0
        assert results["failed"] == 0

    def test_sync_force_overwrites(self, temp_project, multiple_flow_skills):
        """Test that force=True overwrites existing skills."""
        target_dir = temp_project / ".agent" / "skills"

        # First sync
        sync_flow_skills(multiple_flow_skills, target_dir)

        # Force sync should re-inject
        results = sync_flow_skills(multiple_flow_skills, target_dir, force=True)

        assert results["injected"] == 3

    def test_sync_creates_target_directory(self, temp_project, sample_flow_skill):
        """Test that sync creates target directory if it doesn't exist."""
        resources_dir = temp_project / "resources"
        target_dir = temp_project / ".agent" / "skills"

        assert not target_dir.exists()

        results = sync_flow_skills(resources_dir, target_dir)

        assert target_dir.exists()
        assert results["injected"] == 1

    def test_sync_no_skills_found(self, temp_project):
        """Test sync when no skills are found."""
        resources_dir = temp_project / "resources"
        target_dir = temp_project / ".agent" / "skills"

        results = sync_flow_skills(resources_dir, target_dir)

        assert results["injected"] == 0
        assert results["failed"] == 0

    def test_sync_removes_orphaned_with_force(self, temp_project, multiple_flow_skills):
        """Test that force=True removes orphaned skills."""
        target_dir = temp_project / ".agent" / "skills"

        # Create an orphaned skill
        orphaned_dir = target_dir / f"{FLOW_SKILL_PREFIX}flow_orphaned"
        orphaned_dir.mkdir(parents=True)
        (orphaned_dir / "SKILL.md").write_text("orphaned")

        # Sync with force
        results = sync_flow_skills(multiple_flow_skills, target_dir, force=True)

        assert results["removed"] == 1
        assert not orphaned_dir.exists()


class TestUpdateGitignore:
    """Tests for update_gitignore function."""

    def test_adds_pattern_to_new_gitignore(self, temp_project):
        """Test adding pattern to new .gitignore."""
        result = update_gitignore(temp_project)

        assert result is True
        gitignore = temp_project / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert GITIGNORE_PATTERN in content
        assert "# Monoco Flow Skills" in content

    def test_adds_pattern_to_existing_gitignore(self, temp_project):
        """Test adding pattern to existing .gitignore."""
        gitignore = temp_project / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n")

        result = update_gitignore(temp_project)

        assert result is True
        content = gitignore.read_text()
        assert "*.pyc" in content
        assert GITIGNORE_PATTERN in content

    def test_skips_if_pattern_exists(self, temp_project):
        """Test skipping if pattern already exists."""
        gitignore = temp_project / ".gitignore"
        gitignore.write_text(f"{GITIGNORE_PATTERN}\n")

        result = update_gitignore(temp_project)

        assert result is True
        content = gitignore.read_text()
        # Should not add duplicate
        assert content.count(GITIGNORE_PATTERN) == 1

    def test_skips_if_pattern_with_slash_exists(self, temp_project):
        """Test skipping if pattern with leading slash exists."""
        gitignore = temp_project / ".gitignore"
        gitignore.write_text(f"/{GITIGNORE_PATTERN}\n")

        result = update_gitignore(temp_project)

        assert result is True
        content = gitignore.read_text()
        # Should not add duplicate
        assert content.count(GITIGNORE_PATTERN) == 1


class TestRemoveFlowSkills:
    """Tests for remove_flow_skills function."""

    def test_removes_all_flow_skills(self, temp_project):
        """Test removing all flow skills."""
        target_dir = temp_project / ".agent" / "skills"

        # Create flow skills
        for skill in ["flow_engineer", "flow_manager"]:
            skill_dir = target_dir / f"{FLOW_SKILL_PREFIX}{skill}"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("skill")

        count = remove_flow_skills(target_dir)

        assert count == 2
        assert not (target_dir / f"{FLOW_SKILL_PREFIX}flow_engineer").exists()
        assert not (target_dir / f"{FLOW_SKILL_PREFIX}flow_manager").exists()

    def test_removes_only_prefixed_skills(self, temp_project):
        """Test that only prefixed skills are removed."""
        target_dir = temp_project / ".agent" / "skills"

        # Create flow skill with prefix
        flow_dir = target_dir / f"{FLOW_SKILL_PREFIX}flow_test"
        flow_dir.mkdir(parents=True)
        (flow_dir / "SKILL.md").write_text("flow")

        # Create other skill without prefix
        other_dir = target_dir / "other_skill"
        other_dir.mkdir(parents=True)
        (other_dir / "SKILL.md").write_text("other")

        count = remove_flow_skills(target_dir)

        assert count == 1
        assert not flow_dir.exists()
        assert other_dir.exists()

    def test_returns_zero_if_target_missing(self, temp_project):
        """Test returning zero if target directory doesn't exist."""
        target_dir = temp_project / ".agent" / "skills"

        count = remove_flow_skills(target_dir)

        assert count == 0

    def test_returns_zero_if_no_flow_skills(self, temp_project):
        """Test returning zero if no flow skills exist."""
        target_dir = temp_project / ".agent" / "skills"
        target_dir.mkdir(parents=True)

        # Create non-flow directory
        other_dir = target_dir / "other_skill"
        other_dir.mkdir()
        (other_dir / "SKILL.md").write_text("other")

        count = remove_flow_skills(target_dir)

        assert count == 0


class TestGetFlowSkillCommands:
    """Tests for get_flow_skill_commands function."""

    def test_get_commands(self, temp_project):
        """Test getting flow skill commands."""
        target_dir = temp_project / ".agent" / "skills"

        # Create flow skills
        for skill in ["flow_engineer", "flow_manager", "flow_reviewer"]:
            skill_dir = target_dir / f"{FLOW_SKILL_PREFIX}{skill}"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("skill")

        commands = get_flow_skill_commands(target_dir)

        assert "/flow:engineer" in commands
        assert "/flow:manager" in commands
        assert "/flow:reviewer" in commands

    def test_returns_empty_if_target_missing(self, temp_project):
        """Test returning empty list if target doesn't exist."""
        target_dir = temp_project / ".agent" / "skills"

        commands = get_flow_skill_commands(target_dir)

        assert commands == []

    def test_returns_empty_if_no_flow_skills(self, temp_project):
        """Test returning empty list if no flow skills exist."""
        target_dir = temp_project / ".agent" / "skills"
        target_dir.mkdir(parents=True)

        commands = get_flow_skill_commands(target_dir)

        assert commands == []

    def test_ignores_non_flow_directories(self, temp_project):
        """Test that non-flow directories are ignored."""
        target_dir = temp_project / ".agent" / "skills"

        # Create flow skill
        flow_dir = target_dir / f"{FLOW_SKILL_PREFIX}flow_test"
        flow_dir.mkdir(parents=True)
        (flow_dir / "SKILL.md").write_text("flow")

        # Create other skill
        other_dir = target_dir / "other_skill"
        other_dir.mkdir(parents=True)
        (other_dir / "SKILL.md").write_text("other")

        commands = get_flow_skill_commands(target_dir)

        assert commands == ["/flow:test"]


class TestIntegration:
    """Integration tests for the complete flow."""

    def test_full_sync_workflow(self, temp_project, multiple_flow_skills):
        """Test the complete sync workflow."""
        target_dir = temp_project / ".agent" / "skills"

        # 1. Sync skills
        results = sync_flow_skills(multiple_flow_skills, target_dir)
        assert results["injected"] == 3

        # 2. Update gitignore
        result = update_gitignore(temp_project)
        assert result is True

        # 3. Verify gitignore
        gitignore = temp_project / ".gitignore"
        assert GITIGNORE_PATTERN in gitignore.read_text()

        # 4. Get commands
        commands = get_flow_skill_commands(target_dir)
        assert len(commands) == 3

        # 5. Remove skills
        count = remove_flow_skills(target_dir)
        assert count == 3

        # 6. Verify removal
        assert not any(target_dir.iterdir())

    def test_idempotent_sync(self, temp_project, multiple_flow_skills):
        """Test that sync is idempotent."""
        target_dir = temp_project / ".agent" / "skills"

        # First sync
        results1 = sync_flow_skills(multiple_flow_skills, target_dir)
        assert results1["injected"] == 3

        # Second sync (no changes)
        results2 = sync_flow_skills(multiple_flow_skills, target_dir)
        assert results2["injected"] == 0

        # Third sync (still no changes)
        results3 = sync_flow_skills(multiple_flow_skills, target_dir)
        assert results3["injected"] == 0

        # All skills should still exist
        assert (target_dir / f"{FLOW_SKILL_PREFIX}flow_engineer").exists()
        assert (target_dir / f"{FLOW_SKILL_PREFIX}flow_manager").exists()
        assert (target_dir / f"{FLOW_SKILL_PREFIX}flow_reviewer").exists()
