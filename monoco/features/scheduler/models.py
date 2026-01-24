from typing import List
from pydantic import BaseModel, Field


class RoleTemplate(BaseModel):
    name: str = Field(
        ..., description="Unique identifier for the role (e.g., 'crafter')"
    )
    description: str = Field(..., description="Human-readable description of the role")
    trigger: str = Field(
        ..., description="Event that triggers this agent (e.g., 'issue.created')"
    )
    goal: str = Field(..., description="The primary goal/output of this agent")
    tools: List[str] = Field(default_factory=list, description="List of allowed tools")
    system_prompt: str = Field(
        ..., description="The system prompt template for this agent"
    )
    engine: str = Field(
        default="gemini", description="CLI agent engine (gemini/claude)"
    )


class SchedulerConfig(BaseModel):
    roles: List[RoleTemplate] = Field(default_factory=list)
