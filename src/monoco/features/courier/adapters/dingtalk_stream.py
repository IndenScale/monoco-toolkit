"""
DingTalk Stream Adapter - Official SDK implementation (no public IP needed).
"""

import logging
import threading
import time
from typing import Callable, Dict, Any, Optional
from datetime import datetime

from monoco.features.connector.protocol.schema import (
    InboundMessage,
    OutboundMessage,
    Provider,
    Session,
    SessionType,
    Content,
    ContentType,
)

from .base import BaseAdapter, AdapterConfig, SendResult, HealthStatus

logger = logging.getLogger(__name__)


class DingTalkStreamAdapter(BaseAdapter):
    """DingTalk Stream mode adapter using official SDK."""
    
    provider: str = "dingtalk_stream"
    
    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        app_key: str = "",
        app_secret: str = "",
        default_project: str = "default",
        project_mapping: Optional[Dict[str, str]] = None,
    ):
        config = AdapterConfig(provider="dingtalk_stream")
        super().__init__(config)
        
        self._client_id = client_id or app_key
        self._client_secret = client_secret or app_secret
        self._default_project = default_project
        self._project_mapping = project_mapping or {}
        
        self._client: Any = None
        self._message_handler: Optional[Callable[[InboundMessage, str], None]] = None
        self._running = False
        self._connected = False
        
    def set_message_handler(self, handler: Callable[[InboundMessage, str], None]):
        """Set handler for incoming messages."""
        self._message_handler = handler
    
    def _parse_message(self, message: Any) -> Optional[InboundMessage]:
        """Parse DingTalk message to InboundMessage format."""
        try:
            msg_dict = message.to_dict() if hasattr(message, 'to_dict') else {}
            
            logger.debug(f"Parsing message: {msg_dict}")
            
            msg_type = msg_dict.get("msgtype", "text")
            sender_staff_id = msg_dict.get("senderStaffId", "unknown")
            sender_nick = msg_dict.get("senderNick", "Unknown")
            conversation_id = msg_dict.get("conversationId", "unknown")
            conversation_title = msg_dict.get("conversationTitle")
            chat_type = msg_dict.get("chatType", "")
            
            session_type = SessionType.GROUP if str(chat_type) == "2" else SessionType.DIRECT
            
            # Extract content
            content_text = ""
            if msg_type == "text":
                text_obj = msg_dict.get("text", {})
                content_text = text_obj.get("content", "") if isinstance(text_obj, dict) else str(text_obj)
            elif msg_type == "markdown":
                md_obj = msg_dict.get("markdown", {})
                content_text = md_obj.get("text", "") if isinstance(md_obj, dict) else str(md_obj)
            
            msg_id = msg_dict.get("msgId", "")
            if not msg_id:
                import hashlib
                content_hash = hashlib.sha256(
                    f"{sender_staff_id}:{conversation_id}:{content_text}:{time.time()}".encode()
                ).hexdigest()[:16]
                msg_id = content_hash
            
            logger.info(f"✉️  Received from {sender_nick}: {content_text[:50]}")
            
            return InboundMessage(
                id=f"dingtalk_{msg_id}",
                provider=Provider.DINGTALK,
                session=Session(
                    id=conversation_id,
                    type=session_type,
                    name=conversation_title,
                    thread_key=None,
                ),
                participants={
                    "from": {
                        "id": sender_staff_id,
                        "name": sender_nick,
                        "platform_id": sender_staff_id,
                    },
                    "to": [],
                },
                timestamp=datetime.utcnow(),
                received_at=datetime.utcnow(),
                type=ContentType.TEXT if msg_type == "text" else ContentType.MARKDOWN,
                content=Content(
                    text=content_text if msg_type == "text" else None,
                    markdown=content_text if msg_type == "markdown" else None,
                ),
                artifacts=[],
                metadata={
                    "dingtalk_raw": msg_dict,
                    "msg_type": msg_type,
                    "receive_mode": "stream",
                },
            )
            
        except Exception as e:
            logger.exception(f"Failed to parse message: {e}")
            return None
    
    def run_sync(self) -> None:
        """Run the Stream adapter synchronously (blocking)."""
        try:
            from dingtalk_stream import DingTalkStreamClient, Credential
            from dingtalk_stream import ChatbotHandler, AckMessage
            
            credential = Credential(
                client_id=self._client_id,
                client_secret=self._client_secret,
            )
            
            self._client = DingTalkStreamClient(credential)
            adapter = self
            
            class MonocoChatbotHandler(ChatbotHandler):
                def process(self, message):
                    try:
                        inbound_msg = adapter._parse_message(message)
                        if inbound_msg and adapter._message_handler:
                            conversation_id = inbound_msg.session.id if inbound_msg.session else "unknown"
                            project_slug = adapter._project_mapping.get(
                                conversation_id, 
                                adapter._default_project
                            )
                            adapter._message_handler(inbound_msg, project_slug)
                        return AckMessage.STATUS_OK
                    except Exception as e:
                        logger.exception(f"Handler error: {e}")
                        return AckMessage.STATUS_OK
            
            handler = MonocoChatbotHandler()
            self._client.register_callback_handler('/v1.0/im/bot/messages/get', handler)
            
            self._connected = True
            self._running = True
            
            logger.info("🚀 DingTalk Stream adapter starting...")
            # This blocks forever
            self._client.start_forever()
            
        except Exception as e:
            logger.exception(f"Stream adapter error: {e}")
            self._running = False
            self._connected = False
    
    async def connect(self) -> None:
        """Async connect - just mark as connected, actual run is in run_sync."""
        self._connected = True
        self._running = True
    
    async def disconnect(self) -> None:
        """Stop the adapter."""
        self._running = False
        self._connected = False
        logger.info("DingTalk Stream adapter disconnected")
    
    async def listen(self):
        """Async generator for compatibility."""
        import asyncio
        while self._running:
            await asyncio.sleep(1)
            yield None
    
    async def send(self, message: OutboundMessage) -> SendResult:
        return SendResult(
            success=False,
            error="Send via Stream adapter not implemented."
        )
    
    async def health_check(self) -> HealthStatus:
        if not self._connected:
            return HealthStatus.DISCONNECTED
        return HealthStatus.CONNECTED if self._running else HealthStatus.ERROR


def create_dingtalk_stream_adapter(**kwargs) -> DingTalkStreamAdapter:
    return DingTalkStreamAdapter(**kwargs)
