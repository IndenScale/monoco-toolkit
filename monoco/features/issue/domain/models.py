from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from ..models import (
    IssueType,
    IssueStatus,
    IssueStage,
    IssueSolution,
    IssueIsolation,
    current_time,
)
from monoco.core.lsp import Range


class Span(BaseModel):
    """
    Represents a fine-grained location inside a ContentBlock.
    """

    type: str  # 'wikilink', 'issue_id', 'checkbox', 'yaml_key', 'plain_text'
    range: Range
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentBlock(BaseModel):
    """
    Represents a block of content in the markdown body.
    """

    type: str  # e.g., 'heading', 'task_list', 'paragraph', 'empty'
    content: str
    line_start: int
    line_end: int
    spans: List[Span] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_string(self) -> str:
        return self.content


from enum import Enum


class TaskState(str, Enum):
    TODO = " "
    DONE = "x"
    DOING = "-"
    CANCELLED = "+"


class TaskItem(ContentBlock):
    type: str = "task_item"  # override type
    state: TaskState = TaskState.TODO
    level: int = 0
    parent_index: Optional[int] = None

    @property
    def is_completed(self) -> bool:
        return self.state in [TaskState.DONE, TaskState.CANCELLED]


class IssueBody(BaseModel):
    """
    Represents the parsed body of the issue.
    """

    blocks: List[ContentBlock] = Field(default_factory=list)

    def to_markdown(self) -> str:
        return "\n".join(b.to_string() for b in self.blocks)

    @property
    def raw(self) -> str:
        return self.to_markdown()

    @property
    def tasks(self) -> List[TaskItem]:
        return [
            b
            for b in self.blocks
            if isinstance(b, TaskItem)
            or (isinstance(b, ContentBlock) and b.type == "task_item")
        ]

    @property
    def progress(self) -> str:
        tasks = self.tasks
        if not tasks:
            return "0/0"
        completed = len(
            [t for t in tasks if isinstance(t, TaskItem) and t.is_completed]
        )
        return f"{completed}/{len(tasks)}"


class IssueFrontmatter(BaseModel):
    """
    Represents the YAML frontmatter of the issue.
    Contains metadata and validation logic.
    """

    id: str
    uid: Optional[str] = None
    type: IssueType
    status: IssueStatus = IssueStatus.OPEN
    stage: Optional[IssueStage] = None
    title: str
    created_at: datetime = Field(default_factory=current_time)
    opened_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=current_time)
    closed_at: Optional[datetime] = None
    parent: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    related: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    solution: Optional[IssueSolution] = None
    isolation: Optional[IssueIsolation] = None

    model_config = {"extra": "allow"}

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, v: Any) -> Any:
        # Reusing normalization logic from original model or keeping it clean here
        if isinstance(v, dict):
            if "type" in v and isinstance(v["type"], str):
                v["type"] = v["type"].lower()
            if "status" in v and isinstance(v["status"], str):
                v["status"] = v["status"].lower()
        return v


class Issue(BaseModel):
    """
    The Aggregate Root for an Issue in the Domain Layer.
    """

    path: Optional[str] = None
    frontmatter: IssueFrontmatter
    body: IssueBody

    @property
    def id(self) -> str:
        return self.frontmatter.id

    @property
    def status(self) -> IssueStatus:
        return self.frontmatter.status

    def to_file_content(self) -> str:
        """
        Reconstruct the full file content.
        """
        import yaml

        # Dump frontmatter
        # Dump frontmatter with explicit field handling
        # We want to keep certain fields even if empty to serve as prompts
        data = self.frontmatter.model_dump(mode="json")

        # Explicit ordering and key retention
        # We construct a new dict to control order and presence
        ordered_dump = {}

        # 1. Identity
        ordered_dump["id"] = data["id"]
        if data.get("uid"):
            ordered_dump["uid"] = data["uid"]

        # 2. Classifier
        ordered_dump["type"] = data["type"]
        ordered_dump["status"] = data["status"]
        if data.get("stage"):
            ordered_dump["stage"] = data["stage"]

        # 3. Content
        ordered_dump["title"] = data["title"]

        # 4. Dates (Always keep created/updated, others if exist)
        ordered_dump["created_at"] = data["created_at"]
        if data.get("opened_at"):
            ordered_dump["opened_at"] = data["opened_at"]
        ordered_dump["updated_at"] = data["updated_at"]
        if data.get("closed_at"):
            ordered_dump["closed_at"] = data["closed_at"]

        # 5. Graph (Always include to prompt usage)
        ordered_dump["parent"] = data.get("parent")  # Allow null
        ordered_dump["dependencies"] = data.get("dependencies", [])
        ordered_dump["related"] = data.get("related", [])
        ordered_dump["tags"] = data.get("tags", [])

        # 6. Lifecycle (Optional)
        if data.get("solution"):
            ordered_dump["solution"] = data["solution"]
        if data.get("isolation"):
            ordered_dump["isolation"] = data["isolation"]

        fm_str = yaml.dump(ordered_dump, sort_keys=False, allow_unicode=True).strip()
        body_str = self.body.to_markdown()

        return f"---\n{fm_str}\n---\n\n{body_str}"
