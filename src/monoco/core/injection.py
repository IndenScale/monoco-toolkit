import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


class PromptInjector:
    """
    Engine for injecting managed content into AGENTS.md using mdp (md-patch) CLI tool.
    Maintains a 'Managed Section' under the '## Monoco' heading.
    """

    MANAGED_HEADER = "## Monoco"

    # Backward compatibility: still recognize old markers for migration
    MANAGED_START = "<!-- MONOCO_GENERATED_START -->"
    MANAGED_END = "<!-- MONOCO_GENERATED_END -->"

    FILE_HEADER_COMMENT = """<!--
⚠️ IMPORTANT: This file is partially managed by Monoco.
- Content under the '## Monoco' section is auto-generated.
- Use `monoco sync` to refresh this content.
- Do NOT manually edit the managed section.
-->

"""

    def __init__(self, target_file: Path, verbose: bool = True):
        self.target_file = target_file
        self.verbose = verbose
        self._mdp_path = self._find_mdp()

    def _find_mdp(self) -> str:
        """Find mdp CLI executable."""
        candidates = [
            "mdp",
            str(Path.home() / ".local" / "bin" / "mdp"),
            str(Path.home() / ".cargo" / "bin" / "mdp"),
        ]
        for candidate in candidates:
            try:
                result = subprocess.run(
                    [candidate, "--version"],
                    capture_output=True,
                    check=False,
                )
                if result.returncode == 0:
                    return candidate
            except FileNotFoundError:
                continue
        raise RuntimeError(
            "mdp (md-patch) CLI not found. Please install it from https://github.com/tzmfreedom/md-patch"
        )

    def _run_mdp(
        self,
        args: List[str],
        check: bool = True,
        capture: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run mdp CLI with given arguments."""
        cmd = [self._mdp_path] + args
        if self.verbose:
            print(f"  Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            check=False,
        )

        if check and result.returncode != 0:
            if result.returncode == 2:
                raise MdpHeadingNotFoundError(
                    f"Heading not found in {self.target_file}: {result.stderr}"
                )
            elif result.returncode == 3:
                raise MdpFingerprintError(
                    f"Fingerprint mismatch in {self.target_file}: {result.stderr}"
                )
            else:
                raise MdpError(
                    f"mdp failed with code {result.returncode}: {result.stderr}"
                )

        return result

    def _generate_content(self, prompts: Dict[str, str]) -> str:
        """Generate the content to inject (as a single section, no sub-headings)."""
        lines = ["> **Auto-Generated**: This section is managed by Monoco. Do not edit manually."]

        for title, content in prompts.items():
            lines.append("")
            # Use bold instead of heading to avoid creating new sections
            lines.append(f"**{title}**")
            lines.append("")

            # Sanitize content
            clean_content = content.strip()
            # Remove leading header if it matches the title
            pattern = r"^(#+\s*)" + re.escape(title) + r"\s*\n"
            match = re.match(pattern, clean_content, re.IGNORECASE)
            if match:
                clean_content = clean_content[match.end() :].strip()

            # Demote any headers in content to bold (to avoid creating sections)
            clean_content = self._demote_headers_to_bold(clean_content)
            lines.append(clean_content)

        return "\n".join(lines)

    def _demote_headers_to_bold(self, content: str) -> str:
        """Convert headers to bold text to avoid creating sections."""
        result_lines = []
        for line in content.splitlines():
            if line.strip().startswith("#"):
                # Convert header to bold
                match = re.match(r"^(#+)\s*(.+)$", line.strip())
                if match:
                    hashes, text = match.groups()
                    level = len(hashes)
                    # Use multiple levels of bold for visual hierarchy
                    if level == 1:
                        result_lines.append(f"**{text}**")
                    elif level == 2:
                        result_lines.append(f"**{text}**")
                    else:
                        result_lines.append(f"*{text}*")
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)
        return "\n".join(result_lines)

    def _demote_headers(self, content: str) -> str:
        """Demote headers in content to start at level 4 (####)."""
        header_lines = [
            line for line in content.splitlines() if line.lstrip().startswith("#")
        ]
        min_level = 99
        for line in header_lines:
            match = re.match(r"^(#+)\s", line.lstrip())
            if match:
                min_level = min(min_level, len(match.group(1)))

        if min_level == 99:
            return content

        shift = 4 - min_level
        result_lines = []
        for line in content.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                match = re.match(r"^(#+)(.*)", stripped)
                if match:
                    hashes, rest = match.groups()
                    new_level = max(1, len(hashes) + shift)
                    result_lines.append("#" * new_level + rest)
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)

        return "\n".join(result_lines)

    def _ensure_file_and_heading(self) -> bool:
        """Ensure target file exists and has the managed heading."""
        created = False

        if not self.target_file.exists():
            root_heading = f"# {self.target_file.stem}"
            self.target_file.parent.mkdir(parents=True, exist_ok=True)
            self.target_file.write_text(
                self.FILE_HEADER_COMMENT
                + f"{root_heading}\n\n{self.MANAGED_HEADER}\n\n<!-- placeholder -->\n",
                encoding="utf-8",
            )
            created = True
            if self.verbose:
                print(f"  Created new file: {self.target_file}")
        else:
            content = self.target_file.read_text(encoding="utf-8")

            # If file is empty, treat it as new file
            if not content.strip():
                root_heading = f"# {self.target_file.stem}"
                self.target_file.write_text(
                    self.FILE_HEADER_COMMENT
                    + f"{root_heading}\n\n{self.MANAGED_HEADER}\n\n<!-- placeholder -->\n",
                    encoding="utf-8",
                )
                if self.verbose:
                    print(f"  Initialized empty file: {self.target_file}")
                return True

            if self.MANAGED_START in content or self.MANAGED_END in content:
                content = self._migrate_from_markers(content)
                self.target_file.write_text(content, encoding="utf-8")
                if self.verbose:
                    print(f"  Migrated old HTML markers in {self.target_file}")

            # Check if file has any heading
            has_heading = re.search(r"^#\s+.+$", content, re.MULTILINE)
            if not has_heading:
                # Add root heading if none exists
                root_heading = f"# {self.target_file.stem}"
                if not content.endswith("\n"):
                    content += "\n"
                content = f"{root_heading}\n\n{content}"
                self.target_file.write_text(content, encoding="utf-8")

            heading_pattern = re.compile(
                rf"^{re.escape(self.MANAGED_HEADER)}\s*$", re.MULTILINE
            )
            if not heading_pattern.search(content):
                if not content.endswith("\n"):
                    content += "\n"
                content += f"\n{self.MANAGED_HEADER}\n\n<!-- placeholder -->\n"
                self.target_file.write_text(content, encoding="utf-8")
                if self.verbose:
                    print(f"  Added {self.MANAGED_HEADER} heading to {self.target_file}")

        return created

    def _migrate_from_markers(self, content: str) -> str:
        """Migrate content from old HTML marker format to heading-based format."""
        lines = content.splitlines()
        result = []
        in_managed_block = False

        for line in lines:
            if self.MANAGED_START in line:
                in_managed_block = True
                continue
            if self.MANAGED_END in line:
                in_managed_block = False
                continue
            if in_managed_block:
                result.append(line)
            else:
                result.append(line)

        while result and not result[-1].strip():
            result.pop()

        content = "\n".join(result)

        heading_pattern = re.compile(
            rf"^{re.escape(self.MANAGED_HEADER)}\s*$", re.MULTILINE
        )
        if not heading_pattern.search(content):
            content += f"\n\n{self.MANAGED_HEADER}\n\n<!-- placeholder -->\n"

        return content + "\n"

    def _detect_root_heading(self, content: str) -> str:
        """Detect the root heading (e.g., '# AGENTS.md')."""
        match = re.search(r"^(# .+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "# " + self.target_file.stem

    def inject(self, prompts: Dict[str, str]) -> bool:
        """
        Injects the provided prompts into the target file using mdp CLI.

        Args:
            prompts: A dictionary where key is the section title and value is the content.

        Returns:
            True if changes were written, False otherwise.
        """
        # Ensure file and heading exist
        self._ensure_file_and_heading()

        # Detect root heading
        content = self.target_file.read_text(encoding="utf-8")
        root_heading = self._detect_root_heading(content)
        
        # Build heading path
        heading_path = [root_heading, self.MANAGED_HEADER]

        # Generate content
        new_content = self._generate_content(prompts)

        # Use mdp replace to update the section
        result = self._run_mdp(
            [
                "patch",
                "-f",
                str(self.target_file),
                "-H",
                " ".join(heading_path),
                "--op",
                "replace",
                "-c",
                new_content,
                "--force",
            ],
            check=False,
        )

        if result.returncode != 0:
            raise MdpError(f"Failed to inject content: {result.stderr}")

        return True

    def remove(self) -> bool:
        """Removes the managed section from the target file using mdp CLI."""
        if not self.target_file.exists():
            return False

        content = self.target_file.read_text(encoding="utf-8")

        heading_pattern = re.compile(
            rf"^{re.escape(self.MANAGED_HEADER)}\s*$", re.MULTILINE
        )
        if not heading_pattern.search(content):
            if self.MANAGED_START in content:
                return self._legacy_remove()
            return False

        root_heading = self._detect_root_heading(content)
        heading_path = [root_heading, self.MANAGED_HEADER]

        result = self._run_mdp(
            [
                "patch",
                "-f",
                str(self.target_file),
                "-H",
                " ".join(heading_path),
                "--op",
                "delete",
                "--force",
            ],
            check=False,
        )

        return result.returncode == 0

    def _legacy_remove(self) -> bool:
        """Remove content using old marker-based logic."""
        content = self.target_file.read_text(encoding="utf-8")

        if self.MANAGED_START not in content:
            return False

        lines = content.splitlines()
        result = []
        in_block = False

        for line in lines:
            if self.MANAGED_START in line:
                in_block = True
                continue
            if self.MANAGED_END in line:
                in_block = False
                continue
            if not in_block:
                result.append(line)

        new_content = "\n".join(result).strip() + "\n"
        if new_content != content:
            self.target_file.write_text(new_content, encoding="utf-8")
            return True
        return False


class MdpError(Exception):
    """Base exception for mdp-related errors."""
    pass


class MdpHeadingNotFoundError(MdpError):
    """Raised when the target heading is not found."""
    pass


class MdpFingerprintError(MdpError):
    """Raised when fingerprint validation fails."""
    pass
