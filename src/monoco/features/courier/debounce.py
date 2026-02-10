"""
Debounce Handler - Merge rapid consecutive messages.

Reduces noise from rapid message sequences by buffering and merging
messages within a time window before writing to the mailbox.
"""

import asyncio
import inspect
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from monoco.features.connector.protocol.schema import InboundMessage


@dataclass
class DebounceConfig:
    """Configuration for debounce behavior."""

    window_ms: int = 5000  # Buffer window in milliseconds
    max_wait_ms: int = 30000  # Maximum wait time before flush
    key_extractor: Optional[Callable[[InboundMessage], str]] = None


@dataclass
class MessageBuffer:
    """Buffer for debounced messages."""

    key: str
    messages: List[InboundMessage] = field(default_factory=list)
    first_arrival: Optional[float] = None
    last_arrival: Optional[float] = None
    timer_task: Optional[asyncio.Task] = None

    def add(self, message: InboundMessage) -> None:
        """Add a message to the buffer."""
        now = time.time()
        self.messages.append(message)
        if self.first_arrival is None:
            self.first_arrival = now
        self.last_arrival = now

    def should_flush(self, window_ms: int, max_wait_ms: int) -> bool:
        """Check if buffer should be flushed."""
        if not self.messages:
            return False
        now = time.time()
        elapsed_ms = (now - self.first_arrival) * 1000
        idle_ms = (now - self.last_arrival) * 1000
        # Flush if idle for window_ms or max_wait_ms exceeded
        return idle_ms >= window_ms / 1000 or elapsed_ms >= max_wait_ms / 1000

    def flush(self) -> List[InboundMessage]:
        """Get all messages and clear buffer."""
        messages = self.messages.copy()
        self.messages.clear()
        self.first_arrival = None
        self.last_arrival = None
        return messages


def default_key_extractor(message: InboundMessage) -> str:
    """
    Default key extractor for grouping messages.

    Groups by session_id:thread_key.
    """
    session_id = message.session.id if message.session else "unknown"
    thread_key = message.session.thread_key if message.session else None
    thread_part = thread_key or "_"
    return f"{session_id}:{thread_part}"


class DebounceHandler:
    """
    Handles debouncing of incoming messages.

    Buffers messages for a configurable window and flushes them
    when the window expires or max wait time is reached.
    """

    def __init__(
        self,
        config: DebounceConfig,
        flush_callback: Callable[[List[InboundMessage]], None],
    ):
        self.config = config
        self.flush_callback = flush_callback
        self._buffers: Dict[str, MessageBuffer] = {}
        self._key_extractor = config.key_extractor or default_key_extractor
        self._shutdown = False

    async def add(self, message: InboundMessage) -> Optional[List[InboundMessage]]:
        """
        Add a message to the debounce buffer.

        Returns the message list if flush is triggered, None otherwise.
        """
        if self._shutdown:
            return [message]

        key = self._key_extractor(message)

        if key not in self._buffers:
            self._buffers[key] = MessageBuffer(key=key)
            # Schedule a delayed flush check
            asyncio.create_task(self._schedule_flush(key))

        buffer = self._buffers[key]
        buffer.add(message)

        # Check immediate flush
        if buffer.should_flush(self.config.window_ms, self.config.max_wait_ms):
            return await self._flush_key(key)

        return None

    async def _schedule_flush(self, key: str) -> None:
        """Schedule a flush check after the window expires."""
        await asyncio.sleep(self.config.window_ms / 1000)
        await self._check_and_flush(key)

    async def _check_and_flush(self, key: str) -> None:
        """Check if buffer should be flushed and flush if needed."""
        buffer = self._buffers.get(key)
        if not buffer:
            return

        if buffer.should_flush(self.config.window_ms, self.config.max_wait_ms):
            await self._flush_key(key)

    async def _flush_key(self, key: str) -> List[InboundMessage]:
        """Flush a specific buffer."""
        buffer = self._buffers.pop(key, None)
        if not buffer:
            return []

        messages = buffer.flush()
        if messages:
            # Call the flush callback
            if inspect.iscoroutinefunction(self.flush_callback):
                await self.flush_callback(messages)
            else:
                self.flush_callback(messages)
        return messages

    async def flush_all(self) -> Dict[str, List[InboundMessage]]:
        """Flush all buffers immediately."""
        results = {}
        for key in list(self._buffers.keys()):
            messages = await self._flush_key(key)
            if messages:
                results[key] = messages
        return results

    def shutdown(self) -> None:
        """Mark handler as shutting down."""
        self._shutdown = True

    def get_pending_count(self) -> int:
        """Get total number of pending messages across all buffers."""
        return sum(len(b.messages) for b in self._buffers.values())

    def get_buffer_keys(self) -> List[str]:
        """Get list of active buffer keys."""
        return list(self._buffers.keys())
