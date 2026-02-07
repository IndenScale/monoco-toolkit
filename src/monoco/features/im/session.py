"""
IM Agent Session Management (FEAT-0170).

Provides session lifecycle management for Agent-IM interactions,
including context window management, streaming output, and session state tracking.
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable, AsyncIterator
from pathlib import Path

from .models import (
    IMMessage,
    IMChannel,
    IMAgentSession,
    MessageStatus,
    PlatformType,
    ContentType,
    MessageContent,
)
from .core import MessageStore, IMChannelManager

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """
    Session lifecycle states.
    
    States:
        IDLE: Session created, waiting for first message
        PROCESSING: Agent is processing a request
        STREAMING: Agent is streaming output to IM
        COMPLETED: Session completed successfully
        ERROR: Session encountered an error
        STOPPED: Session was manually stopped
    """
    IDLE = "idle"
    PROCESSING = "processing"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"


class CommandType(Enum):
    """Supported IM commands."""
    ARCHITECT = "/architect"
    ENGINEER = "/engineer"
    REVIEWER = "/reviewer"
    PLANNER = "/planner"
    MEMO = "/memo"
    ISSUE = "/issue"
    STATUS = "/status"
    STOP = "/stop"
    HELP = "/help"


@dataclass
class Command:
    """Parsed IM command."""
    command_type: CommandType
    args: List[str] = field(default_factory=list)
    raw_text: str = ""
    
    @property
    def prompt(self) -> str:
        """Get the prompt part (everything after command)."""
        parts = self.raw_text.split(None, 1)
        return parts[1] if len(parts) > 1 else ""
    
    @property
    def target_id(self) -> Optional[str]:
        """Get target ID (first arg, usually issue_id or PR URL)."""
        return self.args[0] if self.args else None


@dataclass
class StreamChunk:
    """A chunk of streamed output."""
    content: str
    is_final: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SessionContext:
    """Context for an Agent session."""
    messages: List[IMMessage] = field(default_factory=list)
    window_size: int = 10
    
    def add_message(self, message: IMMessage) -> None:
        """Add a message to context, maintaining window size."""
        self.messages.append(message)
        # Trim to window size (sliding window)
        if len(self.messages) > self.window_size:
            self.messages = self.messages[-self.window_size:]
    
    def to_prompt(self) -> str:
        """Convert context to prompt format for Agent."""
        lines = []
        for msg in self.messages:
            sender = msg.sender.display_name or msg.sender.participant_id
            text = msg.content.text or ""
            lines.append(f"{sender}: {text}")
        return "\n".join(lines)


class IMAgentSessionController:
    """
    Controller for an Agent session bound to an IM channel.
    
    Manages the interaction between an Agent and an IM channel,
    including state transitions, streaming output, and context management.
    """
    
    def __init__(
        self,
        session_id: str,
        channel_id: str,
        agent_role: str,
        message_store: MessageStore,
        channel_manager: IMChannelManager,
        context_window: int = 10,
        timeout_minutes: int = 30,
    ):
        self.session_id = session_id
        self.channel_id = channel_id
        self.agent_role = agent_role
        self.message_store = message_store
        self.channel_manager = channel_manager
        self.context_window = context_window
        self.timeout_minutes = timeout_minutes
        
        # State
        self.state = SessionState.IDLE
        self._state_lock = asyncio.Lock()
        
        # Context
        self.context = SessionContext(window_size=context_window)
        
        # Timestamps
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.completed_at: Optional[datetime] = None
        
        # Streaming
        self._stream_queue: Optional[asyncio.Queue[StreamChunk]] = None
        self._stream_task: Optional[asyncio.Task] = None
        self._stream_callbacks: List[Callable[[StreamChunk], None]] = []
        
        # Linked entities
        self.linked_issue_id: Optional[str] = None
        self.linked_task_id: Optional[str] = None
        
        # Result
        self.result_summary: Optional[str] = None
        self.message_count = 0
        
        logger.info(f"[Session {session_id}] Created for channel {channel_id} with role {agent_role}")
    
    async def transition_to(self, new_state: SessionState) -> None:
        """Transition to a new state."""
        async with self._state_lock:
            old_state = self.state
            self.state = new_state
            self.last_activity = datetime.now()
            logger.info(f"[Session {self.session_id}] {old_state.value} -> {new_state.value}")
    
    def is_active(self) -> bool:
        """Check if session is still active."""
        return self.state in (
            SessionState.IDLE,
            SessionState.PROCESSING,
            SessionState.STREAMING,
        )
    
    def is_expired(self) -> bool:
        """Check if session has expired due to inactivity."""
        if self.completed_at:
            return True
        cutoff = datetime.now() - timedelta(minutes=self.timeout_minutes)
        return self.last_activity < cutoff
    
    async def add_message(self, message: IMMessage) -> None:
        """Add a message to session context."""
        self.context.add_message(message)
        self.message_count += 1
        self.last_activity = datetime.now()
        
        # Persist message association
        await self._persist_message(message.message_id)
    
    async def _persist_message(self, message_id: str) -> None:
        """Persist message association to storage."""
        # This would update the session file with the new message ID
        pass  # Implementation depends on storage backend
    
    # --- Streaming Output ---
    
    async def start_streaming(self) -> asyncio.Queue[StreamChunk]:
        """Start streaming mode and return the queue."""
        await self.transition_to(SessionState.STREAMING)
        self._stream_queue = asyncio.Queue()
        return self._stream_queue
    
    async def stream_chunk(self, content: str, is_final: bool = False) -> None:
        """Send a chunk of streamed content."""
        if self._stream_queue is None:
            return
        
        chunk = StreamChunk(content=content, is_final=is_final)
        await self._stream_queue.put(chunk)
        
        # Notify callbacks
        for callback in self._stream_callbacks:
            try:
                callback(chunk)
            except Exception as e:
                logger.warning(f"[Session {self.session_id}] Stream callback error: {e}")
    
    def add_stream_callback(self, callback: Callable[[StreamChunk], None]) -> None:
        """Add a callback for stream chunks."""
        self._stream_callbacks.append(callback)
    
    def remove_stream_callback(self, callback: Callable[[StreamChunk], None]) -> None:
        """Remove a stream callback."""
        if callback in self._stream_callbacks:
            self._stream_callbacks.remove(callback)
    
    async def end_streaming(self, summary: Optional[str] = None) -> None:
        """End streaming mode."""
        if self._stream_queue:
            await self._stream_queue.put(StreamChunk(content="", is_final=True))
        
        if summary:
            self.result_summary = summary
        
        await self.transition_to(SessionState.COMPLETED)
    
    # --- Session Lifecycle ---
    
    async def complete(self, summary: Optional[str] = None) -> None:
        """Mark session as completed."""
        self.result_summary = summary
        self.completed_at = datetime.now()
        await self.transition_to(SessionState.COMPLETED)
    
    async def fail(self, reason: str) -> None:
        """Mark session as failed."""
        self.result_summary = f"Failed: {reason}"
        self.completed_at = datetime.now()
        await self.transition_to(SessionState.ERROR)
    
    async def stop(self) -> None:
        """Stop the session."""
        self.completed_at = datetime.now()
        await self.transition_to(SessionState.STOPPED)
    
    def to_model(self) -> IMAgentSession:
        """Convert to IMAgentSession model."""
        return IMAgentSession(
            session_id=self.session_id,
            channel_id=self.channel_id,
            agent_role=self.agent_role,
            status=self._state_to_status(),
            message_ids=[m.message_id for m in self.context.messages],
            context_message_count=self.message_count,
            linked_issue_id=self.linked_issue_id,
            linked_task_id=self.linked_task_id,
            started_at=self.created_at,
            last_activity=self.last_activity,
            ended_at=self.completed_at,
            result_summary=self.result_summary,
        )
    
    def _state_to_status(self) -> str:
        """Convert SessionState to IMAgentSession status."""
        mapping = {
            SessionState.IDLE: "active",
            SessionState.PROCESSING: "active",
            SessionState.STREAMING: "active",
            SessionState.COMPLETED: "completed",
            SessionState.ERROR: "error",
            SessionState.STOPPED: "completed",
        }
        return mapping.get(self.state, "active")


class IMAgentSessionManager:
    """
    Manages all IM Agent sessions.
    
    Provides session CRUD operations, cleanup of stale sessions,
    and lookup by channel or session ID.
    """
    
    def __init__(
        self,
        storage_dir: Path,
        message_store: MessageStore,
        channel_manager: IMChannelManager,
    ):
        self.storage_dir = storage_dir
        self.sessions_dir = storage_dir / "sessions"
        self.message_store = message_store
        self.channel_manager = channel_manager
        
        # Active sessions
        self._sessions: Dict[str, IMAgentSessionController] = {}
        
        # Channel -> active session mapping (one active session per channel)
        self._channel_sessions: Dict[str, str] = {}
        
        # Ensure storage
        self._ensure_storage()
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    def _ensure_storage(self) -> None:
        """Ensure storage directory exists."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"im-{secrets.token_hex(8)}"
    
    async def start(self) -> None:
        """Start the session manager."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("IMAgentSessionManager started")
    
    async def stop(self) -> None:
        """Stop the session manager."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Complete all active sessions
        for session in list(self._sessions.values()):
            if session.is_active():
                await session.stop()
        
        logger.info("IMAgentSessionManager stopped")
    
    async def create_session(
        self,
        channel_id: str,
        agent_role: str,
        context_window: int = 10,
        linked_issue_id: Optional[str] = None,
        linked_task_id: Optional[str] = None,
        replace_existing: bool = True,
    ) -> IMAgentSessionController:
        """
        Create a new Agent session.
        
        Args:
            channel_id: The IM channel ID
            agent_role: Agent role (e.g., 'architect', 'engineer')
            context_window: Number of messages to keep in context
            linked_issue_id: Optional linked issue ID
            linked_task_id: Optional linked task ID
            replace_existing: If True, stop existing session for this channel
        
        Returns:
            The created session controller
        """
        # Check if channel already has an active session
        if channel_id in self._channel_sessions and replace_existing:
            old_session_id = self._channel_sessions[channel_id]
            if old_session_id in self._sessions:
                old_session = self._sessions[old_session_id]
                if old_session.is_active():
                    logger.info(f"[Channel {channel_id}] Stopping existing session {old_session_id}")
                    await old_session.stop()
        
        session_id = self._generate_session_id()
        
        session = IMAgentSessionController(
            session_id=session_id,
            channel_id=channel_id,
            agent_role=agent_role,
            message_store=self.message_store,
            channel_manager=self.channel_manager,
            context_window=context_window,
        )
        
        session.linked_issue_id = linked_issue_id
        session.linked_task_id = linked_task_id
        
        self._sessions[session_id] = session
        self._channel_sessions[channel_id] = session_id
        
        await self._save_session(session)
        
        logger.info(f"[Session {session_id}] Created for channel {channel_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[IMAgentSessionController]:
        """Get a session by ID."""
        return self._sessions.get(session_id)
    
    def get_channel_session(self, channel_id: str) -> Optional[IMAgentSessionController]:
        """Get the active session for a channel."""
        session_id = self._channel_sessions.get(channel_id)
        if session_id:
            return self._sessions.get(session_id)
        return None
    
    def list_sessions(
        self,
        channel_id: Optional[str] = None,
        active_only: bool = False,
    ) -> List[IMAgentSessionController]:
        """List sessions with optional filters."""
        sessions = list(self._sessions.values())
        
        if channel_id:
            sessions = [s for s in sessions if s.channel_id == channel_id]
        
        if active_only:
            sessions = [s for s in sessions if s.is_active()]
        
        return sessions
    
    async def end_session(
        self,
        session_id: str,
        status: str = "completed",
        summary: Optional[str] = None,
    ) -> bool:
        """End a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        if status == "completed":
            await session.complete(summary)
        elif status == "error":
            await session.fail(summary or "Unknown error")
        else:
            await session.stop()
        
        await self._save_session(session)
        
        # Clean up channel mapping if this was the active session
        if self._channel_sessions.get(session.channel_id) == session_id:
            del self._channel_sessions[session.channel_id]
        
        return True
    
    async def _save_session(self, session: IMAgentSessionController) -> None:
        """Save session to disk."""
        self._ensure_storage()
        
        session_file = self.sessions_dir / f"{session.session_id}.json"
        model = session.to_model()
        
        import json
        session_file.write_text(
            json.dumps(model.model_dump(), default=str),
            encoding="utf-8"
        )
    
    async def _cleanup_loop(self) -> None:
        """Background loop to clean up stale sessions."""
        while self._running:
            try:
                await self._cleanup_stale_sessions()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_stale_sessions(self) -> int:
        """Clean up expired sessions."""
        expired = [
            sid for sid, s in self._sessions.items()
            if s.is_expired()
        ]
        
        for sid in expired:
            session = self._sessions[sid]
            logger.info(f"[Session {sid}] Cleaning up expired session")
            await session.stop()
            
            # Clean up channel mapping
            if self._channel_sessions.get(session.channel_id) == sid:
                del self._channel_sessions[session.channel_id]
        
        return len(expired)


class CommandParser:
    """Parser for IM commands."""
    
    COMMAND_PREFIX = "/"
    
    @classmethod
    def parse(cls, text: str) -> Optional[Command]:
        """
        Parse text into a Command.
        
        Args:
            text: The message text
        
        Returns:
            Command if text is a command, None otherwise
        """
        if not text or not text.strip().startswith(cls.COMMAND_PREFIX):
            return None
        
        text = text.strip()
        parts = text.split()
        if not parts:
            return None
        
        cmd_str = parts[0].lower()
        args = parts[1:]
        
        # Find command type
        try:
            cmd_type = CommandType(cmd_str)
        except ValueError:
            # Unknown command
            logger.debug(f"Unknown command: {cmd_str}")
            return None
        
        return Command(
            command_type=cmd_type,
            args=args,
            raw_text=text,
        )
    
    @classmethod
    def is_command(cls, text: str) -> bool:
        """Check if text is a command."""
        return text and text.strip().startswith(cls.COMMAND_PREFIX)
    
    @classmethod
    def get_available_commands(cls) -> Dict[str, str]:
        """Get available commands with descriptions."""
        return {
            "/architect [prompt]": "启动 Architect Agent 进行架构设计",
            "/engineer [issue_id]": "启动 Engineer Agent 处理 Issue",
            "/reviewer [pr_url]": "启动 Reviewer Agent 审查代码",
            "/planner [prompt]": "启动 Planner Agent 进行规划",
            "/memo [content]": "创建 Memo",
            "/issue [title]": "创建 Issue",
            "/status": "查看当前会话状态",
            "/stop": "停止当前 Agent",
            "/help": "显示帮助信息",
        }
