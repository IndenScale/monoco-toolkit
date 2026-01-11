from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field, model_validator
from datetime import datetime

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

class IssueMetadata(BaseModel):
    model_config = {"extra": "allow"}
    
    id: str
    type: IssueType
    status: IssueStatus = IssueStatus.OPEN
    stage: Optional[IssueStage] = None
    title: str
    
    # Time Anchors
    created_at: datetime = Field(default_factory=datetime.now)
    opened_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None

    parent: Optional[str] = None
    sprint: Optional[str] = None
    solution: Optional[IssueSolution] = None
    dependencies: List[str] = []
    related: List[str] = []
    tags: List[str] = []

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
                self.closed_at = datetime.now()
        
        elif self.status == IssueStatus.OPEN:
            # Ensure valid stage for open status
            if self.stage is None or self.stage == IssueStage.DONE:
                self.stage = IssueStage.DOING
        
        return self

class IssueDetail(IssueMetadata):
    body: str = ""
    raw_content: Optional[str] = None # Full file content including frontmatter for editing
