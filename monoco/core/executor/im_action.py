"""
SendIMAction - Action for sending notifications.

Part of Layer 3 (Action Executor) in the event automation framework.
Provides action for sending IM/webhook notifications.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from monoco.core.scheduler import AgentEvent
from monoco.core.router import Action, ActionResult

logger = logging.getLogger(__name__)


class NotificationResult:
    """Result of a notification send."""
    
    def __init__(
        self,
        success: bool,
        message: str,
        response: Optional[Any] = None,
    ):
        self.success = success
        self.message = message
        self.response = response


class SendIMAction(Action):
    """
    Action that sends notifications via IM or webhook.
    
    This action sends notifications to various channels:
    - Webhook (HTTP POST)
    - Console (stdout)
    - File (append to log file)
    
    Future: Slack, Discord, Email, etc.
    
    Example:
        >>> action = SendIMAction(
        ...     channel="webhook",
        ...     webhook_url="https://hooks.example.com/notify",
        ...     message_template="Issue {issue_id} updated to {new_stage}",
        ... )
        >>> result = await action(event)
    """
    
    def __init__(
        self,
        channel: str = "console",
        message_template: str = "{event_type}: {payload}",
        webhook_url: Optional[str] = None,
        webhook_headers: Optional[Dict[str, str]] = None,
        log_file: Optional[str] = None,
        timeout: int = 30,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self.channel = channel
        self.message_template = message_template
        self.webhook_url = webhook_url
        self.webhook_headers = webhook_headers or {}
        self.log_file = log_file
        self.timeout = timeout
        self._last_result: Optional[NotificationResult] = None
    
    @property
    def name(self) -> str:
        return f"SendIMAction({self.channel})"
    
    async def can_execute(self, event: AgentEvent) -> bool:
        """Check if the channel is available."""
        if self.channel == "webhook":
            return self.webhook_url is not None
        elif self.channel == "file":
            return self.log_file is not None
        elif self.channel == "console":
            return True
        return False
    
    async def execute(self, event: AgentEvent) -> ActionResult:
        """Send notification."""
        # Format message
        message = self._format_message(event)
        
        logger.debug(f"Sending {self.channel} notification: {message[:100]}...")
        
        try:
            if self.channel == "webhook":
                result = await self._send_webhook(message, event)
            elif self.channel == "file":
                result = await self._write_to_file(message)
            else:  # console
                result = await self._send_console(message)
            
            self._last_result = result
            
            if result.success:
                return ActionResult.success_result(
                    output={
                        "channel": self.channel,
                        "message_sent": True,
                    },
                    metadata={
                        "message_preview": message[:200],
                    },
                )
            else:
                return ActionResult.failure_result(
                    error=result.message,
                    metadata={
                        "channel": self.channel,
                    },
                )
        
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return ActionResult.failure_result(error=str(e))
    
    def _format_message(self, event: AgentEvent) -> str:
        """Format notification message with event data."""
        try:
            return self.message_template.format(
                event_type=event.type.value,
                timestamp=event.timestamp.isoformat(),
                source=event.source or "unknown",
                **event.payload,
            )
        except (KeyError, ValueError) as e:
            # If formatting fails, return a simple message
            return f"Event: {event.type.value} at {event.timestamp.isoformat()}"
    
    async def _send_webhook(
        self,
        message: str,
        event: AgentEvent,
    ) -> NotificationResult:
        """Send notification via webhook."""
        try:
            import aiohttp
        except ImportError:
            # Fallback to sync requests
            return await self._send_webhook_sync(message, event)
        
        payload = {
            "message": message,
            "event_type": event.type.value,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "payload": event.payload,
        }
        
        headers = {
            "Content-Type": "application/json",
            **self.webhook_headers,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status < 400:
                        return NotificationResult(
                            success=True,
                            message=f"Webhook sent: HTTP {response.status}",
                            response={
                                "status": response.status,
                                "body": await response.text(),
                            },
                        )
                    else:
                        return NotificationResult(
                            success=False,
                            message=f"Webhook failed: HTTP {response.status}",
                            response={"status": response.status},
                        )
        except Exception as e:
            return NotificationResult(
                success=False,
                message=f"Webhook error: {str(e)}",
            )
    
    async def _send_webhook_sync(
        self,
        message: str,
        event: AgentEvent,
    ) -> NotificationResult:
        """Send webhook using sync requests (fallback)."""
        try:
            import requests
        except ImportError:
            return NotificationResult(
                success=False,
                message="Neither aiohttp nor requests available for webhook",
            )
        
        payload = {
            "message": message,
            "event_type": event.type.value,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "payload": event.payload,
        }
        
        headers = {
            "Content-Type": "application/json",
            **self.webhook_headers,
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            
            if response.status_code < 400:
                return NotificationResult(
                    success=True,
                    message=f"Webhook sent: HTTP {response.status_code}",
                    response={
                        "status": response.status_code,
                        "body": response.text,
                    },
                )
            else:
                return NotificationResult(
                    success=False,
                    message=f"Webhook failed: HTTP {response.status_code}",
                )
        except Exception as e:
            return NotificationResult(
                success=False,
                message=f"Webhook error: {str(e)}",
            )
    
    async def _write_to_file(self, message: str) -> NotificationResult:
        """Write notification to log file."""
        try:
            import aiofiles
        except ImportError:
            # Fallback to sync file write
            return await self._write_to_file_sync(message)
        
        try:
            timestamp = asyncio.get_event_loop().time()
            log_line = f"[{timestamp}] {message}\n"
            
            async with aiofiles.open(self.log_file, "a") as f:
                await f.write(log_line)
            
            return NotificationResult(
                success=True,
                message=f"Written to {self.log_file}",
            )
        except Exception as e:
            return NotificationResult(
                success=False,
                message=f"File write error: {str(e)}",
            )
    
    async def _write_to_file_sync(self, message: str) -> NotificationResult:
        """Write to file synchronously (fallback)."""
        try:
            import time
            log_line = f"[{time.time()}] {message}\n"
            
            with open(self.log_file, "a") as f:
                f.write(log_line)
            
            return NotificationResult(
                success=True,
                message=f"Written to {self.log_file}",
            )
        except Exception as e:
            return NotificationResult(
                success=False,
                message=f"File write error: {str(e)}",
            )
    
    async def _send_console(self, message: str) -> NotificationResult:
        """Print notification to console."""
        print(f"[NOTIFICATION] {message}")
        return NotificationResult(
            success=True,
            message="Printed to console",
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get action statistics."""
        stats = super().get_stats()
        stats.update({
            "channel": self.channel,
            "webhook_configured": self.webhook_url is not None,
            "log_file": self.log_file,
        })
        return stats
