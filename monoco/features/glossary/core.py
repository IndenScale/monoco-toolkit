import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class GlossaryManager:
    """
    Manages the retrieval and formatting of glossary resources.
    """
    
    delimiters = {
        "start": "<!-- MONOCO_GENERATED_START: glossary -->",
        "end": "<!-- MONOCO_GENERATED_END: glossary -->"
    }

    def __init__(self):
        # Locate resources relative to this file
        self.resource_base = Path(__file__).parent / "resources"

    def get_glossary_content(self, lang: str = "en") -> str:
        """
        Retrieve the raw markdown content for the specified language.
        Falls back to 'en' if the specific language is not found.
        """
        target_file = self.resource_base / lang / "glossary.md"
        
        if not target_file.exists():
            logger.warning(f"Glossary resource for language '{lang}' not found at {target_file}. Falling back to 'en'.")
            target_file = self.resource_base / "en" / "glossary.md"
            
        if not target_file.exists():
            logger.error(f"Glossary resource not found even in fallback 'en'.")
            return ""
            
        return target_file.read_text(encoding="utf-8")

    def format_for_injection(self, content: str, header_offset: int = 0) -> str:
        """
        Format the content for injection:
        1. Apply header level offset (demote headers).
        2. Wrap in generated delimiters.
        """
        if not content:
            return ""

        lines = content.splitlines()
        formatted_lines = []
        
        for line in lines:
            if line.strip().startswith("#"):
                # Add '#' to demote the header based on offset
                # If offset is 1, # becomes ##
                formatted_lines.append("#" * header_offset + line)
            else:
                formatted_lines.append(line)
        
        body = "\n".join(formatted_lines)
        
        return f"{self.delimiters['start']}\n\n{body}\n\n{self.delimiters['end']}"

    def inject_into_file(self, target_file_path: Path, lang: str = "en", header_offset: int = 1) -> bool:
        """
        Injects the glossary into the target file, replacing the content between delimiters.
        Appends to end if delimiters not found (with a newline).
        """
        content = self.get_glossary_content(lang)
        if not content:
            return False
            
        formatted_block = self.format_for_injection(content, header_offset)
        
        # Read target file
        if not target_file_path.exists():
            # If file doesn't exist, just write it
            target_file_path.write_text(formatted_block, encoding="utf-8")
            return True
            
        target_content = target_file_path.read_text(encoding="utf-8")
        
        start_marker = self.delimiters["start"]
        end_marker = self.delimiters["end"]
        
        if start_marker in target_content and end_marker in target_content:
            # Replace existing block
            pre = target_content.split(start_marker)[0]
            # Find the part after end_marker
            # split might be dangerous if multiple markers, assuming unique for now per section
            post = target_content.split(end_marker)[1]
            
            new_content = pre + formatted_block + post
        else:
            # Append
            new_content = target_content + "\n\n" + formatted_block
            
        target_file_path.write_text(new_content, encoding="utf-8")
        return True
