"""
Last-Word: Session-End Knowledge Delta Protocol Models.

This module defines the data models for the last-word protocol, which enables
declarative knowledge base updates at the end of an agent session.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class OperationType(str, Enum):
    """
    Knowledge update operation types.
    
    | content value | operation | behavior                      |
    |---------------|-----------|-------------------------------|
    | null (default)| no-op     | No update (placeholder)       |
    | "..."         | update    | Create or overwrite heading   |
    | ""            | clear     | Clear content, keep heading   |
    | null          | delete    | Delete entire heading         |
    """
    NO_OP = "no-op"
    UPDATE = "update"
    CLEAR = "clear"
    DELETE = "delete"


class TargetKey(BaseModel):
    """
    Unique identifier for a knowledge base target.
    
    The combination of (path, heading, level) must be unique within a session.
    """
    path: str = Field(
        ...,
        description="Target file path (supports ~ expansion and relative paths)"
    )
    heading: str = Field(
        ...,
        description="Exact heading text to target"
    )
    level: int = Field(
        default=2,
        ge=1,
        le=6,
        description="Heading level (1-6)"
    )
    
    @field_validator("path")
    @classmethod
    def expand_home(cls, v: str) -> str:
        """Expand ~ to home directory."""
        if v.startswith("~/"):
            return str(Path.home() / v[2:])
        return v
    
    def __hash__(self) -> int:
        """Enable using TargetKey as dict key."""
        return hash((self.path, self.heading, self.level))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TargetKey):
            return NotImplemented
        return (self.path, self.heading, self.level) == (
            other.path, other.heading, other.level
        )


class EntryMeta(BaseModel):
    """Metadata for a knowledge update entry."""
    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence level of the update (0-1)"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for the update"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this entry was created"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Source session identifier"
    )


class Entry(BaseModel):
    """
    A single knowledge update entry.
    
    Represents an intention to update a specific heading in a knowledge base file.
    """
    key: TargetKey = Field(
        ...,
        description="Target identification"
    )
    operation: OperationType = Field(
        default=OperationType.NO_OP,
        description="Type of update operation"
    )
    content: Optional[str] = Field(
        default=None,
        description="Content to update (null for no-op/delete, empty string for clear)"
    )
    meta: EntryMeta = Field(
        default_factory=EntryMeta,
        description="Entry metadata"
    )
    
    @model_validator(mode="after")
    def validate_content_operation(self) -> "Entry":
        """Validate content-operation consistency."""
        # If content is None
        if self.content is None:
            # Auto-correct operation based on content
            if self.operation == OperationType.UPDATE:
                # UPDATE with null content becomes DELETE
                self.operation = OperationType.DELETE
            elif self.operation == OperationType.CLEAR:
                # CLEAR with null content becomes DELETE
                self.operation = OperationType.DELETE
            # NO_OP and DELETE stay as-is
        # If content is empty string
        elif self.content == "":
            # Empty string means clear content
            if self.operation == OperationType.UPDATE:
                self.operation = OperationType.CLEAR
            elif self.operation == OperationType.NO_OP:
                self.operation = OperationType.CLEAR
            # DELETE with empty string stays DELETE
        return self
    
    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "key": {
                "path": self.key.path,
                "heading": self.key.heading,
                "level": self.key.level,
            },
            "operation": self.operation.value,
            "content": self.content,
            "meta": {
                "confidence": self.meta.confidence,
                "reason": self.meta.reason,
                "created_at": self.meta.created_at.isoformat(),
                "session_id": self.meta.session_id,
            }
        }
    
    @classmethod
    def from_yaml_dict(cls, data: dict[str, Any]) -> "Entry":
        """Create Entry from YAML dictionary."""
        key_data = data.get("key", {})
        meta_data = data.get("meta", {})
        
        # Parse datetime
        created_at_str = meta_data.get("created_at")
        created_at = (
            datetime.fromisoformat(created_at_str) 
            if created_at_str 
            else datetime.now()
        )
        
        return cls(
            key=TargetKey(
                path=key_data.get("path", ""),
                heading=key_data.get("heading", ""),
                level=key_data.get("level", 2),
            ),
            operation=OperationType(data.get("operation", "no-op")),
            content=data.get("content"),
            meta=EntryMeta(
                confidence=meta_data.get("confidence", 0.9),
                reason=meta_data.get("reason"),
                created_at=created_at,
                session_id=meta_data.get("session_id"),
            )
        )


class SchemaVersion(BaseModel):
    """Schema version information."""
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @classmethod
    def parse(cls, version_str: str) -> "SchemaVersion":
        """Parse version string like '1.0.0'."""
        parts = version_str.split(".")
        return cls(
            major=int(parts[0]) if len(parts) > 0 else 0,
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0,
        )


class LastWordSchema(BaseModel):
    """
    Top-level schema for last-word knowledge update declarations.
    
    This is the structure stored in .yaml files.
    """
    version: str = Field(
        default="1.0.0",
        description="Schema version"
    )
    source: Optional[str] = Field(
        default=None,
        description="Source session or process identifier"
    )
    entries: list[Entry] = Field(
        default_factory=list,
        description="List of knowledge update entries"
    )
    
    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        import yaml
        data = {
            "version": self.version,
            "source": self.source,
            "entries": [e.to_yaml_dict() for e in self.entries],
        }
        return yaml.dump(data, allow_unicode=True, sort_keys=False)
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> "LastWordSchema":
        """Parse from YAML string."""
        import yaml
        data = yaml.safe_load(yaml_str)
        return cls(
            version=data.get("version", "1.0.0"),
            source=data.get("source"),
            entries=[
                Entry.from_yaml_dict(e) 
                for e in data.get("entries", [])
            ]
        )


class ValidationError(BaseModel):
    """Entry validation error."""
    entry: Entry
    error: str
    error_code: str


class ValidationResult(BaseModel):
    """Result of validating entries."""
    valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


class StagedFile(BaseModel):
    """A staged update file waiting to be applied."""
    path: Path
    created_at: datetime
    target_file: str
    
    @property
    def filename(self) -> str:
        return self.path.name


class ApplyResult(BaseModel):
    """Result of applying a last-word update."""
    success: bool
    entry: Entry
    target_file: str
    error: Optional[str] = None
    applied_at: datetime = Field(default_factory=datetime.now)


class KnowledgeBaseConfig(BaseModel):
    """Configuration for a single knowledge base."""
    name: str
    path: str
    enabled: bool = True
    description: Optional[str] = None


class LastWordConfig(BaseModel):
    """
    Configuration for the last-word system.
    
    Stored in ~/.config/agents/last-word/config.yaml
    """
    version: str = "1.0.0"
    
    # Default knowledge bases
    global_agents: KnowledgeBaseConfig = Field(
        default_factory=lambda: KnowledgeBaseConfig(
            name="global_agents",
            path="~/.config/agents/AGENTS.md",
            description="Global best practices across projects"
        )
    )
    soul: KnowledgeBaseConfig = Field(
        default_factory=lambda: KnowledgeBaseConfig(
            name="soul",
            path="~/.config/agents/SOUL.md",
            description="Self personality and values"
        )
    )
    user: KnowledgeBaseConfig = Field(
        default_factory=lambda: KnowledgeBaseConfig(
            name="user",
            path="~/.config/agents/USER.md",
            description="User identity, preferences, background"
        )
    )
    
    # Project-level knowledge (auto-detected)
    project_knowledge: Optional[KnowledgeBaseConfig] = None
    
    # Session bootstrap: knowledge bases to load on session start
    session_bootstrap: list[str] = Field(
        default_factory=lambda: ["global_agents", "soul", "user"]
    )
    
    # Retry configuration
    max_retries: int = 3
    retry_base_delay: float = 1.0  # seconds
    retry_max_delay: float = 10.0  # seconds
    
    def get_knowledge_base(self, name: str) -> Optional[KnowledgeBaseConfig]:
        """Get knowledge base by name."""
        kb_map = {
            "global_agents": self.global_agents,
            "soul": self.soul,
            "user": self.user,
        }
        if name in kb_map:
            return kb_map[name]
        if name == "project" and self.project_knowledge:
            return self.project_knowledge
        return None
