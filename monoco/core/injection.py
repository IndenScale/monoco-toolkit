import re
from pathlib import Path
from typing import Dict, Optional


class PromptInjector:
    """
    Engine for injecting managed content into Markdown-like files (e.g., .cursorrules, GEMINI.md).
    Maintains a 'Managed Block' defined by a specific header.
    """

    MANAGED_HEADER = "## Monoco Toolkit"
    MANAGED_START = "<!-- MONOCO_GENERATED_START -->"
    MANAGED_END = "<!-- MONOCO_GENERATED_END -->"

    FILE_HEADER_COMMENT = """<!--
⚠️ IMPORTANT: This file is partially managed by Monoco.
- Content between MONOCO_GENERATED_START and MONOCO_GENERATED_END is auto-generated.
- Use `monoco sync` to refresh this content.
- Do NOT manually edit the managed block.
- Do NOT add content after MONOCO_GENERATED_END (use separate files instead).
-->

"""

    def __init__(self, target_file: Path, verbose: bool = True):
        self.target_file = target_file
        self.verbose = verbose

    def _detect_external_content(self, content: str) -> Optional[str]:
        """
        Detects content outside the managed block.

        Returns:
            The external content string if found, None otherwise.
        """
        if not content or self.MANAGED_END not in content:
            return None

        # Split by MANAGED_END and check if there's non-empty content after
        parts = content.split(self.MANAGED_END)
        if len(parts) < 2:
            return None

        post_content = parts[-1].strip()
        # Check if there's meaningful content (not just whitespace or newlines)
        if post_content and len(post_content) > 10:  # Threshold to avoid false positives
            return post_content
        return None

    def _warn_external_content(self, external_content: str):
        """Outputs warning about external content."""
        if not self.verbose:
            return

        # Truncate long content for warning message
        preview = external_content[:200].replace("\n", " ")
        if len(external_content) > 200:
            preview += "..."

        print(f"⚠️  Warning: Manual content detected after Managed Block in {self.target_file}")
        print(f"   Consider moving to a separate file. Found content starting with: {preview}")

    def inject(self, prompts: Dict[str, str]) -> bool:
        """
        Injects the provided prompts into the target file.

        Args:
            prompts: A dictionary where key is the section title and value is the content.

        Returns:
            True if changes were written, False otherwise.
        """
        current_content = ""
        if self.target_file.exists():
            current_content = self.target_file.read_text(encoding="utf-8")

        # Check for external content and warn
        external_content = self._detect_external_content(current_content)
        if external_content:
            self._warn_external_content(external_content)

        new_content = self._merge_content(current_content, prompts)

        if new_content != current_content:
            self.target_file.write_text(new_content, encoding="utf-8")
            return True
        return False

    def _merge_content(self, original: str, prompts: Dict[str, str]) -> str:
        """
        Merges the generated prompts into the original content within the managed block.
        """
        # 1. Generate the new managed block content
        managed_block = [self.MANAGED_HEADER, ""]
        managed_block.append(
            "> **Auto-Generated**: This section is managed by Monoco. Do not edit manually.\n"
        )

        for title, content in prompts.items():
            managed_block.append(f"### {title}")
            managed_block.append("")  # Blank line after header

            # Sanitize content: remove leading header if it matches the title
            clean_content = content.strip()
            # Regex to match optional leading hash header matching the title (case insensitive)
            pattern = r"^(#+\s*)" + re.escape(title) + r"\s*\n"
            match = re.match(pattern, clean_content, re.IGNORECASE)

            if match:
                clean_content = clean_content[match.end() :].strip()
            
            # Demote headers in content to be below ### (so start at ####)
            # Find the minimum header level in the source content to calculate shift
            header_lines = [line for line in clean_content.splitlines() if line.lstrip().startswith("#")]
            min_level = 99
            for line in header_lines:
                match = re.match(r"^(#+)\s", line.lstrip())
                if match:
                    min_level = min(min_level, len(match.group(1)))
            
            if min_level == 99:
                # No headers found, just use splitlines
                demoted_content = clean_content.splitlines()
            else:
                # Shift so that min_level maps to level 4
                shift = 4 - min_level
                demoted_content = []
                for line in clean_content.splitlines():
                    stripped_line = line.lstrip()
                    if stripped_line.startswith("#"):
                        # Use regex to separate hashes from the rest of the line
                        match = re.match(r"^(#+)(.*)", stripped_line)
                        if match:
                            hashes, rest = match.groups()
                            # Apply shift, ensuring minimum level is 1
                            new_level = max(1, len(hashes) + shift)
                            demoted_content.append("#" * new_level + rest)
                        else:
                            demoted_content.append(line)
                    else:
                        demoted_content.append(line)
            
            managed_block.append("\n".join(demoted_content))
            managed_block.append("")  # Blank line after section

        managed_block_str = "\n".join(managed_block).strip() + "\n"
        managed_block_str = f"{self.MANAGED_START}\n{managed_block_str}\n{self.MANAGED_END}\n"

        # 2. Add file header comment if not present
        has_header = original.strip().startswith("<!--") and "IMPORTANT: This file is partially managed by Monoco" in original

        # 2. Find and replace/append in the original content
        # Check for delimiters first
        if self.MANAGED_START in original and self.MANAGED_END in original:
            try:
                pre = original.split(self.MANAGED_START)[0]
                post = original.split(self.MANAGED_END)[1]
                # Add header comment if not present
                if not has_header and not pre.strip().startswith("<!--"):
                    pre = self.FILE_HEADER_COMMENT + pre
                # Reconstruct
                return pre + managed_block_str.strip() + post
            except IndexError:
                # Fallback to header detection if delimiters malformed
                pass

        lines = original.splitlines()
        start_idx = -1
        end_idx = -1

        # Find start
        for i, line in enumerate(lines):
            if line.strip() == self.MANAGED_HEADER:
                start_idx = i
                break
        
        if start_idx == -1:
             # Check if we have delimiters even if header is missing/changed?
             # Handled above.
             pass

        if start_idx == -1:
            # Block not found, append to end
            result = ""
            if not has_header:
                result = self.FILE_HEADER_COMMENT
            if original and not original.endswith("\n"):
                result += original + "\n\n" + managed_block_str.strip()
            elif original:
                result += original + "\n" + managed_block_str.strip()
            else:
                result += managed_block_str.strip() + "\n"
            return result

        # Find end: Look for next header of level 1 or 2 (siblings or parents)
        header_level_match = re.match(r"^(#+)\s", self.MANAGED_HEADER)
        header_level_prefix = header_level_match.group(1) if header_level_match else "##"

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            # Check if this line is a header of the same level or higher (fewer #s)
            if line.startswith("#"):
                match = re.match(r"^(#+)\s", line)
                if match:
                    level = match.group(1)
                    if len(level) <= len(header_level_prefix):
                        end_idx = i
                        break

        if end_idx == -1:
            end_idx = len(lines)

        # 3. Construct result
        pre_block = "\n".join(lines[:start_idx])
        post_block = "\n".join(lines[end_idx:])

        result = ""
        # Add header comment if not present
        if not has_header and not pre_block.strip().startswith("<!--"):
            result = self.FILE_HEADER_COMMENT

        if pre_block:
            result += pre_block + "\n\n"

        result += managed_block_str

        if post_block:
            # Ensure separation if post block exists and isn't just empty lines
            if post_block.strip():
                result += "\n" + post_block
            else:
                result += post_block  # Keep trailing newlines if any, or normalize?

        return result.strip() + "\n"

    def remove(self) -> bool:
        """
        Removes the managed block from the target file.

        Returns:
            True if changes were written (block removed), False otherwise.
        """
        if not self.target_file.exists():
            return False

        current_content = self.target_file.read_text(encoding="utf-8")
        lines = current_content.splitlines()

        start_idx = -1
        end_idx = -1

        # Find start
        for i, line in enumerate(lines):
            if self.MANAGED_START in line:
                start_idx = i
                # Look for end from here
                for j in range(i, len(lines)):
                    if self.MANAGED_END in lines[j]:
                        end_idx = j + 1 # Include the end line
                        break
                break
        
        if start_idx == -1:
            # Fallback to header logic
             for i, line in enumerate(lines):
                if line.strip() == self.MANAGED_HEADER:
                    start_idx = i
                    break

        if start_idx == -1:
            return False

        if end_idx == -1:
            # Find end: exact logic as in _merge_content
            header_level_match = re.match(r"^(#+)\s", self.MANAGED_HEADER)
            header_level_prefix = header_level_match.group(1) if header_level_match else "##"

            for i in range(start_idx + 1, len(lines)):
                line = lines[i]
                if line.startswith("#"):
                    match = re.match(r"^(#+)\s", line)
                    if match:
                        level = match.group(1)
                        if len(level) <= len(header_level_prefix):
                            end_idx = i
                            break

        if end_idx == -1:
            end_idx = len(lines)

        # Reconstruct content without the block
        # We also need to be careful about surrounding newlines to avoid leaving gaps

        # Check lines before start_idx
        while start_idx > 0 and not lines[start_idx - 1].strip():
            start_idx -= 1

        # Check lines after end_idx (optional, but good for cleanup)
        # Usually end_idx points to the next header or EOF.
        # If it points to next header, we keep it.

        pre_block = lines[:start_idx]
        post_block = lines[end_idx:]

        # Check if pre_block contains only the file header comment
        pre_text = "\n".join(pre_block)
        if pre_text.strip() and "This file is partially managed by Monoco" in pre_text:
            # Check if pre_block is just the header comment
            is_only_header = all(
                line.strip().startswith("<!--") or
                line.strip().startswith("⚠️ IMPORTANT") or
                line.strip().startswith("-") or
                line.strip().startswith("-->") or
                not line.strip()
                for line in pre_block
            )
            if is_only_header and not post_block:
                pre_block = []

        # If we removed everything, the file might become empty or just newlines

        new_lines = pre_block + post_block
        if not new_lines:
            new_content = ""
        else:
            new_content = "\n".join(new_lines).strip() + "\n"

        if new_content != current_content:
            self.target_file.write_text(new_content, encoding="utf-8")
            return True

        return False
