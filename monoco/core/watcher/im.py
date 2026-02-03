"""
IMWatcher - Monitors IM message flow for Agent triggers (FEAT-0167).

Part of Layer 1 (File Watcher) in the event automation framework.
Emits events when IM messages are received and need Agent processing.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from monoco.core.scheduler import AgentEventType, EventBus, event_bus

from .base import (
    ChangeType,
    FileEvent,
    PollingWatcher,
    WatchConfig,
)

logger = logging.getLogger(__name__)


class IMFileEvent(FileEvent):
    """FileEvent specific to IM message files."""
    
    def __init__(
        self,
        path: Path,
        change_type: ChangeType,
        message_id: str,
        channel_id: str,
        platform: str,
        event_type: str = "message_received",
        **kwargs,
    ):
        super().__init__(
            path=path,
            change_type=change_type,
            watcher_name="IMWatcher",
            **kwargs,
        )
        self.message_id = message_id
        self.channel_id = channel_id
        self.platform = platform
        self.event_type = event_type
    
    def to_agent_event_type(self) -> Optional[AgentEventType]:
        """Convert to appropriate AgentEventType."""
        event_map = {
            "message_received": AgentEventType.IM_MESSAGE_RECEIVED,
            "message_replied": AgentEventType.IM_MESSAGE_REPLIED,
            "agent_trigger": AgentEventType.IM_AGENT_TRIGGER,
            "session_started": AgentEventType.IM_SESSION_STARTED,
            "session_closed": AgentEventType.IM_SESSION_CLOSED,
        }
        return event_map.get(self.event_type)
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to payload with IM-specific fields."""
        payload = super().to_payload()
        payload.update({
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "platform": self.platform,
            "event_type": self.event_type,
        })
        return payload


class IMWatcher(PollingWatcher):
    """
    Watcher for IM message storage.
    
    Monitors the .monoco/im/messages/ directory for:
    - New message files
    - Message status changes
    - Agent trigger conditions
    
    Emits appropriate events to the EventBus for Agent scheduling.
    
    Example:
        >>> config = WatchConfig(
        ...     path=Path("./.monoco/im/messages"),
        ...     patterns=["*.jsonl"],
        ...     poll_interval=2.0,
        ... )
        >>> watcher = IMWatcher(config)
        >>> await watcher.start()
    """
    
    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        name: str = "IMWatcher",
        trigger_on_mention: bool = True,
    ):
        super().__init__(config, event_bus, name)
        self.trigger_on_mention = trigger_on_mention
        self._file_states: Dict[Path, Dict[str, Any]] = {}
        self._processed_messages: set = set()
        self._message_handlers: List[Callable[[Dict[str, Any]], None]] = []
    
    def register_message_handler(
        self,
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register a handler for new messages.
        
        The handler will be called with the message data dictionary.
        """
        self._message_handlers.append(handler)
        logger.debug(f"Registered message handler: {handler.__name__}")
    
    def unregister_message_handler(
        self,
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Unregister a message handler."""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)
    
    async def _check_changes(self) -> None:
        """Check for new messages in IM storage."""
        if not self.config.path.exists():
            return
        
        try:
            # Scan all message files
            message_files = list(self.config.path.glob("*.jsonl"))
            
            for file_path in message_files:
                if not self._should_process(file_path):
                    continue
                
                await self._process_message_file(file_path)
        
        except Exception as e:
            logger.error(f"Error checking IM messages: {e}")
    
    async def _process_message_file(self, file_path: Path) -> None:
        """Process a message file for new entries."""
        try:
            # Get current file state
            stat = file_path.stat()
            current_size = stat.st_size
            
            # Check if we've seen this file before
            if file_path in self._file_states:
                last_size = self._file_states[file_path].get("size", 0)
                if current_size <= last_size:
                    # No new content
                    return
            
            # Read new messages
            messages = self._read_messages(file_path)
            
            for message_data in messages:
                message_id = message_data.get("message_id")
                
                if not message_id:
                    continue
                
                # Skip already processed messages
                if message_id in self._processed_messages:
                    continue
                
                # Process new message
                await self._handle_new_message(file_path, message_data)
                self._processed_messages.add(message_id)
            
            # Update file state
            self._file_states[file_path] = {
                "size": current_size,
                "mtime": stat.st_mtime,
            }
        
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    def _read_messages(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read all messages from a JSONL file."""
        messages = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        messages.append(data)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in {file_path}")
        
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
        
        return messages
    
    async def _handle_new_message(
        self,
        file_path: Path,
        message_data: Dict[str, Any]
    ) -> None:
        """Handle a new message."""
        message_id = message_data.get("message_id")
        channel_id = message_data.get("channel_id")
        platform = message_data.get("platform", "unknown")
        status = message_data.get("status", "received")
        
        logger.debug(f"New IM message: {message_id} in {channel_id}")
        
        # Call registered handlers
        for handler in self._message_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message_data)
                else:
                    handler(message_data)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
        
        # Determine event type based on status
        event_type = self._determine_event_type(message_data)
        
        if event_type:
            event = IMFileEvent(
                path=file_path,
                change_type=ChangeType.CREATED,
                message_id=message_id,
                channel_id=channel_id,
                platform=platform,
                event_type=event_type,
                metadata={
                    "status": status,
                    "sender": message_data.get("sender", {}),
                    "content_preview": self._get_content_preview(message_data),
                },
            )
            await self.emit(event)
            logger.info(f"Emitted IM event: {event_type} for message {message_id}")
    
    def _determine_event_type(self, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Determine the event type for a message.
        
        Returns:
            Event type string or None if no event should be emitted
        """
        status = message_data.get("status", "received")
        
        # Map status to event type
        status_map = {
            "received": "message_received",
            "routing": "message_received",
            "agent_processing": "agent_trigger",
            "replied": "message_replied",
        }
        
        event_type = status_map.get(status)
        
        # Check for agent trigger conditions
        if event_type == "message_received" and self._should_trigger_agent(message_data):
            event_type = "agent_trigger"
        
        return event_type
    
    def _should_trigger_agent(self, message_data: Dict[str, Any]) -> bool:
        """
        Determine if this message should trigger an Agent.
        
        Override this method for custom trigger logic.
        """
        content = message_data.get("content", {})
        text = content.get("text", "")
        mentions = message_data.get("mentions", [])
        mention_all = message_data.get("mention_all", False)
        
        # Trigger if @mentioned
        if mentions or mention_all:
            return True
        
        # Trigger on specific keywords
        trigger_keywords = [
            "@monoco", "@agent", "@bot",
            "#task", "#issue", "#help",
        ]
        
        text_lower = text.lower() if text else ""
        for keyword in trigger_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def _get_content_preview(self, message_data: Dict[str, Any], max_length: int = 50) -> str:
        """Get a preview of the message content."""
        content = message_data.get("content", {})
        text = content.get("text", "")
        
        if not text:
            return "[No text content]"
        
        if len(text) > max_length:
            return text[:max_length] + "..."
        
        return text
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        stats = super().get_stats()
        stats.update({
            "processed_messages": len(self._processed_messages),
            "monitored_files": len(self._file_states),
            "trigger_on_mention": self.trigger_on_mention,
        })
        return stats
    
    def clear_processed_cache(self) -> None:
        """Clear the processed message cache."""
        self._processed_messages.clear()
        logger.debug("Cleared IM message processed cache")


class IMInboundWatcher(IMWatcher):
    """
    Specialized watcher for inbound IM messages.
    
    Watches for messages that need Agent attention and emits
    IM_AGENT_TRIGGER events.
    """
    
    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        name: str = "IMInboundWatcher",
    ):
        super().__init__(config, event_bus, name, trigger_on_mention=True)
    
    def _should_trigger_agent(self, message_data: Dict[str, Any]) -> bool:
        """Always trigger for inbound messages that need processing."""
        # Only trigger for messages in 'received' or 'routing' status
        status = message_data.get("status", "")
        if status not in ("received", "routing"):
            return False
        
        # Check if sender is not an agent/bot
        sender = message_data.get("sender", {})
        sender_type = sender.get("participant_type", "user")
        if sender_type in ("agent", "bot"):
            return False
        
        # Check for mentions
        mentions = message_data.get("mentions", [])
        mention_all = message_data.get("mention_all", False)
        
        if mentions or mention_all:
            return True
        
        # Check for trigger keywords
        content = message_data.get("content", {})
        text = content.get("text", "")
        
        if text:
            text_lower = text.lower()
            trigger_keywords = [
                "@monoco", "@agent", "@bot",
                "#task", "#issue", "#help",
                "请帮忙", "help me", " assistance",
            ]
            for keyword in trigger_keywords:
                if keyword in text_lower:
                    return True
        
        return False


class IMWebhookWatcher(PollingWatcher):
    """
    Watcher for IM webhook configuration changes.
    
    Monitors the .monoco/im/webhooks/ directory for:
    - New webhook configurations
    - Webhook configuration updates
    """
    
    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        name: str = "IMWebhookWatcher",
    ):
        super().__init__(config, event_bus, name)
        self._webhook_configs: Dict[str, Dict[str, Any]] = {}
    
    async def _check_changes(self) -> None:
        """Check for webhook configuration changes."""
        if not self.config.path.exists():
            return
        
        try:
            config_files = list(self.config.path.glob("*.json"))
            
            for file_path in config_files:
                if not self._should_process(file_path):
                    continue
                
                await self._process_config_file(file_path)
        
        except Exception as e:
            logger.error(f"Error checking webhook configs: {e}")
    
    async def _process_config_file(self, file_path: Path) -> None:
        """Process a webhook config file."""
        try:
            stat = file_path.stat()
            mtime = stat.st_mtime
            
            # Check if file has been modified
            if file_path.name in self._webhook_configs:
                last_mtime = self._webhook_configs[file_path.name].get("mtime", 0)
                if mtime <= last_mtime:
                    return
            
            # Read and validate config
            config_data = json.loads(file_path.read_text(encoding="utf-8"))
            
            # Store config state
            self._webhook_configs[file_path.name] = {
                "mtime": mtime,
                "config": config_data,
            }
            
            # Emit event
            event = FileEvent(
                path=file_path,
                change_type=ChangeType.MODIFIED,
                watcher_name=self.name,
                metadata={
                    "platform": config_data.get("platform"),
                    "channel_id": config_data.get("channel_id"),
                    "event_type": "webhook_config_updated",
                },
            )
            await self.emit(event)
            
            logger.info(f"Updated webhook config: {file_path.name}")
        
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
