from typing import List
from pydantic import BaseModel, Field


class RoleTemplate(BaseModel):
    name: str = Field(
        ..., description="Unique identifier for the role (e.g., 'principal')"
    )
    description: str = Field(..., description="Human-readable description of the role")
    trigger: str = Field(
        ..., description="Event that triggers this agent (e.g., 'issue.created')"
    )
    goal: str = Field(..., description="The primary goal/output of this agent")
    system_prompt: str = Field(
        ..., description="The system prompt template for this agent"
    )
    engine: str = Field(
        default="claude", description="CLI agent engine (claude/gemini)"
    )


class AgentRoleConfig(BaseModel):
    roles: List[RoleTemplate] = Field(default_factory=list)


# Backward compatibility alias
SchedulerConfig = AgentRoleConfig
