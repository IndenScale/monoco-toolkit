from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field
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
    dependencies: List[str] = []
    related: List[str] = []
    tags: List[str] = []

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
        return v

    def __init__(self, **data):
        super().__init__(**self.normalize_fields(data))

