"""
IM Message and Command Handlers (FEAT-0170).

Provides message routing, command parsing, and Agent integration
for IM-based interactions.
"""

from __future__ import annotations

import asyncio
import logging
import json
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .models import (
    IMMessage,
    IMChannel,
    IMParticipant,
    PlatformType,
    MessageStatus,
    ContentType,
    MessageContent,
    ParticipantType,
)
from .core import IMManager, MessageStore, IMChannelManager
from .session import (
    IMAgentSessionController,
    IMAgentSessionManager,
    CommandParser,
    Command,
    CommandType,
    SessionState,
    StreamChunk,
)

logger = logging.getLogger(__name__)


@dataclass
class HandlerResult:
    """Result of handling a message."""
    success: bool
    message: Optional[str] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class IMAgentTrigger:
    """
    Determines when to trigger an Agent session.
    
    Checks message content, mentions, and channel configuration
    to decide if an Agent should be invoked.
    """
    
    def __init__(self, bot_user_id: Optional[str] = None):
        self.bot_user_id = bot_user_id
        self._trigger_keywords: List[str] = [
            "agent", "ai", "bot", "助手", "帮助",
            "create issue", "创建 issue", "review", "审阅",
        ]
    
    def should_trigger(self, message: IMMessage, channel: IMChannel) -> bool:
        """
        Determine if Agent should be triggered.
        
        Returns:
            True if Agent should be triggered
        """
        text = message.content.text or ""
        
        # 1. Command mode - always trigger
        if CommandParser.is_command(text):
            return True
        
        # 2. @ mention bot
        if self.bot_user_id and self.bot_user_id in message.mentions:
            return True
        
        # 3. Mention all
        if message.mention_all:
            return True
        
        # 4. Keyword triggers (if auto_reply is enabled)
        if channel.auto_reply:
            text_lower = text.lower()
            for keyword in self._trigger_keywords:
                if keyword in text_lower:
                    return True
        
        return False
    
    def get_trigger_reason(self, message: IMMessage) -> str:
        """Get the reason why this message triggered the Agent."""
        text = message.content.text or ""
        
        if CommandParser.is_command(text):
            return "command"
        if self.bot_user_id and self.bot_user_id in message.mentions:
            return "mention"
        if message.mention_all:
            return "mention_all"
        return "keyword"


class IMMessageHandler:
    """
    Handles incoming IM messages.
    
    Routes messages to appropriate handlers based on content type
    and channel configuration.
    """
    
    def __init__(
        self,
        im_manager: IMManager,
        session_manager: IMAgentSessionManager,
        output_callback: Optional[Callable[[str, str, str], None]] = None,
    ):
        self.im_manager = im_manager
        self.session_manager = session_manager
        self.output_callback = output_callback
        
        self.trigger = IMAgentTrigger()
        self.command_handler = IMCommandHandler(session_manager, im_manager)
    
    async def handle_message(self, message: IMMessage) -> HandlerResult:
        """
        Handle an incoming IM message.
        
        Args:
            message: The incoming message
        
        Returns:
            HandlerResult with processing outcome
        """
        # Save message to store
        self.im_manager.messages.save_message(message)
        
        # Get or create channel
        channel = self.im_manager.channels.get_or_create_channel(
            message.channel_id,
            message.platform,
        )
        
        # Check if we should trigger an Agent
        if not self.trigger.should_trigger(message, channel):
            logger.debug(f"[Message {message.message_id}] Not triggering Agent")
            return HandlerResult(success=True, message="Ignored")
        
        logger.info(f"[Message {message.message_id}] Triggering Agent ({self.trigger.get_trigger_reason(message)})")
        
        # Update message status
        self.im_manager.messages.update_message_status(
            message.message_id,
            MessageStatus.AGENT_PROCESSING,
        )
        
        try:
            # Check if this is a command
            command = CommandParser.parse(message.content.text or "")
            if command:
                return await self.command_handler.handle_command(
                    command, message, channel
                )
            
            # Handle as regular message (continue existing session or start new)
            return await self._handle_regular_message(message, channel)
            
        except Exception as e:
            logger.exception(f"[Message {message.message_id}] Error handling message")
            self.im_manager.messages.update_message_status(
                message.message_id,
                MessageStatus.ERROR,
            )
            return HandlerResult(success=False, error=str(e))
    
    async def _handle_regular_message(
        self,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """Handle a regular (non-command) message."""
        # Check for existing active session
        session = self.session_manager.get_channel_session(message.channel_id)
        
        if session and session.is_active():
            # Add message to existing session
            await session.add_message(message)
            logger.info(f"[Session {session.session_id}] Added message to existing session")
            
            # If session is idle, trigger processing
            if session.state == SessionState.IDLE:
                return await self._trigger_agent_processing(session, message)
            
            return HandlerResult(
                success=True,
                message="Added to existing session",
                session_id=session.session_id,
            )
        
        # No active session - create new one with default agent
        if channel.default_agent:
            session = await self.session_manager.create_session(
                channel_id=message.channel_id,
                agent_role=channel.default_agent,
                context_window=channel.context_window,
            )
            await session.add_message(message)
            
            logger.info(f"[Session {session.session_id}] Created new session with default agent {channel.default_agent}")
            
            return await self._trigger_agent_processing(session, message)
        
        # No default agent - ignore or send help message
        return HandlerResult(
            success=True,
            message="No active session and no default agent configured",
        )
    
    async def _trigger_agent_processing(
        self,
        session: IMAgentSessionController,
        message: IMMessage,
    ) -> HandlerResult:
        """Trigger Agent processing for a session."""
        await session.transition_to(SessionState.PROCESSING)
        
        # Build prompt from context
        prompt = session.context.to_prompt()
        
        # This would integrate with the scheduler
        # For now, we just mark it as processing
        logger.info(f"[Session {session.session_id}] Triggering {session.agent_role} with prompt length {len(prompt)}")
        
        return HandlerResult(
            success=True,
            message=f"Processing with {session.agent_role}",
            session_id=session.session_id,
        )


class IMCommandHandler:
    """
    Handles IM commands.
    
    Processes commands like /architect, /engineer, /status, etc.
    """
    
    def __init__(
        self,
        session_manager: IMAgentSessionManager,
        im_manager: IMManager,
    ):
        self.session_manager = session_manager
        self.im_manager = im_manager
    
    async def handle_command(
        self,
        command: Command,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """
        Handle a parsed command.
        
        Args:
            command: The parsed command
            message: The original message
            channel: The channel context
        
        Returns:
            HandlerResult with outcome
        """
        handler_map = {
            CommandType.ARCHITECT: self._handle_architect,
            CommandType.ENGINEER: self._handle_engineer,
            CommandType.REVIEWER: self._handle_reviewer,
            CommandType.PLANNER: self._handle_planner,
            CommandType.MEMO: self._handle_memo,
            CommandType.ISSUE: self._handle_issue,
            CommandType.STATUS: self._handle_status,
            CommandType.STOP: self._handle_stop,
            CommandType.HELP: self._handle_help,
        }
        
        handler = handler_map.get(command.command_type)
        if not handler:
            return HandlerResult(
                success=False,
                error=f"Unknown command: {command.command_type.value}"
            )
        
        return await handler(command, message, channel)
    
    async def _handle_architect(
        self,
        command: Command,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """Handle /architect command."""
        prompt = command.prompt
        
        session = await self.session_manager.create_session(
            channel_id=message.channel_id,
            agent_role="architect",
            context_window=channel.context_window,
        )
        await session.add_message(message)
        
        return HandlerResult(
            success=True,
            message=f"🏗️ Architect session started. Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"🏗️ Architect session started. Prompt: {prompt}",
            session_id=session.session_id,
        )
    
    async def _handle_engineer(
        self,
        command: Command,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """Handle /engineer command."""
        issue_id = command.target_id
        
        session = await self.session_manager.create_session(
            channel_id=message.channel_id,
            agent_role="engineer",
            context_window=channel.context_window,
            linked_issue_id=issue_id,
        )
        await session.add_message(message)
        
        msg = f"👨‍💻 Engineer session started"
        if issue_id:
            msg += f" for issue {issue_id}"
        
        return HandlerResult(
            success=True,
            message=msg,
            session_id=session.session_id,
        )
    
    async def _handle_reviewer(
        self,
        command: Command,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """Handle /reviewer command."""
        pr_url = command.target_id
        
        session = await self.session_manager.create_session(
            channel_id=message.channel_id,
            agent_role="reviewer",
            context_window=channel.context_window,
        )
        await session.add_message(message)
        
        msg = f"👁️ Reviewer session started"
        if pr_url:
            msg += f" for PR {pr_url}"
        
        return HandlerResult(
            success=True,
            message=msg,
            session_id=session.session_id,
        )
    
    async def _handle_planner(
        self,
        command: Command,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """Handle /planner command."""
        prompt = command.prompt
        
        session = await self.session_manager.create_session(
            channel_id=message.channel_id,
            agent_role="planner",
            context_window=channel.context_window,
        )
        await session.add_message(message)
        
        return HandlerResult(
            success=True,
            message=f"📋 Planner session started",
            session_id=session.session_id,
        )
    
    async def _handle_memo(
        self,
        command: Command,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """Handle /memo command."""
        content = command.prompt
        
        if not content:
            return HandlerResult(
                success=False,
                error="Please provide memo content: /memo [content]"
            )
        
        # Create memo using monoco memo add
        import subprocess
        try:
            result = subprocess.run(
                ["monoco", "memo", "add", content],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return HandlerResult(
                    success=True,
                    message=f"📝 Memo created: {content[:50]}..." if len(content) > 50 else f"📝 Memo created: {content}",
                )
            else:
                return HandlerResult(
                    success=False,
                    error=f"Failed to create memo: {result.stderr}"
                )
        except Exception as e:
            return HandlerResult(
                success=False,
                error=f"Error creating memo: {e}"
            )
    
    async def _handle_issue(
        self,
        command: Command,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """Handle /issue command."""
        title = command.prompt
        
        if not title:
            return HandlerResult(
                success=False,
                error="Please provide issue title: /issue [title]"
            )
        
        # Create feature issue
        import subprocess
        try:
            result = subprocess.run(
                ["monoco", "issue", "create", "feature", "-t", title],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Extract issue ID from output
                output = result.stdout
                return HandlerResult(
                    success=True,
                    message=f"📋 Issue created: {title[:50]}...\n{output}" if len(title) > 50 else f"📋 Issue created: {title}\n{output}",
                )
            else:
                return HandlerResult(
                    success=False,
                    error=f"Failed to create issue: {result.stderr}"
                )
        except Exception as e:
            return HandlerResult(
                success=False,
                error=f"Error creating issue: {e}"
            )
    
    async def _handle_status(
        self,
        command: Command,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """Handle /status command."""
        session = self.session_manager.get_channel_session(message.channel_id)
        
        if not session:
            return HandlerResult(
                success=True,
                message="ℹ️ No active session in this channel.",
            )
        
        model = session.to_model()
        status_text = f"""📊 Session Status

Session ID: {model.session_id}
Agent Role: {model.agent_role}
Status: {model.status}
Messages: {model.context_message_count}
Started: {model.started_at.strftime('%Y-%m-%d %H:%M:%S')}
Last Activity: {model.last_activity.strftime('%Y-%m-%d %H:%M:%S')}
"""
        if model.linked_issue_id:
            status_text += f"Linked Issue: {model.linked_issue_id}\n"
        
        return HandlerResult(
            success=True,
            message=status_text,
            session_id=session.session_id,
        )
    
    async def _handle_stop(
        self,
        command: Command,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """Handle /stop command."""
        session = self.session_manager.get_channel_session(message.channel_id)
        
        if not session:
            return HandlerResult(
                success=True,
                message="ℹ️ No active session to stop.",
            )
        
        await session.stop()
        await self.session_manager.end_session(session.session_id, status="stopped")
        
        return HandlerResult(
            success=True,
            message="🛑 Session stopped.",
            session_id=session.session_id,
        )
    
    async def _handle_help(
        self,
        command: Command,
        message: IMMessage,
        channel: IMChannel,
    ) -> HandlerResult:
        """Handle /help command."""
        commands = CommandParser.get_available_commands()
        
        help_text = "🤖 **Available Commands**\n\n"
        for cmd, desc in commands.items():
            help_text += f"**{cmd}**\n  {desc}\n\n"
        
        return HandlerResult(
            success=True,
            message=help_text,
        )


class IMStreamOutputHandler:
    """
    Handles streaming output from Agents to IM.
    
    Manages message updates, chunking, and formatting.
    """
    
    def __init__(
        self,
        send_callback: Callable[[str, Optional[str]], None],
        max_message_length: int = 2000,
    ):
        self.send_callback = send_callback
        self.max_message_length = max_message_length
        self._active_streams: Dict[str, Dict[str, Any]] = {}
    
    async def start_stream(
        self,
        session_id: str,
        channel_id: str,
        initial_message: str = "🤔 Thinking...",
    ) -> str:
        """
        Start a new stream.
        
        Returns:
            message_id: The ID of the stream message
        """
        # Send initial message
        message_id = await self._send_message(channel_id, initial_message)
        
        self._active_streams[session_id] = {
            "channel_id": channel_id,
            "message_id": message_id,
            "buffer": "",
            "chunks_sent": 0,
        }
        
        return message_id
    
    async def handle_chunk(self, session_id: str, chunk: StreamChunk) -> None:
        """Handle a stream chunk."""
        stream = self._active_streams.get(session_id)
        if not stream:
            return
        
        stream["buffer"] += chunk.content
        
        # Update message with new content
        if len(stream["buffer"]) > self.max_message_length:
            # Send as new message (continue)
            await self._send_message(
                stream["channel_id"],
                stream["buffer"][:self.max_message_length]
            )
            stream["buffer"] = stream["buffer"][self.max_message_length:]
            stream["chunks_sent"] += 1
        else:
            # Update existing message
            await self._update_message(
                stream["channel_id"],
                stream["message_id"],
                stream["buffer"] + (" ✍️" if not chunk.is_final else "")
            )
        
        if chunk.is_final:
            await self.end_stream(session_id)
    
    async def end_stream(self, session_id: str) -> None:
        """End a stream."""
        stream = self._active_streams.pop(session_id, None)
        if not stream:
            return
        
        # Final update
        if stream["buffer"]:
            await self._update_message(
                stream["channel_id"],
                stream["message_id"],
                stream["buffer"]
            )
    
    async def _send_message(self, channel_id: str, content: str) -> str:
        """Send a new message."""
        self.send_callback(channel_id, content)
        return f"msg_{datetime.now().timestamp()}"
    
    async def _update_message(self, channel_id: str, message_id: str, content: str) -> None:
        """Update an existing message."""
        # This would call the platform-specific API to update a message
        # For now, just log it
        logger.debug(f"[Stream] Update message {message_id} in {channel_id}: {content[:50]}...")
