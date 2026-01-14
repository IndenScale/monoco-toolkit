from enum import Enum
from typing import List, Optional, Any
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
    TODO = "todo"
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
    type: IsolationType
    ref: str  # Git branch name
    path: Optional[str] = None  # Worktree path (relative to repo root or absolute)
    created_at: datetime = Field(default_factory=current_time)

class IssueMetadata(BaseModel):
    model_config = {"extra": "allow"}
    
    id: str
    uid: Optional[str] = None  # Global unique identifier for cross-project identity
    type: IssueType
    status: IssueStatus = IssueStatus.OPEN
    stage: Optional[IssueStage] = None
    title: str
    
    # Time Anchors
    created_at: datetime = Field(default_factory=current_time)
    opened_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=current_time)
    closed_at: Optional[datetime] = None

    parent: Optional[str] = None
    sprint: Optional[str] = None
    solution: Optional[IssueSolution] = None
    isolation: Optional[IssueIsolation] = None
    dependencies: List[str] = []
    related: List[str] = []
    dependencies: List[str] = []
    related: List[str] = []
    tags: List[str] = []
    path: Optional[str] = None  # Absolute path to the issue file


    @model_validator(mode='before')
    @classmethod
    def normalize_fields(cls, v: Any) -> Any:
        if isinstance(v, dict):
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
        return v

    @model_validator(mode='after')
    def validate_lifecycle(self) -> 'IssueMetadata':
        # Logic Definition:
        # status: backlog -> stage: null
        # status: closed -> stage: done
        # status: open -> stage: todo | doing | review (default todo)

        if self.status == IssueStatus.BACKLOG:
            self.stage = IssueStage.FREEZED
        
        elif self.status == IssueStatus.CLOSED:
            # Enforce stage=done for closed issues
            if self.stage != IssueStage.DONE:
                self.stage = IssueStage.DONE
            # Auto-fill closed_at if missing
            if not self.closed_at:
                self.closed_at = current_time()
        
        elif self.status == IssueStatus.OPEN:
            # Ensure valid stage for open status
            if self.stage is None or self.stage == IssueStage.DONE:
                self.stage = IssueStage.TODO
        
        return self

class IssueDetail(IssueMetadata):
    body: str = ""
    raw_content: Optional[str] = None # Full file content including frontmatter for editing
