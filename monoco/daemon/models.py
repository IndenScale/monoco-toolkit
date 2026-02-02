from pydantic import BaseModel
from typing import Optional, List
from monoco.features.issue.models import (
    IssueType,
    IssueStatus,
    IssueSolution,
    IssueStage,
)


class CreateIssueRequest(BaseModel):
    type: IssueType
    title: str
    parent: Optional[str] = None
    status: IssueStatus = IssueStatus.OPEN
    stage: Optional[IssueStage] = None
    dependencies: List[str] = []
    related: List[str] = []
    subdir: Optional[str] = None
    project_id: Optional[str] = None  # Added for multi-project support
    from_memos: List[str] = []  # Memo IDs to link to this issue


class UpdateIssueRequest(BaseModel):
    status: Optional[IssueStatus] = None
    stage: Optional[IssueStage] = None
    solution: Optional[IssueSolution] = None
    parent: Optional[str] = None
    dependencies: Optional[List[str]] = None
    related: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    project_id: Optional[str] = None


class UpdateIssueContentRequest(BaseModel):
    content: str
    project_id: Optional[str] = None
