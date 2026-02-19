"""
Agenthooks Parser: HOOK.md Configuration Parser

Parses agenthooks standard HOOK.md files with YAML frontmatter.
Compatible with agenthooks open standard specification.

See: https://github.com/IndenScale/agenthooks/blob/main/docs/en/SPECIFICATION.md
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

import yaml

from .models import (
    HookMetadata,
    HookType,
    ParsedHook,
    normalize_agent_event,
)


@dataclass
class AgenthooksMatcher:
    """
    Agenthooks matcher configuration.

    Filters hook trigger conditions for tool-related events.
    """

    tool: Optional[str] = None
    pattern: Optional[str] = None

    def matches(self, tool_name: Optional[str] = None, tool_input: Optional[dict] = None) -> bool:
        """
        Check if the given tool/input matches this matcher.

        Args:
            tool_name: The name of the tool being called
            tool_input: The input parameters for the tool

        Returns:
            True if matches (or if no matcher criteria specified)
        """
        import re

        # If neither tool nor pattern specified, always matches
        if self.tool is None and self.pattern is None:
            return True

        # Check tool name match
        if self.tool is not None and tool_name is not None:
            if not re.search(self.tool, tool_name):
                return False

        # Check pattern match in tool input
        if self.pattern is not None and tool_input is not None:
            # Convert tool_input to string for pattern matching
            input_str = str(tool_input)
            if not re.search(self.pattern, input_str):
                return False

        return True


@dataclass
class AgenthooksConfig:
    """
    Agenthooks configuration from HOOK.md frontmatter.

    This represents the full agenthooks standard configuration.
    """

    name: str
    description: str
    trigger: str
    matcher: Optional[AgenthooksMatcher] = None
    timeout: int = 30000  # milliseconds
    async_mode: bool = False
    priority: int = 100
    metadata: dict[str, Any] = field(default_factory=dict)

    # Script entry point (default: scripts/run.sh)
    script_entry: str = "scripts/run.sh"

    def to_hook_metadata(self) -> HookMetadata:
        """
        Convert agenthooks config to monoco HookMetadata.

        Returns:
            HookMetadata compatible with monoco system
        """
        # Normalize event name
        event = normalize_agent_event(self.trigger)

        # Convert matcher to monoco format (list of patterns)
        matcher: Optional[list[str]] = None
        if self.matcher:
            # Store matcher info in extra for later use
            matcher_patterns = []
            if self.matcher.tool:
                matcher_patterns.append(f"tool:{self.matcher.tool}")
            if self.matcher.pattern:
                matcher_patterns.append(f"pattern:{self.matcher.pattern}")
            if matcher_patterns:
                matcher = matcher_patterns

        return HookMetadata(
            type=HookType.AGENT,
            event=event,
            matcher=matcher,
            priority=self.priority,
            description=self.description,
            provider="agenthooks",  # Agenthooks hooks are provider-agnostic
            extra={
                "agenthooks_name": self.name,
                "agenthooks_timeout": self.timeout,
                "agenthooks_async": self.async_mode,
                "agenthooks_script_entry": self.script_entry,
                "agenthooks_matcher": {
                    "tool": self.matcher.tool if self.matcher else None,
                    "pattern": self.matcher.pattern if self.matcher else None,
                },
                **self.metadata,
            },
        )


class AgenthooksParser:
    """
    Parser for agenthooks HOOK.md files.

    Supports the agenthooks open standard format with YAML frontmatter.
    """

    def __init__(self):
        """Initialize the parser."""
        self.errors: list[str] = []

    def parse_hook_md(self, path: Path) -> Optional[AgenthooksConfig]:
        """
        Parse a HOOK.md file and extract configuration.

        Args:
            path: Path to the HOOK.md file

        Returns:
            AgenthooksConfig if successful, None if parsing fails
        """
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            self.errors.append(f"Failed to read {path}: {e}")
            return None

        return self.parse_hook_md_content(path, content)

    def parse_hook_md_content(
        self, path: Path, content: str
    ) -> Optional[AgenthooksConfig]:
        """
        Parse HOOK.md content.

        Args:
            path: Path to the file (for error reporting)
            content: The file content

        Returns:
            AgenthooksConfig if successful, None if parsing fails
        """
        # Extract YAML frontmatter
        frontmatter = self._extract_frontmatter(content)
        if frontmatter is None:
            self.errors.append(f"No valid YAML frontmatter found in {path}")
            return None

        # Parse YAML
        try:
            data = yaml.safe_load(frontmatter)
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parsing error in {path}: {e}")
            return None

        if not isinstance(data, dict):
            self.errors.append(f"Frontmatter must be a YAML mapping in {path}")
            return None

        # Build AgenthooksConfig
        return self._build_config(path, data)

    def _extract_frontmatter(self, content: str) -> Optional[str]:
        """
        Extract YAML frontmatter from markdown content.

        Args:
            content: The markdown content

        Returns:
            YAML frontmatter string or None if not found
        """
        lines = content.splitlines()

        # Look for opening ---
        start_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "---":
                start_idx = i
                break

        if start_idx is None:
            return None

        # Look for closing ---
        end_idx = None
        for i in range(start_idx + 1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx is None:
            return None

        # Extract frontmatter lines
        frontmatter_lines = lines[start_idx + 1 : end_idx]
        return "\n".join(frontmatter_lines)

    def _build_config(
        self, path: Path, data: dict[str, Any]
    ) -> Optional[AgenthooksConfig]:
        """
        Build AgenthooksConfig from parsed YAML data.

        Args:
            path: Path to the file
            data: Parsed YAML data

        Returns:
            AgenthooksConfig or None if invalid
        """
        # Required fields
        name = data.get("name")
        if not name:
            self.errors.append(f"Missing required field 'name' in {path}")
            return None

        description = data.get("description", "")
        trigger = data.get("trigger")
        if not trigger:
            self.errors.append(f"Missing required field 'trigger' in {path}")
            return None

        # Parse matcher
        matcher_data = data.get("matcher")
        matcher: Optional[AgenthooksMatcher] = None
        if matcher_data and isinstance(matcher_data, dict):
            matcher = AgenthooksMatcher(
                tool=matcher_data.get("tool"),
                pattern=matcher_data.get("pattern"),
            )

        # Parse other fields
        timeout = data.get("timeout", 30000)
        async_mode = data.get("async", False)
        priority = data.get("priority", 100)
        script_entry = data.get("script_entry", "scripts/run.sh")

        # Extract additional metadata (non-standard fields)
        known_fields = {
            "name", "description", "trigger", "matcher",
            "timeout", "async", "priority", "script_entry",
        }
        metadata = {k: v for k, v in data.items() if k not in known_fields}

        return AgenthooksConfig(
            name=name,
            description=description,
            trigger=trigger,
            matcher=matcher,
            timeout=timeout,
            async_mode=async_mode,
            priority=priority,
            metadata=metadata,
            script_entry=script_entry,
        )

    def discover_hooks(self, directory: Path) -> list[AgenthooksConfig]:
        """
        Discover all agenthooks in a directory.

        Each subdirectory should contain a HOOK.md file.

        Args:
            directory: Directory to scan (e.g., ~/.config/agents/hooks/)

        Returns:
            List of successfully parsed AgenthooksConfig
        """
        configs: list[AgenthooksConfig] = []

        if not directory.exists() or not directory.is_dir():
            return configs

        # Look for subdirectories containing HOOK.md
        for item in directory.iterdir():
            if item.is_dir():
                hook_md = item / "HOOK.md"
                if hook_md.exists():
                    config = self.parse_hook_md(hook_md)
                    if config:
                        # Store the hook directory path
                        config.metadata["_hook_dir"] = str(item)
                        configs.append(config)

        # Sort by priority (higher = first, per agenthooks spec)
        configs.sort(key=lambda c: c.priority, reverse=True)

        return configs

    def get_errors(self) -> list[str]:
        """Get all parsing errors."""
        return self.errors.copy()

    def clear_errors(self) -> None:
        """Clear the error list."""
        self.errors.clear()


def convert_agenthooks_to_parsed_hook(
    config: AgenthooksConfig, hook_dir: Path
) -> Optional[ParsedHook]:
    """
    Convert AgenthooksConfig to monoco ParsedHook.

    Args:
        config: The agenthooks configuration
        hook_dir: The directory containing the hook

    Returns:
        ParsedHook if the script exists, None otherwise
    """
    script_path = hook_dir / config.script_entry

    if not script_path.exists():
        return None

    try:
        content = script_path.read_text(encoding="utf-8")
    except Exception:
        return None

    metadata = config.to_hook_metadata()

    return ParsedHook(
        metadata=metadata,
        script_path=script_path,
        content=content,
        front_matter_start_line=0,
        front_matter_end_line=0,
    )
