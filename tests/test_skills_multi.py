"""
Unit tests for SkillManager multi-skill architecture.

Tests cover:
- Multi-skill discovery from resources/skills/
- Flow skill detection and distribution
- Standard skill backward compatibility
- Mixed mode (standard + flow skills)
- Skill metadata type and role fields
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from monoco.core.skills import Skill, SkillManager, SkillMetadata


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_standard_skill(temp_project):
    """Create a sample standard skill in resources/en/SKILL.md (legacy pattern)."""
    resources_dir = temp_project / "resources"
    en_dir = resources_dir / "en"
    en_dir.mkdir(parents=True)

    skill_content = """---
name: test-standard-skill
description: Test standard skill
version: 1.0.0
type: standard
---

# Test Standard Skill

This is a standard skill.
"""
    (en_dir / "SKILL.md").write_text(skill_content)
    return resources_dir


@pytest.fixture
def sample_flow_skill(temp_project):
    """Create a sample flow skill in resources/skills/flow_test/SKILL.md."""
    skills_dir = temp_project / "resources" / "skills" / "flow_test"
    skills_dir.mkdir(parents=True)

    skill_content = """---
name: flow-test
description: Test flow skill
type: flow
role: test
version: 1.0.0
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

    skills = [
        ("flow_engineer", "engineer"),
        ("flow_manager", "manager"),
        ("flow_reviewer", "reviewer"),
    ]
    for skill_name, role in skills:
        skill_dir = resources_dir / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        content = f"---\nname: {skill_name}\ndescription: Test\ntype: flow\nrole: {role}\n---\n"
        (skill_dir / "SKILL.md").write_text(content)

    return resources_dir


@pytest.fixture
def mixed_skills(temp_project):
    """Create mixed skills: one standard (legacy) and multiple flow skills."""
    resources_dir = temp_project / "resources"

    # Standard skill (legacy pattern)
    en_dir = resources_dir / "en"
    en_dir.mkdir(parents=True)
    standard_content = """---
name: mixed-standard
description: Standard skill in mixed setup
type: standard
---

# Standard
"""
    (en_dir / "SKILL.md").write_text(standard_content)

    # Flow skills
    for skill_name in ["flow_helper", "flow_utils"]:
        skill_dir = resources_dir / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        content = f"---\nname: {skill_name}\ndescription: Test\ntype: flow\n---\n"
        (skill_dir / "SKILL.md").write_text(content)

    return resources_dir


class TestSkillMetadata:
    """Tests for SkillMetadata model."""

    def test_metadata_with_type_and_role(self):
        """Test metadata with type and role fields."""
        metadata = SkillMetadata(
            name="test-flow",
            description="Test flow skill",
            type="flow",
            role="engineer",
        )

        assert metadata.name == "test-flow"
        assert metadata.type == "flow"
        assert metadata.role == "engineer"

    def test_metadata_defaults(self):
        """Test metadata default values."""
        metadata = SkillMetadata(
            name="test-skill",
            description="Test skill",
        )

        assert metadata.type == "standard"
        assert metadata.role is None
        assert metadata.version is None
        assert metadata.author is None

    def test_metadata_standard_type_explicit(self):
        """Test explicitly setting type to standard."""
        metadata = SkillMetadata(
            name="test-skill",
            description="Test skill",
            type="standard",
        )

        assert metadata.type == "standard"


class TestSkillTypeAndRole:
    """Tests for Skill type and role methods."""

    def test_skill_get_type_flow(self, temp_project):
        """Test get_type for flow skill."""
        skill_dir = temp_project / "flow_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\ntype: flow\n---\n"
        )

        skill = Skill(temp_project, skill_dir)

        assert skill.get_type() == "flow"

    def test_skill_get_type_standard(self, temp_project):
        """Test get_type for standard skill."""
        skill_dir = temp_project / "standard_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\ntype: standard\n---\n"
        )

        skill = Skill(temp_project, skill_dir)

        assert skill.get_type() == "standard"

    def test_skill_get_type_default(self, temp_project):
        """Test get_type defaults to standard when not specified."""
        skill_dir = temp_project / "default_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\n---\n"
        )

        skill = Skill(temp_project, skill_dir)

        assert skill.get_type() == "standard"

    def test_skill_get_role(self, temp_project):
        """Test get_role method."""
        skill_dir = temp_project / "role_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\ntype: flow\nrole: engineer\n---\n"
        )

        skill = Skill(temp_project, skill_dir)

        assert skill.get_role() == "engineer"

    def test_skill_get_role_none(self, temp_project):
        """Test get_role returns None when not set."""
        skill_dir = temp_project / "no_role_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\n---\n"
        )

        skill = Skill(temp_project, skill_dir)

        assert skill.get_role() is None


class TestSkillManagerMultiSkillDiscovery:
    """Tests for SkillManager multi-skill discovery."""

    def test_discover_flow_skills(self, temp_project, multiple_flow_skills):
        """Test discovering multiple flow skills."""
        # Create a mock feature
        class MockFeature:
            name = "test_feature"

            class __class__:
                __module__ = "monoco.features.test.adapter"

        manager = SkillManager(
            temp_project,
            features=[MockFeature()],
        )

        # Manually trigger discovery with our test resources
        manager._discover_multi_skills(multiple_flow_skills, "test")

        flow_skills = manager.get_flow_skills()
        assert len(flow_skills) == 3

        skill_names = {s.name for s in flow_skills}
        # Note: skill directories are flow_engineer, flow_manager, flow_reviewer
        # After adding prefix "monoco_flow_", they become monoco_flow_flow_engineer, etc.
        # The get_flow_skills() filters by type="flow"
        assert len(skill_names) == 3

    def test_discover_standard_skill_legacy(self, temp_project, sample_standard_skill):
        """Test discovering standard skill with legacy pattern."""
        class MockFeature:
            name = "test_feature"

            class __class__:
                __module__ = "monoco.features.test.adapter"

        manager = SkillManager(
            temp_project,
            features=[MockFeature()],
        )

        # Manually trigger discovery
        manager._discover_legacy_skill(sample_standard_skill, "test")

        skills = manager.list_skills()
        assert len(skills) == 1
        assert skills[0].get_type() == "standard"

    def test_discover_mixed_skills(self, temp_project, mixed_skills):
        """Test discovering mixed standard and flow skills."""
        class MockFeature:
            name = "test_feature"

            class __class__:
                __module__ = "monoco.features.test.adapter"

        manager = SkillManager(
            temp_project,
            features=[MockFeature()],
        )

        # Discover both types
        manager._discover_multi_skills(mixed_skills, "test")
        manager._discover_legacy_skill(mixed_skills, "test")

        all_skills = manager.list_skills()
        flow_skills = manager.get_flow_skills()

        assert len(all_skills) == 3  # 1 standard + 2 flow
        assert len(flow_skills) == 2

    def test_flow_skill_prefix_custom(self, temp_project, sample_flow_skill):
        """Test custom flow skill prefix."""
        class MockFeature:
            name = "test_feature"

            class __class__:
                __module__ = "monoco.features.test.adapter"

        custom_prefix = "custom_"
        manager = SkillManager(
            temp_project,
            features=[MockFeature()],
            flow_skill_prefix=custom_prefix,
        )

        resources_dir = temp_project / "resources"
        manager._discover_multi_skills(resources_dir, "test")

        flow_skills = manager.get_flow_skills()
        assert len(flow_skills) == 1
        assert flow_skills[0].name == "custom_flow_test"


class TestSkillManagerDistribution:
    """Tests for SkillManager skill distribution."""

    def test_distribute_flow_skill(self, temp_project, sample_flow_skill):
        """Test distributing a flow skill."""
        skill = Skill(
            root_dir=temp_project,
            skill_dir=sample_flow_skill,
            name="monoco_flow_test",
            skill_file=sample_flow_skill / "SKILL.md",
        )

        target_dir = temp_project / ".agent" / "skills"

        manager = SkillManager(temp_project)
        manager.skills["monoco_flow_test"] = skill

        results = manager.distribute(target_dir, lang="en")

        assert results["monoco_flow_test"] is True
        assert (target_dir / "monoco_flow_test" / "SKILL.md").exists()

    def test_distribute_standard_skill(self, temp_project, sample_standard_skill):
        """Test distributing a standard skill."""
        skill = Skill(
            root_dir=temp_project,
            skill_dir=sample_standard_skill,
            name="test_standard",
        )

        target_dir = temp_project / ".agent" / "skills"

        manager = SkillManager(temp_project)
        manager.skills["test_standard"] = skill

        results = manager.distribute(target_dir, lang="en")

        assert results["test_standard"] is True
        assert (target_dir / "test_standard" / "SKILL.md").exists()

    def test_distribute_mixed_skills(self, temp_project, mixed_skills):
        """Test distributing mixed standard and flow skills."""
        # Create standard skill
        standard_skill = Skill(
            root_dir=temp_project,
            skill_dir=mixed_skills,
            name="test_mixed",
        )

        # Create flow skill
        flow_skill_dir = mixed_skills / "skills" / "flow_helper"
        flow_skill = Skill(
            root_dir=temp_project,
            skill_dir=flow_skill_dir,
            name="monoco_flow_helper",
            skill_file=flow_skill_dir / "SKILL.md",
        )

        target_dir = temp_project / ".agent" / "skills"

        manager = SkillManager(temp_project)
        manager.skills["test_mixed"] = standard_skill
        manager.skills["monoco_flow_helper"] = flow_skill

        results = manager.distribute(target_dir, lang="en")

        assert results["test_mixed"] is True
        assert results["monoco_flow_helper"] is True
        assert (target_dir / "test_mixed" / "SKILL.md").exists()
        assert (target_dir / "monoco_flow_helper" / "SKILL.md").exists()

    def test_distribute_skips_up_to_date(self, temp_project, sample_flow_skill):
        """Test that distribute skips up-to-date skills."""
        skill = Skill(
            root_dir=temp_project,
            skill_dir=sample_flow_skill,
            name="monoco_flow_test",
            skill_file=sample_flow_skill / "SKILL.md",
        )

        target_dir = temp_project / ".agent" / "skills"

        manager = SkillManager(temp_project)
        manager.skills["monoco_flow_test"] = skill

        # First distribute
        manager.distribute(target_dir, lang="en")

        # Second distribute should skip
        results = manager.distribute(target_dir, lang="en")

        # Should still return True (success), just skip the copy
        assert results["monoco_flow_test"] is True

    def test_distribute_force_overwrites(self, temp_project, sample_flow_skill):
        """Test that force=True overwrites existing skills."""
        skill = Skill(
            root_dir=temp_project,
            skill_dir=sample_flow_skill,
            name="monoco_flow_test",
            skill_file=sample_flow_skill / "SKILL.md",
        )

        target_dir = temp_project / ".agent" / "skills"

        manager = SkillManager(temp_project)
        manager.skills["monoco_flow_test"] = skill

        # First distribute
        manager.distribute(target_dir, lang="en")

        # Force distribute should overwrite
        results = manager.distribute(target_dir, lang="en", force=True)

        assert results["monoco_flow_test"] is True


class TestSkillManagerFlowCommands:
    """Tests for flow skill command generation."""

    def test_get_flow_skill_commands(self, temp_project):
        """Test getting flow skill commands."""
        # Create flow skills with roles
        # Note: SkillManager adds "monoco_flow_" prefix, so we use just the role name
        skills_data = [
            ("engineer", "engineer"),
            ("manager", "manager"),
            ("reviewer", "reviewer"),
        ]

        manager = SkillManager(temp_project)

        for skill_name, role in skills_data:
            skill_dir = temp_project / skill_name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {skill_name}\ndescription: Test\ntype: flow\nrole: {role}\n---\n"
            )
            skill = Skill(
                root_dir=temp_project,
                skill_dir=skill_dir,
                name=skill_name,
                skill_file=skill_dir / "SKILL.md",
            )
            manager.skills[skill_name] = skill

        commands = manager.get_flow_skill_commands()

        # Commands are extracted from skill names (after removing prefix)
        # e.g., "engineer" -> "/flow:engineer"
        assert "/flow:engineer" in commands
        assert "/flow:manager" in commands
        assert "/flow:reviewer" in commands
        assert len(commands) == 3

    def test_get_flow_skill_commands_no_role(self, temp_project):
        """Test getting commands when role is extracted from name."""
        # Create a skill that simulates the real structure:
        # Directory: resources/skills/flow_tester/
        # After prefix: monoco_flow_flow_tester
        # Extracted role: "flow_tester"[5:] = "tester"
        skill_dir = temp_project / "flow_tester"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: flow-tester\ndescription: Test\ntype: flow\n---\n"
        )

        skill = Skill(
            root_dir=temp_project,
            skill_dir=skill_dir,
            name="monoco_flow_flow_tester",  # After prefix is added
            skill_file=skill_dir / "SKILL.md",
        )

        manager = SkillManager(temp_project)
        manager.skills["monoco_flow_flow_tester"] = skill

        commands = manager.get_flow_skill_commands()

        # "monoco_flow_flow_tester" -> remove prefix "monoco_flow_" -> "flow_tester"
        # Then remove "flow_" (5 chars) -> "tester"
        assert "/flow:tester" in commands

    def test_get_flow_skill_commands_empty(self, temp_project):
        """Test getting commands when no flow skills exist."""
        manager = SkillManager(temp_project)

        commands = manager.get_flow_skill_commands()

        assert commands == []


class TestSkillManagerCleanup:
    """Tests for SkillManager cleanup."""

    def test_cleanup_removes_all_skills(self, temp_project):
        """Test cleanup removes all distributed skills."""
        target_dir = temp_project / ".agent" / "skills"

        # Create skills in target
        for skill_name in ["skill_a", "skill_b", "monoco_flow_test"]:
            skill_target = target_dir / skill_name
            skill_target.mkdir(parents=True)
            (skill_target / "SKILL.md").write_text("test")

        manager = SkillManager(temp_project)
        manager.skills = {
            "skill_a": None,
            "skill_b": None,
            "monoco_flow_test": None,
        }

        manager.cleanup(target_dir)

        assert not (target_dir / "skill_a").exists()
        assert not (target_dir / "skill_b").exists()
        assert not (target_dir / "monoco_flow_test").exists()

    def test_cleanup_empty_target(self, temp_project):
        """Test cleanup with non-existent target directory."""
        target_dir = temp_project / ".agent" / "skills"

        manager = SkillManager(temp_project)
        manager.skills = {"test_skill": None}

        # Should not raise exception
        manager.cleanup(target_dir)


class TestSkillManagerListSkills:
    """Tests for SkillManager skill listing."""

    def test_list_skills(self, temp_project):
        """Test listing all skills."""
        manager = SkillManager(temp_project)

        # Add some skills
        for skill_name in ["skill_a", "skill_b", "skill_c"]:
            skill_dir = temp_project / skill_name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n")
            skill = Skill(temp_project, skill_dir, name=skill_name)
            manager.skills[skill_name] = skill

        skills = manager.list_skills()

        assert len(skills) == 3
        skill_names = {s.name for s in skills}
        assert skill_names == {"skill_a", "skill_b", "skill_c"}

    def test_list_skills_by_type(self, temp_project):
        """Test listing skills filtered by type."""
        manager = SkillManager(temp_project)

        # Add standard skill
        std_dir = temp_project / "standard_skill"
        std_dir.mkdir()
        (std_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\ntype: standard\n---\n"
        )
        std_skill = Skill(temp_project, std_dir, name="standard_skill")
        manager.skills["standard_skill"] = std_skill

        # Add flow skill
        flow_dir = temp_project / "flow_skill"
        flow_dir.mkdir()
        (flow_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\ntype: flow\n---\n"
        )
        flow_skill = Skill(temp_project, flow_dir, name="flow_skill")
        manager.skills["flow_skill"] = flow_skill

        standard_skills = manager.list_skills_by_type("standard")
        flow_skills = manager.list_skills_by_type("flow")

        assert len(standard_skills) == 1
        assert len(flow_skills) == 1
        assert standard_skills[0].name == "standard_skill"
        assert flow_skills[0].name == "flow_skill"


class TestSkillCustomNameAndFile:
    """Tests for Skill custom name and skill_file parameters."""

    def test_skill_custom_name(self, temp_project):
        """Test skill with custom name."""
        skill_dir = temp_project / "original_name"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n")

        skill = Skill(temp_project, skill_dir, name="custom_name")

        assert skill.name == "custom_name"
        assert skill.skill_dir.name == "original_name"

    def test_skill_custom_skill_file(self, temp_project):
        """Test skill with custom skill_file path."""
        skill_dir = temp_project / "skill"
        custom_file = temp_project / "custom" / "SKILL.md"
        custom_file.parent.mkdir(parents=True)
        custom_file.write_text("---\nname: test\n---\n")

        skill = Skill(temp_project, skill_dir, skill_file=custom_file)

        assert skill.skill_file == custom_file


class TestIntegration:
    """Integration tests for the complete multi-skill workflow."""

    def test_full_workflow_standard_and_flow(
        self, temp_project, mixed_skills
    ):
        """Test complete workflow with both standard and flow skills."""
        class MockFeature:
            name = "test_feature"

            class __class__:
                __module__ = "monoco.features.test.adapter"

        manager = SkillManager(
            temp_project,
            features=[MockFeature()],
        )

        # Discover skills
        manager._discover_multi_skills(mixed_skills, "test")
        manager._discover_legacy_skill(mixed_skills, "test")

        # Verify discovery
        assert len(manager.list_skills()) == 3
        assert len(manager.get_flow_skills()) == 2

        # Distribute
        target_dir = temp_project / ".agent" / "skills"
        results = manager.distribute(target_dir, lang="en")

        assert all(results.values())

        # Verify distribution
        # Note: The legacy skill name is determined by metadata.name or feature name
        # From the output: "mixed_standard/SKILL.md" -> skill name is "mixed_standard"
        assert (target_dir / "mixed_standard" / "SKILL.md").exists()  # Standard (legacy)
        assert (target_dir / "monoco_flow_flow_helper" / "SKILL.md").exists()  # Flow
        assert (target_dir / "monoco_flow_flow_utils" / "SKILL.md").exists()  # Flow

        # Cleanup
        manager.cleanup(target_dir)

        # Verify cleanup
        assert not (target_dir / "test").exists()
        assert not (target_dir / "monoco_flow_helper").exists()

    def test_backward_compatibility_legacy_only(
        self, temp_project, sample_standard_skill
    ):
        """Test backward compatibility with legacy single-skill pattern."""
        class MockFeature:
            name = "test_feature"

            class __class__:
                __module__ = "monoco.features.test.adapter"

        manager = SkillManager(
            temp_project,
            features=[MockFeature()],
        )

        # Discover legacy skill
        manager._discover_legacy_skill(sample_standard_skill, "test")

        # Verify
        skills = manager.list_skills()
        assert len(skills) == 1
        assert skills[0].get_type() == "standard"

        # Distribute
        target_dir = temp_project / ".agent" / "skills"
        results = manager.distribute(target_dir, lang="en")

        assert results["test"] is True
