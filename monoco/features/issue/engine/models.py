from typing import List, Optional, Any
from pydantic import BaseModel
from ..models import IssueStatus, IssueStage, IssueSolution

class Transition(BaseModel):
    name: str
    label: str
    icon: Optional[str] = None
    from_status: Optional[IssueStatus] = None  # None means any
    from_stage: Optional[IssueStage] = None    # None means any
    to_status: IssueStatus
    to_stage: Optional[IssueStage] = None
    required_solution: Optional[IssueSolution] = None
    description: str = ""
    command_template: Optional[str] = None

class StateMachineConfig(BaseModel):
    transitions: List[Transition]
    # We can add more config like default stages for statuses etc.
