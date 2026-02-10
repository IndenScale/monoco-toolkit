"""Ralph Loop - Agent Session Relay System.

When the current Agent hits a bottleneck (insufficient context, local optimum trap,
need for fresh perspective), launch a successor Agent to continue the Issue.
"""

from .core import (
    relay_issue,
    get_relay_status,
    clear_relay_status,
    prepare_last_words,
    spawn_successor_agent,
)
from .models import RalphRelay, RelayStatus, LastWords

__all__ = [
    "relay_issue",
    "get_relay_status",
    "clear_relay_status",
    "prepare_last_words",
    "spawn_successor_agent",
    "RalphRelay",
    "RelayStatus",
    "LastWords",
]
