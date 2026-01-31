"""
Flow Skill to Antigravity Workflow Converter.

This module converts Monoco Flow Skills to Antigravity Workflow format.

Conversion Rules:
1. Frontmatter: Only keep 'description', discard other fields (name, type, role, version, author)
2. Filename: monoco_flow_engineer/SKILL.md -> flow-engineer.md
3. Content: Remove Mermaid state diagrams, convert to simple step lists
4. Output: .agent/workflows/ directory
"""

import re
from pathlib import Path
from typing import Optional, Tuple
import yaml
from rich.console import Console

console = Console()


class FlowSkillConverter:
    """Converts Flow Skill files to Antigravity Workflow format."""

    # Source directories to search for Flow Skills
    SOURCE_PATTERNS = [
        "monoco/features/agent/resources/{lang}/skills/flow_*/SKILL.md",
        "monoco/features/*/resources/{lang}/skills/flow_*/SKILL.md",
    ]

    def __init__(self, root_dir: Path):
        """
        Initialize converter with project root directory.
        
        Args:
            root_dir: Project root directory
        """
        self.root_dir = root_dir

    def _is_flow_skill(self, skill_file: Path) -> bool:
        """
        Check if a SKILL.md file is a Flow Skill by reading its frontmatter.
        
        Args:
            skill_file: Path to SKILL.md file
            
        Returns:
            True if the skill is a Flow Skill (type == "flow")
        """
        try:
            content = skill_file.read_text(encoding="utf-8")
            if not content.startswith("---"):
                return False
            
            parts = content.split("---", 2)
            if len(parts) < 3:
                return False
            
            frontmatter = yaml.safe_load(parts[1].strip()) or {}
            return frontmatter.get("type") == "flow"
        except Exception:
            return False

    def discover_flow_skills(self, lang: str = "zh") -> list[Path]:
        """
        Discover all Flow Skill files in the source directories.
        
        Flow Skills are discovered from monoco/features/*/resources/ directories,
        not from the distributed .claude/skills/ directory.
        
        Args:
            lang: Language code (default: "zh")
            
        Returns:
            List of paths to Flow Skill SKILL.md files
        """
        flow_skills = []
        seen_names = set()
        
        # Search in source directories
        features_dir = self.root_dir / "monoco" / "features"
        if features_dir.exists():
            for feature_dir in features_dir.iterdir():
                if not feature_dir.is_dir():
                    continue
                    
                resources_dir = feature_dir / "resources" / lang / "skills"
                if not resources_dir.exists():
                    continue
                
                for skill_dir in resources_dir.iterdir():
                    if not skill_dir.is_dir():
                        continue
                    
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists() and skill_dir.name not in seen_names:
                        # Check if it's a flow skill by reading frontmatter
                        if self._is_flow_skill(skill_file):
                            flow_skills.append(skill_file)
                            seen_names.add(skill_dir.name)
        
        return sorted(flow_skills)

    def convert_skill(self, skill_file: Path) -> Tuple[str, str]:
        """
        Convert a Flow Skill file to Antigravity Workflow format.
        
        Args:
            skill_file: Path to the Flow Skill SKILL.md file
            
        Returns:
            Tuple of (workflow_filename, workflow_content)
        """
        content = skill_file.read_text(encoding="utf-8")
        
        # Parse frontmatter
        frontmatter, body = self._extract_frontmatter(content)
        
        # Convert frontmatter (keep only description)
        new_frontmatter = self._convert_frontmatter(frontmatter)
        
        # Convert body content
        new_body = self._convert_body(body)
        
        # Generate workflow filename
        workflow_filename = self._generate_filename(skill_file)
        
        # Combine
        if new_frontmatter:
            workflow_content = f"---\n{new_frontmatter}---\n\n{new_body}"
        else:
            workflow_content = new_body
        
        return workflow_filename, workflow_content

    def _extract_frontmatter(self, content: str) -> Tuple[dict, str]:
        """
        Extract YAML frontmatter from markdown content.
        
        Args:
            content: Full markdown content
            
        Returns:
            Tuple of (frontmatter_dict, body_content)
        """
        if not content.startswith("---"):
            return {}, content
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content
        
        try:
            frontmatter = yaml.safe_load(parts[1].strip()) or {}
        except yaml.YAMLError:
            frontmatter = {}
        
        body = parts[2].strip()
        return frontmatter, body

    def _convert_frontmatter(self, frontmatter: dict) -> str:
        """
        Convert frontmatter to Antigravity Workflow format.
        
        Only keeps 'description' field.
        
        Args:
            frontmatter: Original frontmatter dictionary
            
        Returns:
            New frontmatter as YAML string
        """
        description = frontmatter.get("description", "")
        
        if not description:
            return ""
        
        # Create minimal frontmatter with only description
        new_frontmatter = {"description": description}
        
        return yaml.dump(new_frontmatter, allow_unicode=True, sort_keys=False)

    def _convert_body(self, body: str) -> str:
        """
        Convert body content to Antigravity Workflow format.
        
        - Remove Mermaid state diagrams
        - Keep step sections but simplify
        - Remove complex formatting
        
        Args:
            body: Original body content
            
        Returns:
            Converted body content
        """
        lines = body.split("\n")
        result_lines = []
        in_mermaid = False
        skip_section = False
        
        for line in lines:
            # Detect Mermaid code block start
            if line.strip().startswith("```mermaid"):
                in_mermaid = True
                continue
            
            # Detect Mermaid code block end
            if in_mermaid and line.strip() == "```":
                in_mermaid = False
                continue
            
            # Skip lines inside Mermaid block
            if in_mermaid:
                continue
            
            # Skip "工作流状态机" section header
            if "工作流状态机" in line or "Workflow State Machine" in line:
                skip_section = True
                continue
            
            # Detect new section (level 2 header)
            if line.strip().startswith("## ") and skip_section:
                skip_section = False
            
            if skip_section:
                continue
            
            # Keep the line
            result_lines.append(line)
        
        # Clean up excessive blank lines
        cleaned_lines = self._cleanup_blank_lines(result_lines)
        
        return "\n".join(cleaned_lines)

    def _cleanup_blank_lines(self, lines: list[str]) -> list[str]:
        """
        Clean up excessive blank lines while preserving structure.
        
        Args:
            lines: List of content lines
            
        Returns:
            Cleaned list of lines
        """
        result = []
        prev_blank = False
        
        for line in lines:
            is_blank = not line.strip()
            
            # Skip consecutive blank lines
            if is_blank and prev_blank:
                continue
            
            result.append(line)
            prev_blank = is_blank
        
        # Remove trailing blank lines
        while result and not result[-1].strip():
            result.pop()
        
        return result

    def _generate_filename(self, skill_file: Path) -> str:
        """
        Generate workflow filename from skill file path.
        
        Conversion: flow_engineer/SKILL.md -> flow-engineer.md
        
        Args:
            skill_file: Path to the Flow Skill SKILL.md file
            
        Returns:
            Workflow filename
        """
        # Get parent directory name (e.g., "flow_engineer")
        skill_dir_name = skill_file.parent.name
        
        # Remove "flow_" prefix
        if skill_dir_name.startswith("flow_"):
            role_name = skill_dir_name[len("flow_"):]
        else:
            role_name = skill_dir_name
        
        # Convert to workflow filename
        workflow_filename = f"flow-{role_name}.md"
        
        return workflow_filename


class WorkflowDistributor:
    """Distributes converted workflows to target directory."""

    def __init__(self, root_dir: Path):
        """
        Initialize distributor.
        
        Args:
            root_dir: Project root directory
        """
        self.root_dir = root_dir
        self.converter = FlowSkillConverter(root_dir)

    def distribute(self, force: bool = False, lang: str = "zh") -> dict[str, bool]:
        """
        Convert and distribute all Flow Skills to .agent/workflows/.
        
        Args:
            force: Overwrite existing files even if unchanged
            lang: Language code for Flow Skills (default: "zh")
            
        Returns:
            Dictionary mapping workflow filenames to success status
        """
        results = {}
        
        # Discover flow skills
        flow_skills = self.converter.discover_flow_skills(lang=lang)
        
        if not flow_skills:
            console.print("[yellow]No Flow Skills found to convert[/yellow]")
            return results
        
        # Target directory
        workflows_dir = self.root_dir / ".agent" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        console.print(f"[dim]Found {len(flow_skills)} Flow Skills to convert[/dim]")
        
        for skill_file in flow_skills:
            try:
                workflow_filename, workflow_content = self.converter.convert_skill(skill_file)
                target_file = workflows_dir / workflow_filename
                
                # Check if update is needed
                if target_file.exists() and not force:
                    existing_content = target_file.read_text(encoding="utf-8")
                    if existing_content == workflow_content:
                        console.print(f"[dim]  = {workflow_filename} is up to date[/dim]")
                        results[workflow_filename] = True
                        continue
                
                # Write workflow file
                target_file.write_text(workflow_content, encoding="utf-8")
                console.print(f"[green]  ✓ Created {workflow_filename}[/green]")
                results[workflow_filename] = True
                
            except Exception as e:
                console.print(f"[red]  ✗ Failed to convert {skill_file.name}: {e}[/red]")
                results[skill_file.name] = False
        
        return results

    def cleanup(self, lang: str = "zh") -> int:
        """
        Remove all distributed workflows from .agent/workflows/.
        
        Args:
            lang: Language code for Flow Skills (default: "zh")
            
        Returns:
            Number of files removed
        """
        workflows_dir = self.root_dir / ".agent" / "workflows"
        
        if not workflows_dir.exists():
            return 0
        
        removed_count = 0
        
        # Discover flow skills to know which files to remove
        flow_skills = self.converter.discover_flow_skills(lang=lang)
        workflow_filenames = set()
        
        for skill_file in flow_skills:
            workflow_filename = self.converter._generate_filename(skill_file)
            workflow_filenames.add(workflow_filename)
        
        # Remove workflow files
        for workflow_file in workflows_dir.glob("flow-*.md"):
            if workflow_file.name in workflow_filenames:
                workflow_file.unlink()
                console.print(f"[green]  ✓ Removed {workflow_file.name}[/green]")
                removed_count += 1
        
        # Remove empty directory
        if workflows_dir.exists() and not any(workflows_dir.iterdir()):
            workflows_dir.rmdir()
            console.print(f"[dim]  Removed empty directory: {workflows_dir}[/dim]")
        
        if removed_count == 0:
            console.print(f"[dim]No workflows to remove from {workflows_dir}[/dim]")
        
        return removed_count


def convert_flow_skill_to_workflow(skill_content: str) -> str:
    """
    Convert Flow Skill content to Antigravity Workflow format.
    
    This is a standalone utility function for direct content conversion.
    
    Args:
        skill_content: Original Flow Skill markdown content
        
    Returns:
        Converted Workflow markdown content
    """
    converter = FlowSkillConverter(Path("."))
    
    frontmatter, body = converter._extract_frontmatter(skill_content)
    new_frontmatter = converter._convert_frontmatter(frontmatter)
    new_body = converter._convert_body(body)
    
    if new_frontmatter:
        return f"---\n{new_frontmatter}---\n\n{new_body}"
    else:
        return new_body
