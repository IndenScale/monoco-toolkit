"""
Unit tests for SkillManager multi-skill architecture with i18n support.

Tests cover:
- Multi-skill discovery from resources/{lang}/skills/
- Flow skill detection and distribution
- Standard skill support
- Skill metadata type and role fields
- i18n language support
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
    """Create a sample standard skill in resources/en/skills/test_standard/SKILL.md."""
    resources_dir = temp_project / "resources"
    skill_dir = resources_dir / "en" / "skills" / "test_standard"
    skill_dir.mkdir(parents=True)

    skill_content = """---
name: test-standard-skill
description: Test standard skill
version: 1.0.0
type: standard
---

# Test Standard Skill

This is a standard skill.
"""
    (skill_dir / "SKILL.md").write_text(skill_content)
    
    # Also create zh version
    zh_skill_dir = resources_dir / "zh" / "skills" / "test_standard"
    zh_skill_dir.mkdir(parents=True)
    (zh_skill_dir / "SKILL.md").write_text(skill_content)
    
    return resources_dir


@pytest.fixture
def sample_flow_skill(temp_project):
    """Create a sample flow skill in resources/en/skills/flow_test/SKILL.md."""
    resources_dir = temp_project / "resources"
    
    # Create en version
    skill_dir = resources_dir / "en" / "skills" / "flow_test"
    skill_dir.mkdir(parents=True)

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
    (skill_dir / "SKILL.md").write_text(skill_content)
    
    # Create zh version
    zh_skill_dir = resources_dir / "zh" / "skills" / "flow_test"
    zh_skill_dir.mkdir(parents=True)
    (zh_skill_dir / "SKILL.md").write_text(skill_content)
    
    return resources_dir


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
        # Create en version
        skill_dir = resources_dir / "en" / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        content = f"---\nname: {skill_name}\ndescription: Test\ntype: flow\nrole: {role}\n---\n"
        (skill_dir / "SKILL.md").write_text(content)
        
        # Create zh version
        zh_skill_dir = resources_dir / "zh" / "skills" / skill_name
        zh_skill_dir.mkdir(parents=True)
        (zh_skill_dir / "SKILL.md").write_text(content)

    return resources_dir


@pytest.fixture
def mixed_skills(temp_project):
    """Create mixed skills: one standard and multiple flow skills."""
    resources_dir = temp_project / "resources"

    # Standard skill
    std_en_dir = resources_dir / "en" / "skills" / "mixed_standard"
    std_en_dir.mkdir(parents=True)
    standard_content = """---
name: mixed-standard
description: Standard skill in mixed setup
type: standard
---

# Standard
"""
    (std_en_dir / "SKILL.md").write_text(standard_content)
    
    std_zh_dir = resources_dir / "zh" / "skills" / "mixed_standard"
    std_zh_dir.mkdir(parents=True)
    (std_zh_dir / "SKILL.md").write_text(standard_content)

    # Flow skills
    for skill_name in ["flow_helper", "flow_utils"]:
        # en version
        skill_dir = resources_dir / "en" / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        content = f"---\nname: {skill_name}\ndescription: Test\ntype: flow\n---\n"
        (skill_dir / "SKILL.md").write_text(content)
        
        # zh version
        zh_skill_dir = resources_dir / "zh" / "skills" / skill_name
        zh_skill_dir.mkdir(parents=True)
        (zh_skill_dir / "SKILL.md").write_text(content)

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
        resources_dir = temp_project / "resources"
        skill_dir = resources_dir / "en" / "skills" / "flow_skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\ntype: flow\n---\n"
        )

        skill = Skill(temp_project, "flow_skill", resources_dir)

        assert skill.get_type() == "flow"

    def test_skill_get_type_standard(self, temp_project):
        """Test get_type for standard skill."""
        resources_dir = temp_project / "resources"
        skill_dir = resources_dir / "en" / "skills" / "standard_skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\ntype: standard\n---\n"
        )

        skill = Skill(temp_project, "standard_skill", resources_dir)

        assert skill.get_type() == "standard"

    def test_skill_get_type_default(self, temp_project):
        """Test get_type defaults to standard when not specified."""
        resources_dir = temp_project / "resources"
        skill_dir = resources_dir / "en" / "skills" / "default_skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\n---\n"
        )

        skill = Skill(temp_project, "default_skill", resources_dir)

        assert skill.get_type() == "standard"

    def test_skill_get_role(self, temp_project):
        """Test get_role method."""
        resources_dir = temp_project / "resources"
        skill_dir = resources_dir / "en" / "skills" / "role_skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\ntype: flow\nrole: engineer\n---\n"
        )

        skill = Skill(temp_project, "role_skill", resources_dir)

        assert skill.get_role() == "engineer"

    def test_skill_get_role_none(self, temp_project):
        """Test get_role returns None when not set."""
        resources_dir = temp_project / "resources"
        skill_dir = resources_dir / "en" / "skills" / "no_role_skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\n---\n"
        )

        skill = Skill(temp_project, "no_role_skill", resources_dir)

        assert skill.get_role() is None


class TestSkillLanguages:
    """Tests for Skill language support."""

    def test_get_languages_multiple(self, temp_project):
        """Test detecting multiple language versions."""
        resources_dir = temp_project / "resources"
        
        # Create en and zh versions
        (resources_dir / "en" / "skills" / "test_skill").mkdir(parents=True)
        (resources_dir / "en" / "skills" / "test_skill" / "SKILL.md").write_text(
            "---\nname: test\n---\n"
        )
        (resources_dir / "zh" / "skills" / "test_skill").mkdir(parents=True)
        (resources_dir / "zh" / "skills" / "test_skill" / "SKILL.md").write_text(
            "---\nname: test\n---\n"
        )

        skill = Skill(temp_project, "test_skill", resources_dir)
        languages = skill.get_languages()

        assert "en" in languages
        assert "zh" in languages
        assert len(languages) == 2

    def test_get_languages_single(self, temp_project):
        """Test detecting single language version."""
        resources_dir = temp_project / "resources"
        
        (resources_dir / "en" / "skills" / "test_skill").mkdir(parents=True)
        (resources_dir / "en" / "skills" / "test_skill" / "SKILL.md").write_text(
            "---\nname: test\n---\n"
        )

        skill = Skill(temp_project, "test_skill", resources_dir)
        languages = skill.get_languages()

        assert languages == ["en"]

    def test_get_languages_empty(self, temp_project):
        """Test detecting no language versions."""
        resources_dir = temp_project / "resources"

        skill = Skill(temp_project, "nonexistent_skill", resources_dir)
        languages = skill.get_languages()

        assert languages == []


class TestSkillManagerDiscovery:
    """Tests for SkillManager skill discovery."""

    def test_discover_flow_skills(self, temp_project, multiple_flow_skills):
        """Test discovering multiple flow skills."""
        manager = SkillManager(temp_project)
        manager._discover_skills_in_resources(multiple_flow_skills, "test")

        flow_skills = manager.get_flow_skills()
        assert len(flow_skills) == 3

        skill_names = {s.name for s in flow_skills}
        assert len(skill_names) == 3

    def test_discover_standard_skill(self, temp_project, sample_standard_skill):
        """Test discovering standard skill."""
        manager = SkillManager(temp_project)
        manager._discover_skills_in_resources(sample_standard_skill, "test")

        skills = manager.list_skills()
        assert len(skills) == 1
        assert skills[0].get_type() == "standard"

    def test_discover_mixed_skills(self, temp_project, mixed_skills):
        """Test discovering mixed standard and flow skills."""
        manager = SkillManager(temp_project)
        manager._discover_skills_in_resources(mixed_skills, "test")

        all_skills = manager.list_skills()
        flow_skills = manager.get_flow_skills()

        assert len(all_skills) == 3  # 1 standard + 2 flow
        assert len(flow_skills) == 2

    def test_flow_skill_prefix_custom(self, temp_project, sample_flow_skill):
        """Test custom flow skill prefix."""
        custom_prefix = "custom_"
        manager = SkillManager(temp_project, flow_skill_prefix=custom_prefix)
        manager._discover_skills_in_resources(sample_flow_skill, "test")

        flow_skills = manager.get_flow_skills()
        assert len(flow_skills) == 1
        # Skill name is "flow_test", with prefix "custom_" it becomes "custom_flow_test"
        # But the code removes "flow_" prefix first, so it becomes "custom_test"
        assert flow_skills[0].name == "custom_test"


class TestSkillManagerDistribution:
    """Tests for SkillManager skill distribution."""

    def test_distribute_skill(self, temp_project, sample_flow_skill):
        """Test distributing a skill."""
        skill = Skill(
            root_dir=temp_project,
            skill_name="flow_test",
            resources_dir=sample_flow_skill,
        )
        skill.name = "monoco_flow_flow_test"

        target_dir = temp_project / ".agent" / "skills"

        manager = SkillManager(temp_project)
        manager.skills["monoco_flow_flow_test"] = skill

        results = manager.distribute(target_dir, lang="en")

        assert results["monoco_flow_flow_test"] is True
        assert (target_dir / "monoco_flow_flow_test" / "SKILL.md").exists()

    def test_distribute_fallback_to_en(self, temp_project):
        """Test distributing falls back to 'en' when lang not available."""
        resources_dir = temp_project / "resources"
        
        # Only create en version
        skill_dir = resources_dir / "en" / "skills" / "test_skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n")

        skill = Skill(temp_project, "test_skill", resources_dir)

        target_dir = temp_project / ".agent" / "skills"

        manager = SkillManager(temp_project)
        manager.skills["test_skill"] = skill

        # Request zh (which doesn't exist), should fallback to en
        results = manager.distribute(target_dir, lang="zh")

        assert results["test_skill"] is True
        assert (target_dir / "test_skill" / "SKILL.md").exists()

    def test_distribute_skips_up_to_date(self, temp_project, sample_flow_skill):
        """Test that distribute skips up-to-date skills."""
        skill = Skill(
            root_dir=temp_project,
            skill_name="flow_test",
            resources_dir=sample_flow_skill,
        )
        skill.name = "monoco_flow_flow_test"

        target_dir = temp_project / ".agent" / "skills"

        manager = SkillManager(temp_project)
        manager.skills["monoco_flow_flow_test"] = skill

        # First distribute
        manager.distribute(target_dir, lang="en")

        # Second distribute should skip
        results = manager.distribute(target_dir, lang="en")

        # Should still return True (success), just skip the copy
        assert results["monoco_flow_flow_test"] is True

    def test_distribute_force_overwrites(self, temp_project, sample_flow_skill):
        """Test that force=True overwrites existing skills."""
        skill = Skill(
            root_dir=temp_project,
            skill_name="flow_test",
            resources_dir=sample_flow_skill,
        )
        skill.name = "monoco_flow_flow_test"

        target_dir = temp_project / ".agent" / "skills"

        manager = SkillManager(temp_project)
        manager.skills["monoco_flow_flow_test"] = skill

        # First distribute
        manager.distribute(target_dir, lang="en")

        # Force distribute should overwrite
        results = manager.distribute(target_dir, lang="en", force=True)

        assert results["monoco_flow_flow_test"] is True


class TestSkillManagerFlowCommands:
    """Tests for flow skill command generation."""

    def test_get_flow_skill_commands(self, temp_project):
        """Test getting flow skill commands."""
        skills_data = [
            ("engineer", "engineer"),
            ("manager", "manager"),
            ("reviewer", "reviewer"),
        ]

        manager = SkillManager(temp_project)

        resources_dir = temp_project / "resources"
        for skill_name, role in skills_data:
            skill_dir = resources_dir / "en" / "skills" / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {skill_name}\ndescription: Test\ntype: flow\nrole: {role}\n---\n"
            )
            skill = Skill(
                root_dir=temp_project,
                skill_name=skill_name,
                resources_dir=resources_dir,
            )
            skill.name = skill_name
            manager.skills[skill_name] = skill

        commands = manager.get_flow_skill_commands()

        assert "/flow:engineer" in commands
        assert "/flow:manager" in commands
        assert "/flow:reviewer" in commands
        assert len(commands) == 3

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
        resources_dir = temp_project / "resources"

        # Add some skills
        for skill_name in ["skill_a", "skill_b", "skill_c"]:
            skill_dir = resources_dir / "en" / "skills" / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n")
            skill = Skill(temp_project, skill_name, resources_dir)
            manager.skills[skill_name] = skill

        skills = manager.list_skills()

        assert len(skills) == 3
        skill_names = {s.name for s in skills}
        assert skill_names == {"skill_a", "skill_b", "skill_c"}

    def test_list_skills_by_type(self, temp_project):
        """Test listing skills filtered by type."""
        manager = SkillManager(temp_project)
        resources_dir = temp_project / "resources"

        # Add standard skill
        std_dir = resources_dir / "en" / "skills" / "standard_skill"
        std_dir.mkdir(parents=True)
        (std_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\ntype: standard\n---\n"
        )
        std_skill = Skill(temp_project, "standard_skill", resources_dir)
        manager.skills["standard_skill"] = std_skill

        # Add flow skill
        flow_dir = resources_dir / "en" / "skills" / "flow_skill"
        flow_dir.mkdir(parents=True)
        (flow_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test\ntype: flow\n---\n"
        )
        flow_skill = Skill(temp_project, "flow_skill", resources_dir)
        manager.skills["flow_skill"] = flow_skill

        standard_skills = manager.list_skills_by_type("standard")
        flow_skills = manager.list_skills_by_type("flow")

        assert len(standard_skills) == 1
        assert len(flow_skills) == 1
        assert standard_skills[0].name == "standard_skill"
        assert flow_skills[0].name == "flow_skill"


class TestIntegration:
    """Integration tests for the complete multi-skill workflow."""

    def test_full_workflow_standard_and_flow(
        self, temp_project, mixed_skills
    ):
        """Test complete workflow with both standard and flow skills."""
        manager = SkillManager(temp_project)
        
        # Discover skills
        manager._discover_skills_in_resources(mixed_skills, "test")

        # Verify discovery
        assert len(manager.list_skills()) == 3
        assert len(manager.get_flow_skills()) == 2

        # Distribute
        target_dir = temp_project / ".agent" / "skills"
        results = manager.distribute(target_dir, lang="en")

        assert all(results.values())

        # Verify distribution
        assert (target_dir / "test_mixed_standard" / "SKILL.md").exists()  # Standard
        assert (target_dir / "monoco_flow_helper" / "SKILL.md").exists()  # Flow (flow_ prefix removed)
        assert (target_dir / "monoco_flow_utils" / "SKILL.md").exists()  # Flow (flow_ prefix removed)

        # Cleanup
        manager.cleanup(target_dir)

        # Verify cleanup
        assert not (target_dir / "test_mixed_standard").exists()
        assert not (target_dir / "monoco_flow_helper").exists()

    def test_full_workflow_i18n(self, temp_project):
        """Test complete workflow with i18n support."""
        resources_dir = temp_project / "resources"
        
        # Create skill with both en and zh versions
        (resources_dir / "en" / "skills" / "i18n_skill").mkdir(parents=True)
        (resources_dir / "en" / "skills" / "i18n_skill" / "SKILL.md").write_text(
            "---\nname: i18n-skill\ndescription: English version\ntype: standard\n---\n# English\n"
        )
        (resources_dir / "zh" / "skills" / "i18n_skill").mkdir(parents=True)
        (resources_dir / "zh" / "skills" / "i18n_skill" / "SKILL.md").write_text(
            "---\nname: i18n-skill\ndescription: 中文版本\ntype: standard\n---\n# 中文\n"
        )

        manager = SkillManager(temp_project)
        manager._discover_skills_in_resources(resources_dir, "test")

        # Verify both languages detected
        skill = manager.get_skill("test_i18n_skill")
        assert skill is not None
        languages = skill.get_languages()
        assert "en" in languages
        assert "zh" in languages

        # Distribute zh version
        target_dir = temp_project / ".agent" / "skills"
        results = manager.distribute(target_dir, lang="zh")
        assert results["test_i18n_skill"] is True
        assert (target_dir / "test_i18n_skill" / "SKILL.md").exists()

        # Distribute en version (should overwrite)
        results = manager.distribute(target_dir, lang="en", force=True)
        assert results["test_i18n_skill"] is True
