from typing import List, Optional
from pydantic import BaseModel


class Transition(BaseModel):
    name: str
    label: str
    icon: Optional[str] = None
    from_status: Optional[str] = None  # None means any
    from_stage: Optional[str] = None  # None means any
    to_status: str
    to_stage: Optional[str] = None
    required_solution: Optional[str] = None
    description: str = ""
    command_template: Optional[str] = None


class StateMachineConfig(BaseModel):
    transitions: List[Transition]
    # We can add more config like default stages for statuses etc.
