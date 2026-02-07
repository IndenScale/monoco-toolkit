"""
Courier - IM Agent Integration (FEAT-0170).

Integrates IM Agent session management with Courier daemon,
enabling real-time Agent conversations through IM platforms.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from monoco.features.im import (
    IMManager,
    IMMessage,
    PlatformType,
    MessageStatus,
)
from monoco.features.im.session import (
    IMAgentSessionManager,
    IMAgentSessionController,
    SessionState,
)
from monoco.features.im.handlers import (
    IMMessageHandler,
    IMCommandHandler,
    HandlerResult,
)
from monoco.core.scheduler import (
    AgentScheduler,
    AgentTask,
    AgentStatus,
    event_bus,
    AgentEventType,
)

logger = logging.getLogger(__name__)


@dataclass
class IMCourierConfig:
    """Configuration for IM-Courier integration."""
    enabled: bool = True
    project_root: Optional[Path] = None
    max_concurrent_sessions: int = 5
    session_timeout_minutes: int = 30
    context_window_size: int = 10
    
    # Platform-specific settings
    auto_reply_default: bool = True
    require_mention: bool = True


class CourierIMAdapter:
    """
    Adapter integrating IM Agent sessions with Courier daemon.
    
    Responsibilities:
    - Manage IM session lifecycle
    - Route Agent output to IM
    - Handle Agent events and update IM
    - Coordinate with AgentScheduler
    """
    
    def __init__(
        self,
        config: IMCourierConfig,
        scheduler: Optional[AgentScheduler] = None,
    ):
        self.config = config
        self.scheduler = scheduler
        
        # Components (initialized in start())
        self.im_manager: Optional[IMManager] = None
        self.session_manager: Optional[IMAgentSessionManager] = None
        self.message_handler: Optional[IMMessageHandler] = None
        
        # State
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._event_handlers: list = []
    
    async def start(self) -> None:
        """Start the IM-Courier adapter."""
        if self._running:
            return
        
        project_root = self.config.project_root or Path.cwd()
        
        # Initialize IM components
        self.im_manager = IMManager(project_root)
        self.session_manager = IMAgentSessionManager(
            storage_dir=project_root / ".monoco" / "im",
            message_store=self.im_manager.messages,
            channel_manager=self.im_manager.channels,
        )
        
        # Initialize message handler
        self.message_handler = IMMessageHandler(
            im_manager=self.im_manager,
            session_manager=self.session_manager,
            output_callback=self._on_agent_output,
        )
        
        # Start session manager
        await self.session_manager.start()
        
        # Subscribe to Agent events
        self._subscribe_to_events()
        
        self._running = True
        logger.info("CourierIMAdapter started")
    
    async def stop(self) -> None:
        """Stop the IM-Courier adapter."""
        if not self._running:
            return
        
        self._running = False
        
        # Unsubscribe from events
        for event_type, handler in self._event_handlers:
            event_bus.unsubscribe(event_type, handler)
        self._event_handlers.clear()
        
        # Stop session manager
        if self.session_manager:
            await self.session_manager.stop()
        
        logger.info("CourierIMAdapter stopped")
    
    def _subscribe_to_events(self) -> None:
        """Subscribe to Agent scheduler events."""
        handlers = [
            (AgentEventType.SESSION_STARTED, self._on_session_started),
            (AgentEventType.SESSION_COMPLETED, self._on_session_completed),
            (AgentEventType.SESSION_FAILED, self._on_session_failed),
            (AgentEventType.SESSION_TERMINATED, self._on_session_terminated),
        ]
        
        for event_type, handler in handlers:
            event_bus.subscribe(event_type, handler)
            self._event_handlers.append((event_type, handler))
    
    # --- Event Handlers ---
    
    async def _on_session_started(self, event: Dict[str, Any]) -> None:
        """Handle Agent session started event."""
        session_id = event.get("session_id")
        role_name = event.get("role_name")
        issue_id = event.get("issue_id")
        
        logger.info(f"[Agent] Session {session_id} started ({role_name})")
        
        # Find associated IM session
        if not self.session_manager:
            return
        
        for im_session in self.session_manager.list_sessions(active_only=True):
            if im_session.agent_role == role_name:
                await im_session.transition_to(SessionState.PROCESSING)
                break
    
    async def _on_session_completed(self, event: Dict[str, Any]) -> None:
        """Handle Agent session completed event."""
        session_id = event.get("session_id")
        role_name = event.get("role_name")
        
        logger.info(f"[Agent] Session {session_id} completed ({role_name})")
        
        # Complete associated IM sessions
        if not self.session_manager:
            return
        
        for im_session in self.session_manager.list_sessions(active_only=True):
            if im_session.state == SessionState.PROCESSING:
                await im_session.complete(f"Agent session completed")
                break
    
    async def _on_session_failed(self, event: Dict[str, Any]) -> None:
        """Handle Agent session failed event."""
        session_id = event.get("session_id")
        role_name = event.get("role_name")
        reason = event.get("reason", "Unknown error")
        
        logger.error(f"[Agent] Session {session_id} failed ({role_name}): {reason}")
        
        # Fail associated IM sessions
        if not self.session_manager:
            return
        
        for im_session in self.session_manager.list_sessions(active_only=True):
            if im_session.state == SessionState.PROCESSING:
                await im_session.fail(reason)
                break
    
    async def _on_session_terminated(self, event: Dict[str, Any]) -> None:
        """Handle Agent session terminated event."""
        session_id = event.get("session_id")
        role_name = event.get("role_name")
        
        logger.info(f"[Agent] Session {session_id} terminated ({role_name})")
    
    def _on_agent_output(self, channel_id: str, content: str, session_id: str) -> None:
        """Handle Agent output for IM."""
        logger.debug(f"[Agent Output] Channel {channel_id}: {content[:100]}...")
        # This would be called to send output to IM
        # Implementation depends on platform adapter
    
    # --- Message Processing ---
    
    async def handle_inbound_message(self, message: IMMessage) -> HandlerResult:
        """
        Process an inbound IM message.
        
        This is the main entry point for IM messages received by Courier.
        
        Args:
            message: The incoming IM message
        
        Returns:
            HandlerResult with processing outcome
        """
        if not self.message_handler:
            return HandlerResult(
                success=False,
                error="Message handler not initialized"
            )
        
        return await self.message_handler.handle_message(message)
    
    async def schedule_agent_task(
        self,
        session: IMAgentSessionController,
        prompt: str,
    ) -> Optional[str]:
        """
        Schedule an Agent task via the scheduler.
        
        Args:
            session: The IM Agent session
            prompt: The prompt to send to the Agent
        
        Returns:
            scheduler_session_id if scheduled, None otherwise
        """
        if not self.scheduler:
            logger.warning("No scheduler available for Agent task")
            return None
        
        try:
            task = AgentTask(
                task_id=session.session_id,
                role_name=session.agent_role,
                issue_id=session.linked_issue_id or "IM-SESSION",
                prompt=prompt,
                engine="claude",  # Default engine
                timeout=900,
            )
            
            scheduler_session_id = await self.scheduler.schedule(task)
            logger.info(f"[Scheduler] Task scheduled: {scheduler_session_id}")
            
            return scheduler_session_id
            
        except Exception as e:
            logger.error(f"[Scheduler] Failed to schedule task: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        if not self.session_manager:
            return {"running": self._running}
        
        sessions = self.session_manager.list_sessions()
        active_sessions = [s for s in sessions if s.is_active()]
        
        return {
            "running": self._running,
            "total_sessions": len(sessions),
            "active_sessions": len(active_sessions),
            "max_concurrent": self.config.max_concurrent_sessions,
        }


class CourierIMWebhookHandler:
    """
    Handles IM webhooks and routes to CourierIMAdapter.
    
    Platform-specific webhook handlers should use this to
    process incoming messages.
    """
    
    def __init__(self, adapter: CourierIMAdapter):
        self.adapter = adapter
    
    async def handle_message(
        self,
        message_id: str,
        channel_id: str,
        sender_id: str,
        sender_name: str,
        content_text: str,
        platform: PlatformType,
        mentions: Optional[list] = None,
        reply_to: Optional[str] = None,
    ) -> HandlerResult:
        """
        Handle a message from webhook.
        
        Args:
            message_id: Platform message ID
            channel_id: Platform channel ID
            sender_id: Sender's platform ID
            sender_name: Sender's display name
            content_text: Message text content
            platform: Platform type
            mentions: List of mentioned user IDs
            reply_to: ID of message being replied to
        
        Returns:
            HandlerResult with processing outcome
        """
        from monoco.features.im.models import IMParticipant, MessageContent
        
        # Build IMMessage from webhook data
        sender = IMParticipant(
            participant_id=sender_id,
            platform=platform,
            participant_type="user",
            name=sender_name,
            display_name=sender_name,
        )
        
        content = MessageContent(
            type=ContentType.TEXT,
            text=content_text,
        )
        
        message = IMMessage(
            message_id=message_id,
            channel_id=channel_id,
            platform=platform,
            sender=sender,
            content=content,
            mentions=mentions or [],
            reply_to=reply_to,
        )
        
        return await self.adapter.handle_inbound_message(message)


# --- Factory Function ---

def create_im_adapter(
    project_root: Optional[Path] = None,
    scheduler: Optional[AgentScheduler] = None,
    **config_overrides
) -> CourierIMAdapter:
    """
    Factory function to create a CourierIMAdapter.
    
    Args:
        project_root: Project root path
        scheduler: Optional AgentScheduler instance
        **config_overrides: Override default config values
    
    Returns:
        Configured CourierIMAdapter
    """
    config = IMCourierConfig(
        project_root=project_root,
        **config_overrides
    )
    
    return CourierIMAdapter(config, scheduler)
