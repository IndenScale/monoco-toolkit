from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
import hashlib
import secrets


class IssueID:
    """
    Helper for parsing Issue IDs that might be namespaced (e.g. 'toolkit::FEAT-0001').
    """
    def __init__(self, raw: str):
        self.raw = raw
        if "::" in raw:
            self.namespace, self.local_id = raw.split("::", 1)
        else:
            self.namespace = None
            self.local_id = raw

    def __str__(self):
        if self.namespace:
            return f"{self.namespace}::{self.local_id}"
        return self.local_id
        
    def __repr__(self):
        return f"IssueID({self.raw})"

    @property
    def is_local(self) -> bool:
        return self.namespace is None

    def matches(self, other_id: str) -> bool:
        """Check if this ID matches another ID string."""
        return str(self) == other_id or (self.is_local and self.local_id == other_id)

def current_time() -> datetime:
    return datetime.now().replace(microsecond=0)

def generate_uid() -> str:
    """
    Generate a globally unique 6-character short hash for issue identity.
    Uses timestamp + random bytes to ensure uniqueness across projects.
    """
    timestamp = str(datetime.now().timestamp()).encode()
    random_bytes = secrets.token_bytes(8)
    combined = timestamp + random_bytes
    hash_digest = hashlib.sha256(combined).hexdigest()
    return hash_digest[:6]


class IssueType(str, Enum):
    EPIC = "epic"
    FEATURE = "feature"
    CHORE = "chore"
    FIX = "fix"

class IssueStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    BACKLOG = "backlog"

class IssueStage(str, Enum):
    DRAFT = "draft"
    DOING = "doing"
    REVIEW = "review"
    DONE = "done"
    FREEZED = "freezed"

class IssueSolution(str, Enum):
    IMPLEMENTED = "implemented"
    CANCELLED = "cancelled"
    WONTFIX = "wontfix"
    DUPLICATE = "duplicate"

class IsolationType(str, Enum):
    BRANCH = "branch"
    WORKTREE = "worktree"

class IssueIsolation(BaseModel):
    type: str
    ref: str  # Git branch name
    path: Optional[str] = None  # Worktree path (relative to repo root or absolute)
    created_at: datetime = Field(default_factory=current_time)

class IssueAction(BaseModel):
    label: str
    target_status: Optional[str] = None
    target_stage: Optional[str] = None
    target_solution: Optional[str] = None
    icon: Optional[str] = None
    
    # Generic execution extensions
    command: Optional[str] = None
    params: Dict[str, Any] = {}

class IssueMetadata(BaseModel):
    model_config = {"extra": "allow"}
    
    id: str
    uid: Optional[str] = None  # Global unique identifier for cross-project identity
    type: str
    status: str = "open"
    stage: Optional[str] = None
    title: str
    
    # Time Anchors
    created_at: datetime = Field(default_factory=current_time)
    opened_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=current_time)
    closed_at: Optional[datetime] = None

    parent: Optional[str] = None
    sprint: Optional[str] = None
    solution: Optional[str] = None
    isolation: Optional[IssueIsolation] = None
    dependencies: List[str] = []
    related: List[str] = []
    tags: List[str] = []
    path: Optional[str] = None  # Absolute path to the issue file
    
    # Proxy UI Actions (Excluded from file persistence)
    actions: List[IssueAction] = Field(default=[], exclude=True)


    @model_validator(mode='before')
    @classmethod
    def normalize_fields(cls, v: Any) -> Any:
        if isinstance(v, dict):
            # Handle common capitalization variations for robustness
            field_map = {
                "ID": "id",
                "Type": "type",
                "Status": "status",
                "Stage": "stage",
                "Title": "title",
                "Parent": "parent",
                "Solution": "solution",
                "Sprint": "sprint",
            }
            for old_k, new_k in field_map.items():
                if old_k in v and new_k not in v:
                    v[new_k] = v[old_k] # Don't pop yet to avoid mutation issues if used elsewhere, or pop if safe.
                    # Pydantic v2 mode='before' is usually a copy if we want to be safe, but let's just add it.

            # Normalize type and status to lowercase for compatibility
            if "type" in v and isinstance(v["type"], str):
                v["type"] = v["type"].lower()
            if "status" in v and isinstance(v["status"], str):
                v["status"] = v["status"].lower()
            if "solution" in v and isinstance(v["solution"], str):
                v["solution"] = v["solution"].lower()
            # Stage normalization
            if "stage" in v and isinstance(v["stage"], str):
                v["stage"] = v["stage"].lower()
                if v["stage"] == "todo":
                    v["stage"] = "draft"
        return v

    @model_validator(mode='after')
    def validate_lifecycle(self) -> 'IssueMetadata':
        # Logic Definition:
        # status: backlog -> stage: freezed
        # status: closed -> stage: done
        # status: open -> stage: draft | doing | review | done (default draft)
        
        # NOTE: We do NOT auto-correct state here anymore to allow Linter to detect inconsistencies.
        # Auto-correction should be applied explicitly by 'create' or 'update' commands via core logic.
        
        return self

class IssueDetail(IssueMetadata):
    body: str = ""
    raw_content: Optional[str] = None # Full file content including frontmatter for editing
