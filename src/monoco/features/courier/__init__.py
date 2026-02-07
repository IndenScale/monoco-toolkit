"""
Courier Feature - Message transport and service management layer.

The Courier is responsible for:
- Service lifecycle management (start, stop, restart, kill)
- Message transmission (sending outbound messages)
- Webhook receiving (inbound messages from external platforms)
- State management (locks, archive, retry)
- Debounce and merge logic for incoming messages
"""

from .service import CourierService, ServiceStatus
from .state import LockManager, MessageStateManager

__all__ = [
    "CourierService",
    "ServiceStatus",
    "LockManager",
    "MessageStateManager",
]