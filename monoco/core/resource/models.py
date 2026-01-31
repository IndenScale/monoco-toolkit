from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from enum import Enum

class ResourceType(str, Enum):
    PROMPTS = "prompts"
    RULES = "rules"
    SKILLS = "skills"
    ROLES = "roles"
    GLOSSARY = "glossary"
    TEMPLATES = "templates"
    DOCS = "docs"
    OTHER = "other"

@dataclass
class ResourceNode:
    """
    Represents a discovered resource file in a Python package.
    """
    name: str
    path: Path  # Absolute path to the source file
    type: ResourceType
    language: str  # "en", "zh", etc.
    content: Optional[str] = None  # Lazy loaded content
    
    @property
    def key(self) -> str:
        """Unique identifier for the resource (e.g. 'agent.prompts.system')"""
        return f"{self.type.value}.{self.name}"

    def read_text(self) -> str:
        if self.content:
            return self.content
        return self.path.read_text(encoding="utf-8")
