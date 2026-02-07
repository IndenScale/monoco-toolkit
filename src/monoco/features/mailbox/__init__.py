"""
Mailbox Feature - Data layer for message management.

The Mailbox feature provides CLI commands for:
- Listing and reading messages (local filesystem operations)
- Creating outbound message drafts
- Claiming, completing, and failing messages (via Courier API)
"""

from .models import MailboxConfig, MessageFilter, MessageListItem, LockInfo
from .store import MailboxStore, get_mailbox_store
from .queries import MessageQuery, get_message_query
from .client import CourierClient, get_courier_client

__all__ = [
    # Models
    "MailboxConfig",
    "MessageFilter",
    "MessageListItem",
    "LockInfo",
    # Store
    "MailboxStore",
    "get_mailbox_store",
    # Queries
    "MessageQuery",
    "get_message_query",
    # Client
    "CourierClient",
    "get_courier_client",
]
