"""
Universal Hooks: Front Matter Parser

Parses YAML Front Matter from hook scripts with support for multiple
comment styles and languages.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .universal_models import HookMetadata, ParsedHook


@dataclass
class ParseError:
    """Error information from parsing a hook script."""

    path: Path
    line_number: int
    message: str
    raw_content: Optional[str] = None


class HookParser:
    """
    Parser for extracting YAML Front Matter from hook scripts.

    Supports multiple comment styles:
    - Shell/Python/Ruby: `# ---` / `# ---`
    - JavaScript/TypeScript/C/C++/Java/Rust/Go: `// ---` / `// ---`
    - Lua/SQL/Haskell: `-- ---` / `-- ---`
    - HTML/XML: `<!-- ---` / `--- -->`

    The parser detects the comment style automatically based on file extension
    or the first line of the script.
    """

    # Comment style definitions: (prefix, suffix, file_extensions)
    COMMENT_STYLES = {
        "shell": ("#", "", {"sh", "bash", "zsh", "fish", "py", "rb", "pl", "r", "ps1", "Makefile", "Dockerfile"}),
        "c_style": ("//", "", {"js", "ts", "jsx", "tsx", "c", "cpp", "cc", "cxx", "h", "hpp", "java", "cs", "go", "rs", "swift", "kt", "scala", "php", "dart"}),
        "double_dash": ("--", "", {"lua", "sql", "hs", "lhs", "elm", "sql", "mysql", "pgsql"}),
        "html": ("<!--", "-->", {"html", "htm", "xml", "svg", "vue", "svelte"}),
    }

    # Regex patterns for front matter detection
    FRONT_MATTER_DELIMITER = "---"

    def __init__(self):
        """Initialize the parser."""
        self.errors: list[ParseError] = []

    def _detect_comment_style(self, path: Path, first_line: str) -> tuple[str, str]:
        """
        Detect the comment style for a file.

        Args:
            path: Path to the script file
            first_line: First line of the file content

        Returns:
            Tuple of (prefix, suffix) for the comment style
        """
        # First, try to detect from file extension
        ext = path.suffix.lstrip(".").lower()
        name = path.name.lower()

        for style_name, (prefix, suffix, extensions) in self.COMMENT_STYLES.items():
            if ext in extensions or name in extensions:
                return (prefix, suffix)

        # If no extension match, try to detect from shebang or first line
        if first_line.startswith("#!/"):
            # Detect from shebang
            shebang = first_line.lower()
            if any(shell in shebang for shell in ["bash", "sh", "zsh", "python", "ruby", "perl"]):
                return ("#", "")
            if "node" in shebang or "deno" in shebang or "bun" in shebang:
                return ("//", "")
            if "lua" in shebang:
                return ("--", "")

        # Default to shell style if uncertain
        return ("#", "")

    def _strip_comment_prefix(self, line: str, prefix: str, suffix: str) -> str:
        """
        Remove comment prefix and suffix from a line.

        Args:
            line: The line to process
            prefix: The comment prefix (e.g., "#", "//", "--")
            suffix: The comment suffix (e.g., "-->")

        Returns:
            The line with comment markers stripped
        """
        # Remove leading/trailing whitespace first
        stripped = line.strip()

        # Remove prefix
        if prefix and stripped.startswith(prefix):
            stripped = stripped[len(prefix):]

        # Remove suffix
        if suffix and stripped.endswith(suffix):
            stripped = stripped[:-len(suffix)]

        return stripped.strip()

    def _extract_front_matter_lines(
        self,
        lines: list[str],
        prefix: str,
        suffix: str,
    ) -> Optional[tuple[list[str], int, int]]:
        """
        Extract front matter lines from script content.

        Args:
            lines: All lines of the script
            prefix: Comment prefix
            suffix: Comment suffix

        Returns:
            Tuple of (front_matter_lines, start_line, end_line) or None if no front matter
        """
        if not lines:
            return None

        start_idx = 0

        # Skip shebang line if present
        if lines[0].startswith("#!/"):
            start_idx = 1

        # Look for opening delimiter
        opening_line_idx = None
        for i in range(start_idx, len(lines)):
            stripped = self._strip_comment_prefix(lines[i], prefix, suffix)
            if stripped == self.FRONT_MATTER_DELIMITER:
                opening_line_idx = i
                break

        if opening_line_idx is None:
            return None

        # Look for closing delimiter
        closing_line_idx = None
        for i in range(opening_line_idx + 1, len(lines)):
            stripped = self._strip_comment_prefix(lines[i], prefix, suffix)
            if stripped == self.FRONT_MATTER_DELIMITER:
                closing_line_idx = i
                break

        if closing_line_idx is None:
            return None

        # Extract front matter lines (between delimiters)
        front_matter_lines = []
        for i in range(opening_line_idx + 1, closing_line_idx):
            stripped = self._strip_comment_prefix(lines[i], prefix, suffix)
            front_matter_lines.append(stripped)

        # Line numbers are 1-based for error reporting
        return (
            front_matter_lines,
            opening_line_idx + 1,
            closing_line_idx + 1,
        )

    def parse_file(self, path: Path) -> Optional[ParsedHook]:
        """
        Parse a hook script file and extract its metadata.

        Args:
            path: Path to the hook script

        Returns:
            ParsedHook if successful, None if parsing fails
        """
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            self.errors.append(ParseError(
                path=path,
                line_number=0,
                message=f"Failed to read file: {e}",
            ))
            return None

        return self.parse_content(path, content)

    def parse_content(self, path: Path, content: str) -> Optional[ParsedHook]:
        """
        Parse hook content and extract metadata.

        Args:
            path: Path to the hook script (for error reporting and style detection)
            content: The script content

        Returns:
            ParsedHook if successful, None if no valid front matter or parsing fails
        """
        lines = content.splitlines()

        if not lines:
            self.errors.append(ParseError(
                path=path,
                line_number=0,
                message="Empty file",
            ))
            return None

        # Detect comment style
        first_line = lines[0] if lines else ""
        prefix, suffix = self._detect_comment_style(path, first_line)

        # Extract front matter
        result = self._extract_front_matter_lines(lines, prefix, suffix)
        if result is None:
            # No front matter found - this is OK, just return None
            return None

        front_matter_lines, start_line, end_line = result
        yaml_content = "\n".join(front_matter_lines)

        # Parse YAML
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            # Try to extract line number from error
            line_no = getattr(e, 'problem_mark', None)
            if line_no:
                actual_line = start_line + line_no.line + 1
            else:
                actual_line = start_line

            self.errors.append(ParseError(
                path=path,
                line_number=actual_line,
                message=f"YAML parsing error: {e}",
                raw_content=yaml_content,
            ))
            return None

        if not isinstance(data, dict):
            self.errors.append(ParseError(
                path=path,
                line_number=start_line,
                message="Front matter must be a YAML mapping (key: value)",
                raw_content=yaml_content,
            ))
            return None

        # Parse metadata using Pydantic
        try:
            metadata = HookMetadata.model_validate(data)
        except Exception as e:
            self.errors.append(ParseError(
                path=path,
                line_number=start_line,
                message=f"Metadata validation error: {e}",
                raw_content=yaml_content,
            ))
            return None

        return ParsedHook(
            metadata=metadata,
            script_path=path,
            content=content,
            front_matter_start_line=start_line,
            front_matter_end_line=end_line,
        )

    def parse_directory(
        self,
        directory: Path,
        pattern: str = "*",
    ) -> list[ParsedHook]:
        """
        Parse all hook scripts in a directory.

        Args:
            directory: Directory to scan
            pattern: Glob pattern for matching files (default: "*")

        Returns:
            List of successfully parsed hooks
        """
        parsed_hooks: list[ParsedHook] = []

        if not directory.exists():
            return parsed_hooks

        for file_path in directory.rglob(pattern):
            if not file_path.is_file():
                continue

            # Skip hidden files and common non-script files
            if file_path.name.startswith("."):
                continue
            if file_path.suffix.lower() in {".md",".txt",".json",".lock"}:
                continue

            hook = self.parse_file(file_path)
            if hook is not None:
                parsed_hooks.append(hook)

        return parsed_hooks

    def get_errors(self) -> list[ParseError]:
        """Get all parsing errors encountered."""
        return self.errors.copy()

    def clear_errors(self) -> None:
        """Clear the error list."""
        self.errors.clear()
