"""
IM Core Management Classes (FEAT-0167).

Provides channel management, message storage, and message routing
for the IM system.
"""

from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from .models import (
    IMChannel,
    IMMessage,
    IMParticipant,
    IMAgentSession,
    IMWebhookConfig,
    IMStats,
    PlatformType,
    MessageStatus,
    ContentType,
)

logger = logging.getLogger(__name__)


class IMStorageError(Exception):
    """Base exception for IM storage errors."""
    pass


class ChannelNotFoundError(IMStorageError):
    """Raised when a channel is not found."""
    pass


class MessageNotFoundError(IMStorageError):
    """Raised when a message is not found."""
    pass


class IMChannelManager:
    """
    Manages IM channels (groups, private chats, threads).
    
    Responsibilities:
    - Channel CRUD operations
    - Participant management
    - Channel configuration
    """
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.channels_file = storage_dir / "channels.jsonl"
        self._channels: Dict[str, IMChannel] = {}
        self._loaded = False
    
    def _ensure_storage(self) -> None:
        """Ensure storage directory exists."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_channels(self) -> None:
        """Load all channels from storage."""
        if self._loaded:
            return
        
        self._ensure_storage()
        
        if not self.channels_file.exists():
            self._loaded = True
            return
        
        try:
            with open(self.channels_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        channel = IMChannel.model_validate(data)
                        self._channels[channel.channel_id] = channel
                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning(f"Failed to load channel: {e}")
        
        except Exception as e:
            logger.error(f"Error loading channels: {e}")
        
        self._loaded = True
    
    def _save_channels(self) -> None:
        """Save all channels to storage."""
        self._ensure_storage()
        
        with open(self.channels_file, "w", encoding="utf-8") as f:
            for channel in self._channels.values():
                f.write(json.dumps(channel.model_dump(), default=str) + "\n")
    
    def create_channel(
        self,
        channel_id: str,
        platform: PlatformType,
        channel_type: str = "group",
        name: Optional[str] = None,
        **kwargs
    ) -> IMChannel:
        """
        Create a new channel.
        
        Args:
            channel_id: Unique channel ID (platform-specific)
            platform: Platform type
            channel_type: Type of channel (group, private, thread)
            name: Optional channel name
            **kwargs: Additional channel attributes
        
        Returns:
            The created IMChannel
        """
        self._load_channels()
        
        if channel_id in self._channels:
            logger.warning(f"Channel {channel_id} already exists, returning existing")
            return self._channels[channel_id]
        
        channel = IMChannel(
            channel_id=channel_id,
            platform=platform,
            channel_type=channel_type,
            name=name,
            **kwargs
        )
        
        self._channels[channel_id] = channel
        self._save_channels()
        
        logger.info(f"Created channel {channel_id} ({platform.value})")
        return channel
    
    def get_channel(self, channel_id: str) -> Optional[IMChannel]:
        """Get a channel by ID."""
        self._load_channels()
        return self._channels.get(channel_id)
    
    def get_or_create_channel(
        self,
        channel_id: str,
        platform: PlatformType,
        **kwargs
    ) -> IMChannel:
        """Get existing channel or create new one."""
        channel = self.get_channel(channel_id)
        if channel:
            return channel
        return self.create_channel(channel_id, platform, **kwargs)
    
    def update_channel(self, channel_id: str, **updates) -> Optional[IMChannel]:
        """Update channel attributes."""
        self._load_channels()
        
        if channel_id not in self._channels:
            return None
        
        channel = self._channels[channel_id]
        data = channel.model_dump()
        data.update(updates)
        data["last_activity"] = datetime.now()
        
        self._channels[channel_id] = IMChannel.model_validate(data)
        self._save_channels()
        
        return self._channels[channel_id]
    
    def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel."""
        self._load_channels()
        
        if channel_id not in self._channels:
            return False
        
        del self._channels[channel_id]
        self._save_channels()
        
        logger.info(f"Deleted channel {channel_id}")
        return True
    
    def list_channels(
        self,
        platform: Optional[PlatformType] = None,
        project_binding: Optional[str] = None
    ) -> List[IMChannel]:
        """List channels with optional filters."""
        self._load_channels()
        
        channels = list(self._channels.values())
        
        if platform:
            channels = [c for c in channels if c.platform == platform]
        
        if project_binding:
            channels = [c for c in channels if c.project_binding == project_binding]
        
        return sorted(channels, key=lambda c: c.last_activity, reverse=True)
    
    def add_participant(self, channel_id: str, participant: IMParticipant) -> bool:
        """Add a participant to a channel."""
        self._load_channels()
        
        if channel_id not in self._channels:
            return False
        
        channel = self._channels[channel_id]
        channel.add_participant(participant)
        channel.update_activity()
        
        self._save_channels()
        return True
    
    def remove_participant(self, channel_id: str, participant_id: str) -> bool:
        """Remove a participant from a channel."""
        self._load_channels()
        
        if channel_id not in self._channels:
            return False
        
        channel = self._channels[channel_id]
        channel.remove_participant(participant_id)
        channel.update_activity()
        
        self._save_channels()
        return True
    
    def bind_project(self, channel_id: str, project_path: str) -> bool:
        """Bind a channel to a project."""
        return self.update_channel(channel_id, project_binding=project_path) is not None
    
    def unbind_project(self, channel_id: str) -> bool:
        """Unbind a channel from a project."""
        return self.update_channel(channel_id, project_binding=None) is not None


class MessageStore:
    """
    Stores and manages IM messages.
    
    Uses JSONL format for append-only message storage.
    Messages are stored per-channel for efficient querying.
    """
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.messages_dir = storage_dir / "messages"
        self._message_cache: Dict[str, IMMessage] = {}
        self._cache_size = 1000
    
    def _ensure_storage(self) -> None:
        """Ensure storage directory exists."""
        self.messages_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_channel_file(self, channel_id: str) -> Path:
        """Get the message file path for a channel."""
        # Hash channel_id to avoid filesystem issues
        safe_name = channel_id.replace("/", "_").replace("\\", "_")
        return self.messages_dir / f"{safe_name}.jsonl"
    
    def save_message(self, message: IMMessage) -> None:
        """
        Save a message to storage.
        
        Appends to the channel's message file.
        """
        self._ensure_storage()
        
        channel_file = self._get_channel_file(message.channel_id)
        
        with open(channel_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(message.model_dump(), default=str) + "\n")
        
        # Update cache
        self._message_cache[message.message_id] = message
        
        # Trim cache if needed
        if len(self._message_cache) > self._cache_size:
            # Remove oldest 20% of cache
            remove_count = self._cache_size // 5
            keys = list(self._message_cache.keys())[:remove_count]
            for key in keys:
                del self._message_cache[key]
        
        logger.debug(f"Saved message {message.message_id} to {channel_file}")
    
    def get_message(self, message_id: str) -> Optional[IMMessage]:
        """Get a message by ID (uses cache first)."""
        # Check cache first
        if message_id in self._message_cache:
            return self._message_cache[message_id]
        
        # Search all channel files
        if not self.messages_dir.exists():
            return None
        
        for channel_file in self.messages_dir.glob("*.jsonl"):
            try:
                with open(channel_file, "r", encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line.strip())
                        if data.get("message_id") == message_id:
                            message = IMMessage.model_validate(data)
                            self._message_cache[message_id] = message
                            return message
            except Exception as e:
                logger.warning(f"Error reading {channel_file}: {e}")
        
        return None
    
    def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 100,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        status: Optional[MessageStatus] = None
    ) -> List[IMMessage]:
        """
        Get messages for a channel.
        
        Args:
            channel_id: Channel ID
            limit: Maximum number of messages to return
            before: Only return messages before this timestamp
            after: Only return messages after this timestamp
            status: Filter by message status
        """
        channel_file = self._get_channel_file(channel_id)
        
        if not channel_file.exists():
            return []
        
        messages = []
        
        try:
            with open(channel_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        
                        # Apply filters
                        timestamp = datetime.fromisoformat(data["timestamp"])
                        
                        if before and timestamp >= before:
                            continue
                        if after and timestamp <= after:
                            continue
                        if status and data.get("status") != status.value:
                            continue
                        
                        messages.append(IMMessage.model_validate(data))
                    except Exception as e:
                        logger.warning(f"Failed to parse message: {e}")
        
        except Exception as e:
            logger.error(f"Error reading messages: {e}")
        
        # Sort by timestamp descending, then limit
        messages.sort(key=lambda m: m.timestamp, reverse=True)
        return messages[:limit]
    
    def update_message_status(
        self,
        message_id: str,
        status: MessageStatus,
        step: Optional[str] = None
    ) -> bool:
        """
        Update message status.
        
        Note: This rewrites the entire channel file. For high-volume
        scenarios, consider using a proper database.
        """
        message = self.get_message(message_id)
        if not message:
            return False
        
        message.status = status
        if step:
            from .models import ProcessingStep
            message.processing_log.append(ProcessingStep(
                step=step,
                status="completed" if status != MessageStatus.ERROR else "failed"
            ))
        
        # Rewrite channel file
        channel_file = self._get_channel_file(message.channel_id)
        
        if not channel_file.exists():
            return False
        
        try:
            # Read all messages
            messages = []
            with open(channel_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    if data["message_id"] == message_id:
                        messages.append(message.model_dump())
                    else:
                        messages.append(data)
            
            # Write back
            with open(channel_file, "w", encoding="utf-8") as f:
                for msg_data in messages:
                    f.write(json.dumps(msg_data, default=str) + "\n")
            
            # Update cache
            self._message_cache[message_id] = message
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating message status: {e}")
            return False
    
    def get_thread_messages(self, thread_id: str) -> List[IMMessage]:
        """Get all messages in a thread."""
        messages = []
        
        if not self.messages_dir.exists():
            return messages
        
        for channel_file in self.messages_dir.glob("*.jsonl"):
            try:
                with open(channel_file, "r", encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line.strip())
                        if data.get("thread_id") == thread_id:
                            messages.append(IMMessage.model_validate(data))
            except Exception as e:
                logger.warning(f"Error reading {channel_file}: {e}")
        
        messages.sort(key=lambda m: m.timestamp)
        return messages
    
    def get_message_context(
        self,
        message_id: str,
        window_size: int = 10
    ) -> List[IMMessage]:
        """
        Get context messages around a specific message.
        
        Returns messages before and after the target message.
        """
        message = self.get_message(message_id)
        if not message:
            return []
        
        # Get all messages in channel
        channel_messages = self.get_channel_messages(
            message.channel_id,
            limit=window_size * 2
        )
        
        # Find index of target message
        try:
            idx = next(
                i for i, m in enumerate(channel_messages)
                if m.message_id == message_id
            )
        except StopIteration:
            return []
        
        # Return context window
        start = max(0, idx - window_size // 2)
        end = min(len(channel_messages), idx + window_size // 2 + 1)
        
        return channel_messages[start:end]


class IMRouter:
    """
    Routes incoming IM messages to appropriate handlers.
    
    Makes routing decisions based on:
    - Channel configuration
    - Message content
    - Agent availability
    """
    
    def __init__(
        self,
        channel_manager: IMChannelManager,
        message_store: MessageStore
    ):
        self.channel_manager = channel_manager
        self.message_store = message_store
        self._handlers: Dict[str, Callable[[IMMessage], Any]] = {}
        self._default_handler: Optional[Callable[[IMMessage], Any]] = None
    
    def register_handler(
        self,
        handler_id: str,
        handler: Callable[[IMMessage], Any]
    ) -> None:
        """Register a message handler."""
        self._handlers[handler_id] = handler
        logger.debug(f"Registered handler: {handler_id}")
    
    def unregister_handler(self, handler_id: str) -> None:
        """Unregister a message handler."""
        if handler_id in self._handlers:
            del self._handlers[handler_id]
    
    def set_default_handler(self, handler: Callable[[IMMessage], Any]) -> None:
        """Set the default handler for unrouted messages."""
        self._default_handler = handler
    
    def route(self, message: IMMessage) -> Optional[str]:
        """
        Route a message to the appropriate handler.
        
        Returns:
            Handler ID if routed, None otherwise
        """
        channel = self.channel_manager.get_channel(message.channel_id)
        
        if not channel:
            logger.warning(f"Unknown channel: {message.channel_id}")
            return None
        
        # Check if auto-reply is enabled
        if not channel.auto_reply:
            logger.debug(f"Auto-reply disabled for channel {channel.channel_id}")
            return None
        
        # Check if mention is required
        if channel.require_mention:
            # Check if any agent is mentioned
            agent_mentioned = False
            for participant in channel.participants:
                if participant.participant_type.value == "agent":
                    if participant.participant_id in message.mentions:
                        agent_mentioned = True
                        break
            
            if not agent_mentioned and not message.mention_all:
                logger.debug(f"No agent mentioned in message {message.message_id}")
                return None
        
        # Determine handler based on message type and content
        handler_id = self._determine_handler(message, channel)
        
        if handler_id and handler_id in self._handlers:
            try:
                self._handlers[handler_id](message)
                return handler_id
            except Exception as e:
                logger.error(f"Handler error for {handler_id}: {e}")
                return None
        
        # Use default handler
        if self._default_handler:
            try:
                self._default_handler(message)
                return "default"
            except Exception as e:
                logger.error(f"Default handler error: {e}")
        
        return None
    
    def _determine_handler(
        self,
        message: IMMessage,
        channel: IMChannel
    ) -> Optional[str]:
        """
        Determine which handler should process this message.
        
        Override this method for custom routing logic.
        """
        # Check for specific keywords or patterns
        text = message.content.text or ""
        
        # Route to specific agents based on keywords
        if any(keyword in text.lower() for keyword in ["review", "审阅", "审核"]):
            return "reviewer"
        
        if any(keyword in text.lower() for keyword in ["plan", "规划", "计划", "设计"]):
            return "principal"
        
        if any(keyword in text.lower() for keyword in ["fix", "bug", "错误", "修复"]):
            return "engineer"
        
        # Use channel's default agent
        if channel.default_agent:
            return channel.default_agent
        
        return None


class IMAgentSessionManager:
    """
    Manages Agent sessions bound to IM channels.
    
    Tracks active Agent interactions with channels.
    """
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.sessions_dir = storage_dir / "sessions"
        self._active_sessions: Dict[str, IMAgentSession] = {}
        self._loaded = False
    
    def _ensure_storage(self) -> None:
        """Ensure storage directory exists."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"im-{secrets.token_hex(8)}"
    
    def create_session(
        self,
        channel_id: str,
        agent_role: str,
        linked_issue_id: Optional[str] = None,
        linked_task_id: Optional[str] = None
    ) -> IMAgentSession:
        """Create a new Agent session."""
        self._ensure_storage()
        
        session_id = self._generate_session_id()
        session = IMAgentSession(
            session_id=session_id,
            channel_id=channel_id,
            agent_role=agent_role,
            linked_issue_id=linked_issue_id,
            linked_task_id=linked_task_id,
        )
        
        self._active_sessions[session_id] = session
        self._save_session(session)
        
        logger.info(f"Created session {session_id} for channel {channel_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[IMAgentSession]:
        """Get a session by ID."""
        # Check active sessions first
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
        
        # Load from disk
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            try:
                data = json.loads(session_file.read_text(encoding="utf-8"))
                session = IMAgentSession.model_validate(data)
                self._active_sessions[session_id] = session
                return session
            except Exception as e:
                logger.error(f"Error loading session: {e}")
        
        return None
    
    def get_channel_sessions(self, channel_id: str) -> List[IMAgentSession]:
        """Get all sessions for a channel."""
        return [
            s for s in self._active_sessions.values()
            if s.channel_id == channel_id and s.status == "active"
        ]
    
    def update_session(self, session: IMAgentSession) -> None:
        """Update a session."""
        session.update_activity()
        self._active_sessions[session.session_id] = session
        self._save_session(session)
    
    def _save_session(self, session: IMAgentSession) -> None:
        """Save a session to disk."""
        self._ensure_storage()
        
        session_file = self.sessions_dir / f"{session.session_id}.json"
        session_file.write_text(
            json.dumps(session.model_dump(), default=str),
            encoding="utf-8"
        )
    
    def end_session(
        self,
        session_id: str,
        status: str = "completed",
        result_summary: Optional[str] = None
    ) -> bool:
        """End a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.end_session(status)
        if result_summary:
            session.result_summary = result_summary
        
        self._save_session(session)
        
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        
        logger.info(f"Ended session {session_id} with status {status}")
        return True
    
    def add_message_to_session(self, session_id: str, message_id: str) -> bool:
        """Add a message to a session's history."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.message_ids.append(message_id)
        session.context_message_count = len(session.message_ids)
        self.update_session(session)
        
        return True
    
    def cleanup_stale_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions that have been inactive for too long."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        stale_sessions = [
            sid for sid, s in self._active_sessions.items()
            if s.last_activity < cutoff
        ]
        
        for sid in stale_sessions:
            self.end_session(sid, status="completed", result_summary="Session expired due to inactivity")
        
        return len(stale_sessions)


class IMManager:
    """
    Main entry point for IM system.
    
    Provides unified access to all IM functionality.
    """
    
    def __init__(self, project_root: Path):
        self.storage_dir = project_root / ".monoco" / "im"
        self.channels = IMChannelManager(self.storage_dir)
        self.messages = MessageStore(self.storage_dir)
        self.router = IMRouter(self.channels, self.messages)
        self.sessions = IMAgentSessionManager(self.storage_dir)
        
        # Ensure directory structure
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Initialize storage directory structure."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        (self.storage_dir / "messages").mkdir(exist_ok=True)
        (self.storage_dir / "sessions").mkdir(exist_ok=True)
        (self.storage_dir / "webhooks").mkdir(exist_ok=True)
        
        logger.info(f"IM storage initialized at {self.storage_dir}")
    
    def get_stats(self) -> IMStats:
        """Get IM system statistics."""
        channels = self.channels.list_channels()
        
        return IMStats(
            total_channels=len(channels),
            active_channels=len([c for c in channels if c.auto_reply]),
            active_sessions=len(self.sessions._active_sessions),
        )
