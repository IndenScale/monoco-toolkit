"""
Courier Client - HTTP client for Courier API communication.

This module provides the client for Mailbox CLI to communicate with Courier service.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import urljoin
import json
import socket

from monoco.features.connector.protocol.constants import (
    API_PREFIX,
    API_MESSAGE_CLAIM,
    API_MESSAGE_COMPLETE,
    API_MESSAGE_FAIL,
    CLAIM_TIMEOUT_SECONDS,
)

from .models import LockInfo, MessageStatus


class CourierError(Exception):
    """Base exception for Courier client errors."""
    pass


class CourierNotRunningError(CourierError):
    """Raised when Courier service is not running."""
    pass


class MessageAlreadyClaimedError(CourierError):
    """Raised when trying to claim a message that's already claimed."""
    def __init__(self, message: str, claimed_by: Optional[str] = None):
        super().__init__(message)
        self.claimed_by = claimed_by


class MessageNotFoundError(CourierError):
    """Raised when a message is not found."""
    pass


class CourierClient:
    """
    HTTP client for Courier API.

    Handles communication with the Courier service for:
    - Claiming messages
    - Marking messages as complete
    - Marking messages as failed
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_prefix: str = API_PREFIX,
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_prefix = api_prefix
        self.timeout = timeout

    def _make_url(self, endpoint: str) -> str:
        """Build full URL from endpoint path."""
        return urljoin(f"{self.base_url}/", f"{self.api_prefix.lstrip('/')}/{endpoint.lstrip('/')}")

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Courier API.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Response JSON as dictionary

        Raises:
            CourierNotRunningError: If Courier is not reachable
            CourierError: For other API errors
        """
        url = self._make_url(endpoint)

        headers = {"Content-Type": "application/json"}
        body = json.dumps(data).encode("utf-8") if data else None

        req = Request(
            url,
            data=body,
            headers=headers,
            method=method,
        )

        try:
            with urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except socket.timeout:
            raise CourierNotRunningError("Courier service timeout - service may be slow or unresponsive")
        except URLError as e:
            if "Connection refused" in str(e) or "Name or service not known" in str(e):
                raise CourierNotRunningError("Courier service not running. Start with: monoco courier start")
            raise CourierError(f"Request failed: {e}")
        except Exception as e:
            raise CourierError(f"Unexpected error: {e}")

    def health_check(self) -> bool:
        """
        Check if Courier service is running.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            req = Request(url, method="GET")
            with urlopen(req, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    def claim_message(
        self,
        message_id: str,
        agent_id: str,
        timeout: int = CLAIM_TIMEOUT_SECONDS,
    ) -> LockInfo:
        """
        Claim a message for processing.

        Args:
            message_id: Message identifier
            agent_id: Agent claiming the message
            timeout: Claim timeout in seconds

        Returns:
            LockInfo with claim details

        Raises:
            CourierNotRunningError: If Courier is not running
            MessageNotFoundError: If message doesn't exist
            MessageAlreadyClaimedError: If message is already claimed
        """
        endpoint = API_MESSAGE_CLAIM.format(id=message_id)
        data = {
            "agent_id": agent_id,
            "timeout": timeout,
        }

        response = self._request("POST", endpoint, data)

        if not response.get("success"):
            error = response.get("error", "unknown_error")

            if error == "not_found":
                raise MessageNotFoundError(f"Message '{message_id}' not found")

            if error == "already_claimed":
                claimed_by = response.get("claimed_by")
                raise MessageAlreadyClaimedError(
                    f"Message already claimed by {claimed_by}",
                    claimed_by=claimed_by,
                )

            raise CourierError(f"Claim failed: {error}")

        return LockInfo(
            message_id=response["message_id"],
            status=MessageStatus.CLAIMED,
            claimed_by=response.get("claimed_by"),
            claimed_at=datetime.fromisoformat(response["claimed_at"].replace("Z", "+00:00")) if response.get("claimed_at") else None,
            expires_at=datetime.fromisoformat(response["expires_at"].replace("Z", "+00:00")) if response.get("expires_at") else None,
        )

    def complete_message(
        self,
        message_id: str,
        agent_id: str,
    ) -> None:
        """
        Mark a message as complete.

        Args:
            message_id: Message identifier
            agent_id: Agent completing the message

        Raises:
            CourierNotRunningError: If Courier is not running
            MessageNotFoundError: If message doesn't exist
            CourierError: If message not claimed by this agent
        """
        endpoint = API_MESSAGE_COMPLETE.format(id=message_id)
        data = {"agent_id": agent_id}

        response = self._request("POST", endpoint, data)

        if not response.get("success"):
            error = response.get("error", "unknown_error")

            if error == "not_found":
                raise MessageNotFoundError(f"Message '{message_id}' not found")

            if error == "not_claimed":
                raise CourierError(f"Message not claimed by current agent")

            raise CourierError(f"Complete failed: {error}")

    def fail_message(
        self,
        message_id: str,
        agent_id: str,
        reason: str = "",
        retryable: bool = True,
    ) -> None:
        """
        Mark a message as failed.

        Args:
            message_id: Message identifier
            agent_id: Agent failing the message
            reason: Failure reason
            retryable: Whether the failure is retryable

        Raises:
            CourierNotRunningError: If Courier is not running
            MessageNotFoundError: If message doesn't exist
            CourierError: If message not claimed by this agent
        """
        endpoint = API_MESSAGE_FAIL.format(id=message_id)
        data = {
            "agent_id": agent_id,
            "reason": reason,
            "retryable": retryable,
        }

        response = self._request("POST", endpoint, data)

        if not response.get("success"):
            error = response.get("error", "unknown_error")

            if error == "not_found":
                raise MessageNotFoundError(f"Message '{message_id}' not found")

            if error == "not_claimed":
                raise CourierError(f"Message not claimed by current agent")

            raise CourierError(f"Fail failed: {error}")

    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get the status of a message.

        Args:
            message_id: Message identifier

        Returns:
            Message status information

        Raises:
            CourierNotRunningError: If Courier is not running
            MessageNotFoundError: If message doesn't exist
        """
        endpoint = f"/messages/{message_id}"

        response = self._request("GET", endpoint)

        if not response.get("success"):
            error = response.get("error", "unknown_error")

            if error == "not_found":
                raise MessageNotFoundError(f"Message '{message_id}' not found")

            raise CourierError(f"Status check failed: {error}")

        return response


# Global client instance
_client: Optional[CourierClient] = None


def get_courier_client(
    base_url: Optional[str] = None,
    api_prefix: Optional[str] = None,
) -> CourierClient:
    """
    Get or create the global Courier client instance.

    Args:
        base_url: Optional base URL (uses default if not provided)
        api_prefix: Optional API prefix

    Returns:
        CourierClient instance
    """
    global _client
    if _client is None:
        kwargs = {}
        if base_url:
            kwargs["base_url"] = base_url
        if api_prefix:
            kwargs["api_prefix"] = api_prefix
        _client = CourierClient(**kwargs)
    return _client
