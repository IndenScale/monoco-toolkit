"""
Courier HTTP API - REST API for message state management.

Provides endpoints for:
- Claiming messages
- Marking messages complete
- Marking messages failed
- Health checks

Runs as part of the Courier daemon.
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import threading

from monoco.features.connector.protocol.constants import (
    API_PREFIX,
    API_MESSAGE_CLAIM,
    API_MESSAGE_COMPLETE,
    API_MESSAGE_FAIL,
    API_HEALTH,
)
from monoco.features.connector.protocol.schema import MessageStatus
from monoco.core.registry import get_inventory

from .state import LockManager, MessageStateManager, LockError


logger = logging.getLogger(__name__)


class APIError(Exception):
    """API error with status code."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "internal_error"):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class MessageNotFoundError(APIError):
    """Message not found error."""
    def __init__(self, message_id: str):
        super().__init__(f"Message '{message_id}' not found", 404, "not_found")


class CourierAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Courier API."""

    # Class-level storage (set by server)
    lock_manager: Optional[LockManager] = None
    state_manager: Optional[MessageStateManager] = None
    version: str = "1.0.0"

    # Persistent event loop for async adapters
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _loop_thread: Optional[threading.Thread] = None
    
    # DingTalk adapter singleton
    _dingtalk_adapter: Optional["DingtalkAdapter"] = None

    @classmethod
    def get_loop(cls) -> asyncio.AbstractEventLoop:
        """Get or create the background event loop."""
        import asyncio
        import threading
        if cls._loop is None:
            cls._loop = asyncio.new_event_loop()
            cls._loop_thread = threading.Thread(
                target=cls._loop.run_forever,
                daemon=True,
                name="CourierAsyncLoop"
            )
            cls._loop_thread.start()
            logger.info("Initialized persistent event loop for Courier adapters")
        return cls._loop

    @classmethod
    def get_dingtalk_adapter(cls) -> "DingtalkAdapter":
        """Get or create the DingTalk adapter singleton."""
        if cls._dingtalk_adapter is None:
            from .adapters.dingtalk import DingtalkAdapter
            # Ensure adapter uses the persistent loop
            cls.get_loop() 
            cls._dingtalk_adapter = DingtalkAdapter()
        return cls._dingtalk_adapter

    def log_message(self, format: str, *args):
        """Override to use our logger."""
        logger.debug(f"{self.client_address[0]} - {format % args}")

    def _send_json(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_error(self, error: str, status_code: int = 500, error_code: str = "error"):
        """Send error response."""
        self._send_json({
            "success": False,
            "error": error_code,
            "message": error,
        }, status_code)

    def _read_json(self) -> Optional[Dict[str, Any]]:
        """Read JSON request body."""
        content_length = self.headers.get("Content-Length")
        if not content_length:
            return None
        try:
            length = int(content_length)
            body = self.rfile.read(length).decode("utf-8")
            return json.loads(body)
        except (ValueError, json.JSONDecodeError):
            return None

    def _extract_param(self, pattern: str, path: str, param_name: str) -> Optional[str]:
        """Extract a parameter from URL path based on placeholder {name}."""
        parts = path.strip("/").split("/")
        pattern_parts = pattern.strip("/").split("/")

        if len(parts) != len(pattern_parts):
            return None

        for i, (p_part, part) in enumerate(zip(pattern_parts, parts)):
            if p_part == f"{{{param_name}}}":
                return part
            elif p_part.startswith("{") and p_part.endswith("}"):
                continue # Skip other params
            elif p_part != part:
                return None
        return None

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path == API_HEALTH or path == "/health":
                self._handle_health()
            elif path.startswith(f"{API_PREFIX}/messages/"):
                message_id = path.split("/")[-1]
                self._handle_get_message(message_id)
            else:
                self._send_error("Not found", 404, "not_found")
        except APIError as e:
            self._send_error(str(e), e.status_code, e.error_code)
        except Exception as e:
            logger.exception("Unexpected error")
            self._send_error(str(e), 500, "internal_error")

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            # Check for DingTalk multi-project webhook
            # Pattern: /api/v1/courier/webhook/dingtalk/{slug}
            webhook_pattern = f"{API_PREFIX}/webhook/dingtalk/{{slug}}"
            slug = self._extract_param(webhook_pattern, path, "slug")
            
            if slug:
                self._handle_dingtalk_webhook(slug)
                return

            # Channel-based sending (FEAT-0194)
            if path == f"{API_PREFIX}/channels/send":
                self._handle_channel_send()
                return
            elif path.startswith(f"{API_PREFIX}/channels/") and path.endswith("/send"):
                # Pattern: /api/v1/courier/channels/{channel_id}/send
                channel_id = path.split("/")[-2]
                self._handle_channel_send_by_id(channel_id)
                return
            elif path == f"{API_PREFIX}/channels":
                self._handle_channel_list()
                return
            elif path == f"{API_PREFIX}/channels/health":
                self._handle_channel_health()
                return

            # Registry management (Internal/CLI use)
            if path == f"{API_PREFIX}/registry/register":
                self._handle_registry_register()
                return
            elif path == f"{API_PREFIX}/registry/list":
                self._handle_registry_list()
                return

            # Legacy/Standard endpoints
            if "/messages/" in path and path.endswith("/claim"):
                message_id = path.split("/")[-2]
                self._handle_claim(message_id)
            elif "/messages/" in path and path.endswith("/complete"):
                message_id = path.split("/")[-2]
                self._handle_complete(message_id)
            elif "/messages/" in path and path.endswith("/fail"):
                message_id = path.split("/")[-2]
                self._handle_fail(message_id)
            else:
                self._send_error("Not found", 404, "not_found")
        except APIError as e:
            self._send_error(str(e), e.status_code, e.error_code)
        except Exception as e:
            logger.exception("Unexpected error")
            self._send_error(str(e), 500, "internal_error")

    def _handle_dingtalk_webhook(self, slug: str):
        """Handle DingTalk webhook for a specific project slug."""
        import asyncio
        from urllib.parse import parse_qs

        inventory = get_inventory()
        project = inventory.get(slug)
        if not project:
            raise APIError(f"Project slug '{slug}' not found", 404)

        # Extract signature and timestamp from query string
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        timestamp = query_params.get("timestamp", [None])[0]
        sign = query_params.get("sign", [None])[0]

        # Read payload
        data = self._read_json()
        if not data:
            raise APIError("Invalid DingTalk payload", 400)

        # Get adapter and handle webhook
        adapter = self.get_dingtalk_adapter()

        try:
            # Run async handler in the persistent background loop
            loop = self.get_loop()
            future = asyncio.run_coroutine_threadsafe(
                adapter.handle_webhook(
                    project=project,
                    payload=data,
                    sign=sign,
                    timestamp=timestamp,
                ),
                loop
            )
            # Wait for the initial response (buffered/flushed)
            result = future.result(timeout=10)

            logger.info(f"DingTalk webhook processed for '{slug}': {result}")
            self._send_json(result)

        except ValueError as e:
            logger.warning(f"DingTalk webhook validation failed for '{slug}': {e}")
            raise APIError(str(e), 401, "verification_failed")
        except Exception as e:
            logger.exception(f"DingTalk webhook processing failed for '{slug}': {e}")
            raise APIError("Internal processing error", 500, "internal_error")

    def _handle_registry_register(self):
        """Register a new project in the registry."""
        data = self._read_json()
        if not data or "slug" not in data or "path" not in data:
            raise APIError("Missing slug or path", 400)

        slug = data["slug"]
        root_path = Path(data["path"])
        
        inventory = get_inventory()
        project = inventory.register(slug, root_path, data.get("config"))
        
        self._send_json({
            "success": True, 
            "slug": slug,
            "path": str(project.path)
        })

    def _handle_registry_list(self):
        """List all registered projects."""
        inventory = get_inventory()
        mappings = []
        for p in inventory.list():
            mappings.append({
                "slug": p.slug,
                "path": str(p.path),
                "mailbox": str(p.mailbox)
            })

        self._send_json({
            "success": True,
            "projects": mappings
        })

    def _handle_channel_send(self):
        """Send message through default channel."""
        from monoco.features.channel.courier_integration import get_channel_adapter

        data = self._read_json()
        if not data:
            raise APIError("Invalid request body", 400, "invalid_body")

        message = data.get("message")
        if not message:
            raise APIError("message is required", 400, "missing_message")

        title = data.get("title")
        markdown = data.get("markdown", False)

        adapter = get_channel_adapter()
        result = adapter.send_to_default(message, title=title, markdown=markdown)

        if result.success:
            self._send_json({
                "success": True,
                "channel_id": result.channel_id,
                "message_id": result.message_id,
            })
        else:
            self._send_json({
                "success": False,
                "error": result.error,
            }, 500)

    def _handle_channel_send_by_id(self, channel_id: str):
        """Send message through specific channel."""
        from monoco.features.channel.courier_integration import get_channel_adapter

        data = self._read_json()
        if not data:
            raise APIError("Invalid request body", 400, "invalid_body")

        message = data.get("message")
        if not message:
            raise APIError("message is required", 400, "missing_message")

        title = data.get("title")
        markdown = data.get("markdown", False)

        adapter = get_channel_adapter()
        result = adapter.send_to_channel(channel_id, message, title=title, markdown=markdown)

        if result.success:
            self._send_json({
                "success": True,
                "channel_id": result.channel_id,
                "message_id": result.message_id,
            })
        else:
            self._send_json({
                "success": False,
                "error": result.error,
            }, 500 if "not found" not in (result.error or "") else 404)

    def _handle_channel_list(self):
        """List all available channels."""
        from monoco.features.channel.courier_integration import get_channel_adapter

        adapter = get_channel_adapter()
        channels = adapter.get_available_channels()

        self._send_json({
            "success": True,
            "channels": channels,
            "count": len(channels),
        })

    def _handle_channel_health(self):
        """Get channel health status."""
        from monoco.features.channel.courier_integration import get_channel_adapter

        adapter = get_channel_adapter()
        health = adapter.health_check()

        self._send_json({
            "success": True,
            "health": health,
        })

    def _handle_health(self):
        """Handle health check request."""
        inventory = get_inventory()
        projects = inventory.list()
        
        # Build adapters status
        adapters = {
            "dingtalk": {
                "status": "connected", 
                "projects": [p.slug for p in projects]
            },
            "lark": {"status": "disabled"},
            "email": {"status": "disabled"},
            "slack": {"status": "disabled"},
        }

        self._send_json({
            "status": "healthy",
            "version": self.version,
            "adapters": adapters,
            "metrics": {
                "messages_received": 0,
                "messages_sent": 0,
                "messages_claimed": 0,
                "registered_projects": len(projects),
            },
        })

    def _handle_get_message(self, message_id: str):
        """Handle get message status request."""
        if not self.lock_manager:
            raise APIError("Lock manager not initialized", 500, "not_initialized")

        lock = self.lock_manager.get_lock(message_id)
        status = lock.status if lock else MessageStatus.NEW.value

        self._send_json({
            "success": True,
            "message_id": message_id,
            "status": status,
            "lock": lock.to_dict() if lock else None,
        })

    def _handle_claim(self, message_id: str):
        """Handle message claim request."""
        if not self.lock_manager:
            raise APIError("Lock manager not initialized", 500, "not_initialized")

        data = self._read_json()
        if not data:
            raise APIError("Invalid request body", 400, "invalid_body")

        agent_id = data.get("agent_id")
        timeout = data.get("timeout", 300)

        if not agent_id:
            raise APIError("agent_id required", 400, "missing_agent_id")

        try:
            lock = self.lock_manager.claim_message(message_id, agent_id, timeout)
            self._send_json({
                "success": True,
                "message_id": message_id,
                "status": lock.status,
                "claimed_by": lock.claimed_by,
                "claimed_at": lock.claimed_at,
                "expires_at": lock.expires_at,
            })
        except LockError.MessageNotFoundError:
            raise MessageNotFoundError(message_id)
        except LockError.MessageAlreadyClaimedError as e:
            self._send_json({
                "success": False,
                "error": "already_claimed",
                "claimed_by": e.claimed_by,
                "message": str(e),
            }, 409)

    def _handle_complete(self, message_id: str):
        """Handle message complete request."""
        if not self.lock_manager or not self.state_manager:
            raise APIError("Not initialized", 500, "not_initialized")

        data = self._read_json()
        if not data:
            raise APIError("Invalid request body", 400, "invalid_body")

        agent_id = data.get("agent_id")
        if not agent_id:
            raise APIError("agent_id required", 400, "missing_agent_id")

        try:
            self.lock_manager.complete_message(message_id, agent_id)

            # Archive the message
            archived_path = self.state_manager.archive_message(message_id)

            self._send_json({
                "success": True,
                "message_id": message_id,
                "status": MessageStatus.COMPLETED.value,
                "archived_path": str(archived_path) if archived_path else None,
            })
        except LockError.MessageNotFoundError:
            raise MessageNotFoundError(message_id)
        except LockError.MessageNotClaimedError:
            self._send_json({
                "success": False,
                "error": "not_claimed",
                "message": "Message is not claimed",
            }, 409)
        except LockError.MessageClaimedByOtherError as e:
            self._send_json({
                "success": False,
                "error": "claimed_by_other",
                "message": str(e),
            }, 403)

    def _handle_fail(self, message_id: str):
        """Handle message fail request."""
        if not self.lock_manager or not self.state_manager:
            raise APIError("Not initialized", 500, "not_initialized")

        data = self._read_json()
        if not data:
            raise APIError("Invalid request body", 400, "invalid_body")

        agent_id = data.get("agent_id")
        reason = data.get("reason", "")
        retryable = data.get("retryable", True)

        if not agent_id:
            raise APIError("agent_id required", 400, "missing_agent_id")

        try:
            lock = self.lock_manager.fail_message(message_id, agent_id, reason, retryable)

            # Move to deadletter if not retryable
            deadletter_path = None
            if lock.status == MessageStatus.DEADLETTER.value:
                deadletter_path = self.state_manager.move_to_deadletter(message_id)

            self._send_json({
                "success": True,
                "message_id": message_id,
                "status": lock.status,
                "retry_count": lock.retry_count,
                "deadletter_path": str(deadletter_path) if deadletter_path else None,
            })
        except LockError.MessageNotFoundError:
            raise MessageNotFoundError(message_id)
        except LockError.MessageNotClaimedError:
            self._send_json({
                "success": False,
                "error": "not_claimed",
                "message": "Message is not claimed",
            }, 409)
        except LockError.MessageClaimedByOtherError as e:
            self._send_json({
                "success": False,
                "error": "claimed_by_other",
                "message": str(e),
            }, 403)


class CourierAPIServer:
    """HTTP API server for Courier."""

    def __init__(
        self,
        lock_manager: LockManager,
        state_manager: MessageStateManager,
        host: str = "localhost",
        port: int = 8080,
    ):
        self.lock_manager = lock_manager
        self.state_manager = state_manager
        self.host = host
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

    def start(self) -> None:
        """Start the API server."""
        # Set class-level references for handler
        CourierAPIHandler.lock_manager = self.lock_manager
        CourierAPIHandler.state_manager = self.state_manager

        self._server = HTTPServer((self.host, self.port), CourierAPIHandler)

        # Run in a thread so it doesn't block
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

        logger.info(f"API server started on {self.host}:{self.port}")

    def _run(self) -> None:
        """Run the server loop."""
        while not self._shutdown_event.is_set():
            self._server.handle_request()

    def stop(self) -> None:
        """Stop the API server."""
        self._shutdown_event.set()
        if self._server:
            # Trigger one more request to exit the loop
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"http://{self.host}:{self.port}/health",
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=1):
                    pass
            except Exception:
                pass
            self._server.server_close()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("API server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._thread is not None and self._thread.is_alive()
