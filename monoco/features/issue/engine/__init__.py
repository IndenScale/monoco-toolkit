from .models import Transition, StateMachineConfig
from .config import DEFAULT_CONFIG
from .machine import StateMachine

def get_engine() -> StateMachine:
    return StateMachine(DEFAULT_CONFIG)
