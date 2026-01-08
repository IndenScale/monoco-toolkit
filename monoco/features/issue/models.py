from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class IssueType(str, Enum):
    EPIC = "epic"
    STORY = "story"
    TASK = "task"
    BUG = "bug"

class IssueStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    BACKLOG = "backlog"

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
    title: str
    created_at: Any = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    parent: Optional[str] = None
    sprint: Optional[str] = None
    solution: Optional[IssueSolution] = None
    tags: List[str] = []
