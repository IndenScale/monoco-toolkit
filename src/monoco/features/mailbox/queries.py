"""
Mailbox Queries - Query engine for message retrieval.

This module provides high-level query capabilities for the mailbox.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from monoco.features.connector.protocol.schema import (
    InboundMessage,
    Provider,
    MessageStatus,
)

from .models import (
    MailboxConfig,
    MessageFilter,
    MessageListItem,
    ListFormat,
)
from .store import MailboxStore


class MessageQuery:
    """
    Query engine for mailbox messages.

    Provides high-level query capabilities with filtering and formatting.
    """

    def __init__(self, store: MailboxStore):
        self.store = store

    def list_messages(
        self,
        filter: Optional[MessageFilter] = None,
        format: ListFormat = ListFormat.TABLE,
    ) -> List[MessageListItem]:
        """
        List messages with filtering.

        Args:
            filter: Optional filter criteria
            format: Output format (affects what data is retrieved)

        Returns:
            List of message summary items
        """
        if filter is None:
            filter = MessageFilter()

        # Get all inbound messages
        messages = self.store.list_inbound_messages(
            provider=filter.provider.value if filter.provider else None,
            since=filter.since,
        )

        # Get locks for status filtering
        locks = self.store.get_locks()

        results = []
        for file_path, message in messages:
            # Get status from locks
            lock = locks.get(message.id)
            if lock and not lock.is_expired:
                status = lock.status
            else:
                status = MessageStatus.NEW

            # Apply status filter
            if filter.status and status != filter.status:
                continue

            # Apply general filter
            if not filter.matches(message):
                continue

            # Get sender info
            sender = message.get_sender()
            from_name = sender.name if sender else "Unknown"
            from_id = sender.id if sender else "unknown"

            item = MessageListItem(
                id=message.id,
                provider=message.provider,
                from_name=from_name,
                from_id=from_id,
                status=status,
                timestamp=message.timestamp,
                preview=message.get_preview(),
                session_name=message.session.name,
                correlation_id=message.correlation_id,
                artifact_count=len(message.artifacts) if message.artifacts else 0,
            )
            results.append(item)

        # Sort by timestamp descending
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results

    def get_message(self, message_id: str) -> Optional[InboundMessage]:
        """
        Get a single message by ID.

        Args:
            message_id: Message identifier

        Returns:
            InboundMessage if found, None otherwise
        """
        return self.store.read_inbound_message(message_id)

    def find_by_correlation(
        self,
        correlation_id: str,
        include_archived: bool = False,
    ) -> List[InboundMessage]:
        """
        Find all messages with a given correlation ID.

        Args:
            correlation_id: Correlation identifier
            include_archived: Whether to include archived messages

        Returns:
            List of matching messages
        """
        results = []

        # Search inbound
        for file_path, message in self.store.list_inbound_messages():
            if message.correlation_id == correlation_id:
                results.append(message)

        # TODO: Search archive if requested

        # Sort by timestamp
        results.sort(key=lambda x: x.timestamp)
        return results

    def parse_since(self, since_str: str) -> datetime:
        """
        Parse a 'since' string into a datetime.

        Supports formats like:
        - "2h" -> 2 hours ago
        - "1d" -> 1 day ago
        - "30m" -> 30 minutes ago
        - ISO8601 timestamp

        Args:
            since_str: Time specification string

        Returns:
            Datetime object
        """
        since_str = since_str.strip().lower()

        # Relative time
        if since_str.endswith("h"):
            try:
                hours = int(since_str[:-1])
                return datetime.utcnow() - timedelta(hours=hours)
            except ValueError:
                pass

        if since_str.endswith("d"):
            try:
                days = int(since_str[:-1])
                return datetime.utcnow() - timedelta(days=days)
            except ValueError:
                pass

        if since_str.endswith("m"):
            try:
                minutes = int(since_str[:-1])
                return datetime.utcnow() - timedelta(minutes=minutes)
            except ValueError:
                pass

        # Try ISO8601
        try:
            return datetime.fromisoformat(since_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        # Default to 24 hours ago if parsing fails
        return datetime.utcnow() - timedelta(days=1)


# Global query instance
_query: Optional[MessageQuery] = None


def get_message_query(store: Optional[MailboxStore] = None) -> MessageQuery:
    """
    Get or create the global message query instance.

    Args:
        store: Optional store instance (required on first call)

    Returns:
        MessageQuery instance
    """
    global _query
    if _query is None:
        if store is None:
            raise ValueError("Store required for initial query creation")
        _query = MessageQuery(store)
    return _query
