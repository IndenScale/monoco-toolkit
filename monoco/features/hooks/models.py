"""
Universal Hooks: Core Models and Types

Defines the foundational data models for the Universal Hooks system that supports
Git, IDE, and Agent hook types with unified metadata management.
"""

from enum import Enum
from typing import Optional, Any
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class HookType(str, Enum):
    """
    Universal Hook types supported by the system.

    - git: Git lifecycle hooks (pre-commit, pre-push, etc.)
    - ide: IDE integration hooks (on-save, on-open, etc.)
    - agent: Agent lifecycle hooks (session-start, before-tool, etc.)
    """

    GIT = "git"
    IDE = "ide"
    AGENT = "agent"


class GitEvent(str, Enum):
    """
    Git hook events.

    See: https://git-scm.com/docs/githooks
    """

    PRE_COMMIT = "pre-commit"
    PREPARE_COMMIT_MSG = "prepare-commit-msg"
    COMMIT_MSG = "commit-msg"
    POST_MERGE = "post-merge"
    PRE_PUSH = "pre-push"
    POST_CHECKOUT = "post-checkout"
    PRE_REBASE = "pre-rebase"


class AgentEvent(str, Enum):
    """
    Agent lifecycle events.

    Events that occur during agent session execution.
    """

    SESSION_START = "session-start"
    BEFORE_TOOL = "before-tool"
    AFTER_TOOL = "after-tool"
    BEFORE_AGENT = "before-agent"
    AFTER_AGENT = "after-agent"
    SESSION_END = "session-end"


class IDEEvent(str, Enum):
    """
    IDE integration events.

    Events triggered by IDE user interactions.
    """

    ON_SAVE = "on-save"
    ON_OPEN = "on-open"
    ON_CLOSE = "on-close"
    ON_BUILD = "on-build"


class HookMetadata(BaseModel):
    """
    Metadata for a Universal Hook script.

    This model defines the Front Matter schema that can be embedded in hook scripts
    to declare their type, event binding, matching rules, and execution priority.

    Example Front Matter in a shell script:
        # ---
        # type: git
        # event: pre-commit
        # matcher:
        #   - "*.py"
        #   - "*.js"
        # priority: 10
        # description: "Lint Python and JS files before commit"
        # ---

    Example Front Matter for IDE/Agent hooks (requires provider):
        # ---
        # type: agent
        # provider: claude-code
        # event: before-tool
        # priority: 5
        # description: "Log tool usage"
        # ---
    """

    type: HookType = Field(
        ...,  # Required
        description="The hook type: git, ide, or agent"
    )

    event: str = Field(
        ...,  # Required
        description="The event to hook into (e.g., pre-commit, on-save, before-tool)"
    )

    matcher: Optional[list[str]] = Field(
        default=None,
        description="Optional file patterns to match (e.g., ['*.py', '*.js'])"
    )

    priority: int = Field(
        default=100,
        description="Execution priority (lower = earlier, default 100)",
        ge=0,
        le=1000
    )

    description: str = Field(
        default="",
        description="Human-readable description of the hook's purpose"
    )

    provider: Optional[str] = Field(
        default=None,
        description="Required when type is 'agent' or 'ide'. Specifies the provider (e.g., 'claude-code', 'vscode')"
    )

    # Additional flexible metadata for extensibility
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for extensibility"
    )

    @field_validator("matcher", mode="before")
    @classmethod
    def validate_matcher(cls, v):
        """Ensure matcher is a list of strings."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return [str(item) for item in v]
        raise ValueError("matcher must be a string or list of strings")

    @model_validator(mode="after")
    def validate_provider_required(self):
        """
        Validate that provider is provided for agent and ide hook types.
        """
        if self.type in (HookType.AGENT, HookType.IDE) and not self.provider:
            raise ValueError(
                f"'provider' is required when hook type is '{self.type.value}'"
            )
        return self

    @model_validator(mode="after")
    def validate_event_for_type(self):
        """
        Validate that the event is valid for the given hook type.
        """
        valid_events = {
            HookType.GIT: {e.value for e in GitEvent},
            HookType.AGENT: {e.value for e in AgentEvent},
            HookType.IDE: {e.value for e in IDEEvent},
        }

        valid = valid_events.get(self.type, set())
        if valid and self.event not in valid:
            raise ValueError(
                f"Invalid event '{self.event}' for type '{self.type.value}'. "
                f"Valid events: {', '.join(sorted(valid))}"
            )
        return self

    def get_key(self) -> str:
        """
        Generate a unique key for grouping hooks.

        Returns a key in the format: "{type}:{provider}" where provider
        is omitted for git hooks.
        """
        if self.type == HookType.GIT:
            return self.type.value
        return f"{self.type.value}:{self.provider}"

    model_config = ConfigDict(frozen=True, extra="allow")  # Allow extra fields

    @model_validator(mode="before")
    @classmethod
    def collect_extra_fields(cls, data):
        """Collect unknown fields into the extra dictionary."""
        if not isinstance(data, dict):
            return data

        # Known field names
        known_fields = {"type", "event", "matcher", "priority", "description", "provider", "extra"}

        # Separate known and unknown fields
        extra = {}
        cleaned = {}
        for key, value in data.items():
            if key in known_fields:
                cleaned[key] = value
            else:
                extra[key] = value

        # Add extra fields to the extra field
        if extra:
            existing_extra = cleaned.get("extra", {})
            if isinstance(existing_extra, dict):
                existing_extra.update(extra)
            else:
                existing_extra = extra
            cleaned["extra"] = existing_extra

        return cleaned


class ParsedHook(BaseModel):
    """
    A hook script that has been parsed with its metadata.

    Contains both the metadata and the original script content/path
    for execution.
    """

    metadata: HookMetadata
    script_path: Path
    content: str
    front_matter_start_line: int = 0
    front_matter_end_line: int = 0

    model_config = {"arbitrary_types_allowed": True, "frozen": True}


class HookGroup(BaseModel):
    """
    A group of hooks organized by type and provider.

    Used by UniversalHookManager to organize scanned hooks.
    """

    key: str  # e.g., "git" or "agent:claude-code"
    hook_type: HookType
    provider: Optional[str] = None
    hooks: list[ParsedHook] = Field(default_factory=list)

    def add_hook(self, hook: ParsedHook) -> None:
        """Add a hook to this group and re-sort by priority."""
        self.hooks.append(hook)
        # Sort by priority (lower = earlier)
        self.hooks.sort(key=lambda h: h.metadata.priority)

    def get_prioritized_hooks(self) -> list[ParsedHook]:
        """Get hooks sorted by priority."""
        return self.hooks
