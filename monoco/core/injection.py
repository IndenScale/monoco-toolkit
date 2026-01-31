import re
from pathlib import Path
from typing import Dict


class PromptInjector:
    """
    Engine for injecting managed content into Markdown-like files (e.g., .cursorrules, GEMINI.md).
    Maintains a 'Managed Block' defined by a specific header.
    """

    MANAGED_HEADER = "## Monoco Toolkit"
    MANAGED_START = "<!-- MONOCO_GENERATED_START -->"
    MANAGED_END = "<!-- MONOCO_GENERATED_END -->"

    def __init__(self, target_file: Path):
        self.target_file = target_file

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
            # We assume the content headers start at # or ##. 
            # We map # -> ####, ## -> #####, etc. (+3 offset)
            demoted_content = []
            for line in clean_content.splitlines():
                if line.lstrip().startswith("#"):
                    demoted_content.append("###" + line)
                else:
                    demoted_content.append(line)
            
            managed_block.append("\n".join(demoted_content))
            managed_block.append("")  # Blank line after section

        managed_block_str = "\n".join(managed_block).strip() + "\n"
        managed_block_str = f"{self.MANAGED_START}\n{managed_block_str}\n{self.MANAGED_END}\n"

        # 2. Find and replace/append in the original content
        # Check for delimiters first
        if self.MANAGED_START in original and self.MANAGED_END in original:
            try:
                pre = original.split(self.MANAGED_START)[0]
                post = original.split(self.MANAGED_END)[1]
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
            if original and not original.endswith("\n"):
                return original + "\n\n" + managed_block_str.strip()
            elif original:
                return original + "\n" + managed_block_str.strip()
            else:
                return managed_block_str.strip() + "\n"

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

        result = pre_block
        if result:
            result += "\n\n"

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
