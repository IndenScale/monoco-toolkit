"""
Issue Lifecycle Hooks: Domain Models

Defines the core data structures for the Issue Lifecycle Hooks system.
Following ADR-001, this module provides:
- IssueEvent: Enumeration of lifecycle events
- HookDecision: Decision enum for hook results
- IssueHookResult: Structured result with diagnostics and suggestions
- IssueHookContext: Context passed to hooks during execution
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class IssueEvent(str, Enum):
    """
    Issue Lifecycle Events - Canonical Naming (pre/post prefix).
    
    All events follow the Monoco ACL unified protocol with strict `pre-` and `post-`
    prefixes. This ensures internal consistency regardless of external Agent naming.
    """
    # Issue Lifecycle
    PRE_CREATE = "pre-issue-create"
    POST_CREATE = "post-issue-create"
    PRE_START = "pre-issue-start"
    POST_START = "post-issue-start"
    PRE_SUBMIT = "pre-issue-submit"
    POST_SUBMIT = "post-issue-submit"
    PRE_CLOSE = "pre-issue-close"
    POST_CLOSE = "post-issue-close"
    
    # Additional lifecycle events
    PRE_OPEN = "pre-issue-open"
    POST_OPEN = "post-issue-open"
    PRE_CANCEL = "pre-issue-cancel"
    POST_CANCEL = "post-issue-cancel"
    PRE_DELETE = "pre-issue-delete"
    POST_DELETE = "post-issue-delete"


class AgnosticAgentEvent(str, Enum):
    """
    Agnostic Agent Lifecycle Events (Canonical ACL).
    
    These events are mapped from/to Agent-specific events via NamingACL.
    """
    PRE_SESSION = "pre-session"
    POST_SESSION = "post-session"
    PRE_AGENT = "pre-agent"
    POST_AGENT = "post-agent"
    PRE_SUBAGENT = "pre-subagent"
    POST_SUBAGENT = "post-subagent"
    PRE_TOOL_USE = "pre-tool-use"
    POST_TOOL_USE = "post-tool-use"
    PRE_COMPACT = "pre-compact"


class HookDecision(str, Enum):
    """
    Hook execution decision.
    
    - ALLOW: Check passed, continue execution
    - WARN: Warning but allow continuation
    - DENY: Check failed, block command execution
    """
    ALLOW = "allow"
    WARN = "warn"
    DENY = "deny"


class Diagnostic(BaseModel):
    """Diagnostic information for hook failures."""
    line: Optional[int] = None
    column: Optional[int] = None
    severity: Literal["error", "warning", "info"] = "error"
    message: str
    source: Optional[str] = None
    
    model_config = ConfigDict(frozen=True)


class IssueHookResult(BaseModel):
    """
    Result of an Issue Hook execution.
    
    Provides structured feedback for Agents to parse and act upon.
    """
    decision: HookDecision = HookDecision.ALLOW
    message: str = ""
    diagnostics: List[Diagnostic] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: Optional[float] = None
    hook_name: Optional[str] = None
    
    model_config = ConfigDict(frozen=True)
    
    @classmethod
    def allow(cls, message: str = "", **kwargs) -> "IssueHookResult":
        """Create an ALLOW result."""
        return cls(decision=HookDecision.ALLOW, message=message, **kwargs)
    
    @classmethod
    def warn(cls, message: str, suggestions: Optional[List[str]] = None, **kwargs) -> "IssueHookResult":
        """Create a WARN result."""
        return cls(
            decision=HookDecision.WARN,
            message=message,
            suggestions=suggestions or [],
            **kwargs
        )
    
    @classmethod
    def deny(cls, message: str, suggestions: Optional[List[str]] = None, **kwargs) -> "IssueHookResult":
        """Create a DENY result."""
        return cls(
            decision=HookDecision.DENY,
            message=message,
            suggestions=suggestions or [],
            **kwargs
        )


class IssueHookContext(BaseModel):
    """
    Context passed to Issue Hooks during execution.
    
    Contains all relevant information about the execution environment,
    target issue, and trigger source.
    """
    # Event Information
    event: IssueEvent
    trigger_source: Literal["cli", "agent", "git", "webhook", "internal"] = "cli"
    
    # Issue Information
    issue_id: Optional[str] = None
    issue_type: Optional[str] = None
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    from_stage: Optional[str] = None
    to_stage: Optional[str] = None
    issue_path: Optional[Path] = None
    
    # Git Information
    project_root: Optional[Path] = None
    current_branch: Optional[str] = None
    default_branch: Optional[str] = None
    has_uncommitted_changes: bool = False
    
    # User Information
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    
    # Execution Options
    force: bool = False
    dry_run: bool = False
    no_hooks: bool = False
    debug_hooks: bool = False
    
    # Extra context for extensibility
    extra: Dict[str, Any] = Field(default_factory=dict)
    
    # Runtime info
    timestamp: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class HookMetadata(BaseModel):
    """
    Metadata for an Issue Hook script.
    
    Similar to universal hooks but specific to Issue lifecycle.
    """
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: Optional[str] = None
    
    # Event binding
    events: List[IssueEvent] = Field(default_factory=list)
    
    # Execution configuration
    priority: int = Field(default=100, ge=0, le=1000)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    
    # Script info
    script_path: Optional[Path] = None
    script_type: Literal["python", "shell", "builtin"] = "python"
    
    # Runtime state
    enabled: bool = True
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class NamingACL:
    """
    Naming ACL (Agent Compatibility Layer) for event name mapping.
    
    Maps between Monoco's canonical `pre/post` naming and Agent-specific events.
    This ensures internal consistency while maintaining compatibility with
    various Agent implementations (Claude Code, Gemini CLI, etc.).
    """
    
    # Claude Code specific mappings
    CLAUDE_MAPPING = {
        "pre-session": "SessionStart",
        "post-session": "SessionEnd",
        "pre-agent": "UserPromptSubmit",
        "post-agent": "Stop",
        "pre-subagent": "SubagentStart",
        "post-subagent": "SubagentStop",
        "pre-tool-use": "PreToolUse",
        "post-tool-use": "PostToolUse",
        "pre-compact": "PreCompact",
    }
    
    # Gemini CLI specific mappings
    GEMINI_MAPPING = {
        "pre-session": "SessionStart",
        "post-session": "SessionEnd",
        "pre-agent": "BeforeAgent",
        "post-agent": "AfterAgent",
        "pre-tool-use": "BeforeTool",
        "post-tool-use": "AfterTool",
        "pre-compact": "PreCompress",
    }
    
    @classmethod
    def to_agent_event(cls, canonical_event: str, agent_type: str = "claude") -> Optional[str]:
        """
        Convert canonical Monoco event to Agent-specific event name.
        
        Args:
            canonical_event: The canonical event name (e.g., "pre-tool-use")
            agent_type: The agent type ("claude", "gemini")
            
        Returns:
            The agent-specific event name or None if not mapped
        """
        mapping = cls.CLAUDE_MAPPING if agent_type == "claude" else cls.GEMINI_MAPPING
        return mapping.get(canonical_event)
    
    @classmethod
    def from_agent_event(cls, agent_event: str, agent_type: str = "claude") -> Optional[str]:
        """
        Convert Agent-specific event name to canonical Monoco event.
        
        Args:
            agent_event: The agent-specific event name (e.g., "PreToolUse")
            agent_type: The agent type ("claude", "gemini")
            
        Returns:
            The canonical event name or None if not mapped
        """
        mapping = cls.CLAUDE_MAPPING if agent_type == "claude" else cls.GEMINI_MAPPING
        reverse_mapping = {v: k for k, v in mapping.items()}
        return reverse_mapping.get(agent_event)
    
    @classmethod
    def is_canonical(cls, event_name: str) -> bool:
        """Check if the event name follows canonical pre/post naming."""
        return event_name.startswith(("pre-", "post-"))


# Issue command to event mapping
COMMAND_EVENT_MAP = {
    "create": (IssueEvent.PRE_CREATE, IssueEvent.POST_CREATE),
    "start": (IssueEvent.PRE_START, IssueEvent.POST_START),
    "submit": (IssueEvent.PRE_SUBMIT, IssueEvent.POST_SUBMIT),
    "close": (IssueEvent.PRE_CLOSE, IssueEvent.POST_CLOSE),
    "open": (IssueEvent.PRE_OPEN, IssueEvent.POST_OPEN),
    "cancel": (IssueEvent.PRE_CANCEL, IssueEvent.POST_CANCEL),
    "delete": (IssueEvent.PRE_DELETE, IssueEvent.POST_DELETE),
}


def get_events_for_command(command: str) -> tuple[Optional[IssueEvent], Optional[IssueEvent]]:
    """
    Get the pre and post events for a given command.
    
    Returns:
        Tuple of (pre_event, post_event) or (None, None) if command not found
    """
    return COMMAND_EVENT_MAP.get(command, (None, None))
