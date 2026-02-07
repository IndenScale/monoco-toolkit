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

    def _extract_message_id(self, pattern: str, path: str) -> Optional[str]:
        """Extract message ID from URL path."""
        # pattern: /api/v1/messages/{id}/claim
        # path: /api/v1/messages/lark_abc123/claim
        parts = path.strip("/").split("/")
        pattern_parts = pattern.strip("/").split("/")

        if len(parts) != len(pattern_parts):
            return None

        for i, (p_part, part) in enumerate(zip(pattern_parts, parts)):
            if p_part == "{id}":
                return part
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
            # Check for claim endpoint
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

    def _handle_health(self):
        """Handle health check request."""
        # Build adapters status
        adapters = {
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
