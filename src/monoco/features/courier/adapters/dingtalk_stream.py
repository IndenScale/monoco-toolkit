"""
DingTalk Stream Adapter - Official SDK implementation (no public IP needed).

Supports both receiving messages via Stream and sending messages via OpenAPI.
"""

import json
import logging
import threading
import time
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

import httpx

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
    """DingTalk Stream mode adapter using official SDK.
    
    Receives messages via persistent Stream connection.
    Sends messages via DingTalk OpenAPI.
    """
    
    provider: str = "dingtalk_stream"
    
    # DingTalk OpenAPI endpoints
    API_BASE = "https://api.dingtalk.com"
    
    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        client_id: str = "",
        client_secret: str = "",
        robot_code: str = "",
        webhook_url: str = "",
        app_key: str = "",
        app_secret: str = "",
        default_project: str = "default",
        project_mapping: Optional[Dict[str, str]] = None,
    ):
        # Support both AdapterConfig (from dispatcher) and direct string args
        if config is None:
            config = AdapterConfig(provider="dingtalk_stream")
        super().__init__(config)
        
        # Try to get credentials from config extras, then from direct args, then env
        import os
        self._client_id = (
            client_id or app_key or
            getattr(config, 'client_id', None) or 
            os.environ.get("DINGTALK_CLIENT_ID") or 
            os.environ.get("DINGTALK_APP_KEY", "")
        )
        self._client_secret = (
            client_secret or app_secret or
            getattr(config, 'client_secret', None) or 
            os.environ.get("DINGTALK_CLIENT_SECRET") or 
            os.environ.get("DINGTALK_APP_SECRET", "")
        )
        # Robot code for sending messages (may be different from client_id)
        self._robot_code = (
            robot_code or
            getattr(config, 'robot_code', None) or
            os.environ.get("DINGTALK_ROBOT_CODE") or 
            self._client_id  # Fallback to client_id
        )
        # Webhook URL for fallback
        self._webhook_url = (
            webhook_url or
            getattr(config, 'webhook_url', None) or
            os.environ.get("DINGTALK_WEBHOOK_URL", "")
        )
        
        logger.info(f"DingTalkStreamAdapter initialized: client_id={self._client_id[:15]}..., robot_code={self._robot_code[:15]}..., webhook={bool(self._webhook_url)}")
        self._default_project = getattr(config, 'default_project', None) or default_project
        self._project_mapping = project_mapping or {}
        
        self._client: Any = None
        self._message_handler: Optional[Callable[[InboundMessage, str], None]] = None
        self._running = False
        self._connected = False
        
        # Token cache for OpenAPI
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        
    def set_message_handler(self, handler: Callable[[InboundMessage, str], None]):
        """Set handler for incoming messages."""
        self._message_handler = handler
    
    async def _get_access_token(self) -> Optional[str]:
        """Get cached access token or fetch a new one.
        
        Returns:
            Access token string or None if failed.
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.now(timezone.utc) < self._token_expires_at - timedelta(minutes=5):
                return self._access_token
        
        # Fetch new token
        try:
            if not self._http_client:
                self._http_client = httpx.AsyncClient(timeout=30.0)
            
            url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
            payload = {
                "appKey": self._client_id,
                "appSecret": self._client_secret,
            }
            
            logger.debug(f"Getting access token with appKey: {self._client_id[:10]}...")
            response = await self._http_client.post(url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Token request failed: {response.status_code} - {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            access_token = result.get("accessToken")
            expires_in = result.get("expireIn", 7200)
            
            if access_token:
                self._access_token = access_token
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                logger.debug(f"Got new access token, expires in {expires_in}s")
                return access_token
            else:
                logger.error(f"Failed to get access token: {result}")
                return None
                
        except Exception as e:
            logger.exception(f"Error fetching access token: {e}")
            return None
    
    def _is_conversation_id(self, target: str) -> bool:
        """Check if target is a conversation ID (starts with 'cid').
        
        Args:
            target: The target string (conversation_id or user_id)
            
        Returns:
            True if it's a conversation ID, False if it's a user ID.
        """
        # Conversation IDs typically start with 'cid' and contain '/'
        # User IDs typically start with '$:LWCP_v1:$'
        return target.startswith("cid") or "/" in target
    
    async def _send_via_webhook(self, message: OutboundMessage) -> SendResult:
        """Send message using webhook as fallback.
        
        Args:
            message: The message to send
            
        Returns:
            SendResult with success/failure information
        """
        webhook_url = self._webhook_url
        if not webhook_url:
            return SendResult(
                success=False,
                error="No webhook URL configured for fallback",
                timestamp=datetime.now(timezone.utc),
            )
        
        try:
            content = message.content
            text = content.text or content.markdown or ""
            
            payload = {
                "msgtype": "text",
                "text": {"content": text},
            }
            
            response = await self._http_client.post(webhook_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if result.get("errcode") == 0:
                return SendResult(
                    success=True,
                    timestamp=datetime.now(timezone.utc),
                )
            else:
                return SendResult(
                    success=False,
                    error=f"Webhook error: {result.get('errmsg')}",
                    timestamp=datetime.now(timezone.utc),
                )
        except Exception as e:
            logger.error(f"Webhook fallback failed: {e}")
            return SendResult(
                success=False,
                error=f"Webhook fallback failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
            )
    
    async def _send_to_conversation(
        self, 
        access_token: str, 
        conversation_id: str, 
        message: OutboundMessage
    ) -> SendResult:
        """Send message to a group conversation using OpenAPI.
        
        Falls back to webhook if OpenAPI fails with "robot not found" error.
        
        Args:
            access_token: DingTalk access token
            conversation_id: Open conversation ID
            message: The message to send
            
        Returns:
            SendResult with success/failure information
        """
        try:
            # Use the openConversationId-based send API
            url = f"{self.API_BASE}/v1.0/robot/groupMessages/send"
            
            # Build message content
            content = message.content
            text = content.text or content.markdown or ""
            
            # According to DingTalk docs, msgParam must be a JSON string
            if message.type == ContentType.MARKDOWN and content.markdown:
                msg_key = "sampleMarkdown"
                msg_param = json.dumps({
                    "title": "Message",
                    "text": content.markdown
                })
            else:
                # Default to text
                msg_key = "sampleText"
                msg_param = json.dumps({"content": text})
            
            payload = {
                "robotCode": self._robot_code,
                "openConversationId": conversation_id,
                "msgKey": msg_key,
                "msgParam": msg_param,
            }
            
            headers = {"x-acs-dingtalk-access-token": access_token}
            
            logger.info(f"Sending DingTalk message with robot_code: {self._robot_code[:15]}... to conversation: {conversation_id[:20]}...")
            logger.info(f"Request payload: {payload}")
            
            response = await self._http_client.post(
                url, 
                json=payload,
                headers=headers
            )
            
            # Debug logging
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response body: {response.text}")
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                return SendResult(
                    success=True,
                    provider_message_id=result.get("processQueryKey"),
                    timestamp=datetime.now(timezone.utc),
                )
            else:
                # Try to parse error
                try:
                    error_result = response.json()
                    error_msg = error_result.get("message", response.text)
                    error_code = error_result.get("code", "")
                except:
                    error_msg = response.text
                    error_code = ""
                
                # Check if it's a "robot not found" error and fallback to webhook
                if "robot" in error_msg.lower() and "不存在" in error_msg:
                    logger.warning(f"OpenAPI failed with robot error, falling back to webhook: {error_msg}")
                    return await self._send_via_webhook(message)
                
                return SendResult(
                    success=False,
                    error=f"DingTalk API error ({response.status_code}): {error_msg}",
                    timestamp=datetime.now(timezone.utc),
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending to conversation: {e}")
            return SendResult(
                success=False,
                error=f"HTTP error: {str(e)}",
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.exception(f"Error sending to conversation: {e}")
            return SendResult(
                success=False,
                error=f"Send error: {str(e)}",
                timestamp=datetime.now(timezone.utc),
            )
    
    async def _send_to_user(
        self, 
        access_token: str, 
        user_id: str, 
        message: OutboundMessage
    ) -> SendResult:
        """Send message to a single user (private chat).
        
        Args:
            access_token: DingTalk access token
            user_id: User's staff ID or open ID
            message: The message to send
            
        Returns:
            SendResult with success/failure information
        """
        try:
            url = f"{self.API_BASE}/v1.0/robot/oToMessages/batchSend"
            
            # Build message content
            content = message.content
            if message.type == ContentType.MARKDOWN and content.markdown:
                msg_key = "sampleMarkdown"
                msg_param = json.dumps({
                    "title": "Message",
                    "text": content.markdown
                })
            else:
                # Default to text
                text = content.text or content.markdown or ""
                msg_key = "sampleText"
                msg_param = json.dumps({"content": text})
            
            payload = {
                "robotCode": self._robot_code,
                "userIds": [user_id],
                "msgKey": msg_key,
                "msgParam": msg_param,
            }
            
            headers = {"x-acs-dingtalk-access-token": access_token}
            
            response = await self._http_client.post(
                url, 
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Check for success - batchSend returns flowControlStatus
            if response.status_code == 200:
                return SendResult(
                    success=True,
                    provider_message_id=result.get("processQueryKey"),
                    timestamp=datetime.now(timezone.utc),
                )
            else:
                return SendResult(
                    success=False,
                    error=f"DingTalk API error: {result}",
                    timestamp=datetime.now(timezone.utc),
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending to user: {e}")
            return SendResult(
                success=False,
                error=f"HTTP error: {str(e)}",
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.exception(f"Error sending to user: {e}")
            return SendResult(
                success=False,
                error=f"Send error: {str(e)}",
                timestamp=datetime.now(timezone.utc),
            )
    
    async def send(self, message: OutboundMessage) -> SendResult:
        """Send a message via DingTalk OpenAPI.
        
        Supports both group conversations (via conversation_id) and
        private chats (via user_id).
        
        Args:
            message: The outbound message to send
            
        Returns:
            SendResult with success/failure information
        """
        # Get access token
        access_token = await self._get_access_token()
        if not access_token:
            return SendResult(
                success=False,
                error="Failed to get access token",
                timestamp=datetime.now(timezone.utc),
            )
        
        # Ensure HTTP client is initialized
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        
        # Determine target (conversation or user)
        target = message.to
        if isinstance(target, list):
            target = target[0] if target else ""
        
        if not target:
            return SendResult(
                success=False,
                error="No target specified (to field is empty)",
                timestamp=datetime.now(timezone.utc),
            )
        
        # Send based on target type
        if self._is_conversation_id(target):
            logger.info(f"Sending message to conversation: {target[:30]}...")
            return await self._send_to_conversation(access_token, target, message)
        else:
            logger.info(f"Sending message to user: {target[:30]}...")
            return await self._send_to_user(access_token, target, message)
    
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
                timestamp=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
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
        """Async connect - initialize HTTP client for sending."""
        self._connected = True
        self._running = True
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        logger.info("DingTalk Stream adapter connected (OpenAPI ready)")
    
    async def disconnect(self) -> None:
        """Stop the adapter and close HTTP client."""
        self._running = False
        self._connected = False
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        logger.info("DingTalk Stream adapter disconnected")
    
    async def listen(self):
        """Async generator for compatibility."""
        import asyncio
        while self._running:
            await asyncio.sleep(1)
            yield None
    
    async def health_check(self) -> HealthStatus:
        if not self._connected:
            return HealthStatus.DISCONNECTED
        return HealthStatus.CONNECTED if self._running else HealthStatus.ERROR


def create_dingtalk_stream_adapter(**kwargs) -> DingTalkStreamAdapter:
    return DingTalkStreamAdapter(**kwargs)
