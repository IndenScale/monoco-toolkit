"""
DingTalk Adapter - Handles DingTalk specific webhook processing and signature verification.

This module provides:
- DingtalkSigner: Signature verification helper
- DingtalkAdapter: Full adapter with debouncing and storage integration
"""

import asyncio
import base64
import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from monoco.core.config import get_config
from monoco.core.registry import ProjectInventoryEntry
from monoco.features.connector.protocol.schema import (
    Content,
    ContentType,
    InboundMessage,
    Participant,
    Provider,
    Session,
    SessionType,
)
from monoco.features.mailbox.models import MailboxConfig
from monoco.features.mailbox.store import MailboxStore

from ..debounce import DebounceConfig, DebounceHandler
from .dingtalk_artifacts import DingTalkArtifactDownloader

logger = logging.getLogger(__name__)


class DingtalkSigner:
    """Helper for DingTalk signature verification."""

    @staticmethod
    def verify(timestamp: str, sign: str, secret: str) -> bool:
        """
        Verify the DingTalk signature.

        Args:
            timestamp: The timestamp from the query string
            sign: The signature from the query string
            secret: The app secret for the bot

        Returns:
            True if signature is valid, False otherwise
        """
        if not secret:
            logger.warning("No secret provided for DingTalk signature verification")
            return False

        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        calculated_sign = base64.b64encode(hmac_code).decode("utf-8")
        return calculated_sign == sign

    @staticmethod
    def is_timestamp_valid(timestamp_str: str, window_seconds: int = 3600) -> bool:
        """Check if the timestamp is within a reasonable window."""
        try:
            timestamp = int(timestamp_str) / 1000  # DingTalk uses ms
            now = time.time()
            return abs(now - timestamp) < window_seconds
        except (ValueError, TypeError):
            return False


class DingtalkAdapter:
    """
    DingTalk webhook adapter with debouncing and multi-tenant support.

    This adapter handles DingTalk bot webhooks, implementing:
    - Signature verification using project-specific secrets
    - Debouncing for IM streaming input (5s window, 30s max)
    - Standardization to InboundMessage format
    - Atomic storage to project's mailbox
    """

    def __init__(
        self,
        debounce_config: Optional[DebounceConfig] = None,
    ):
        """
        Initialize the DingTalk adapter.

        Args:
            debounce_config: Configuration for debounce behavior.
                           Defaults to 5s window, 30s max wait.
        """
        self.debounce_config = debounce_config or DebounceConfig(
            window_ms=5000,  # 5 second window
            max_wait_ms=30000,  # 30 second max wait
        )

        # Map: project_slug -> DebounceHandler
        self._debouncers: Dict[str, DebounceHandler] = {}

        # Map: project_slug -> MailboxStore
        self._stores: Dict[str, MailboxStore] = {}

        # Map: project_slug -> DingTalkArtifactDownloader
        self._artifact_downloaders: Dict[str, DingTalkArtifactDownloader] = {}

        self._lock = asyncio.Lock()

    async def handle_webhook(
        self,
        project: ProjectInventoryEntry,
        payload: Dict[str, Any],
        sign: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle a DingTalk webhook for a specific project.

        Args:
            project: The project inventory entry (contains config and paths)
            payload: The JSON payload from DingTalk
            sign: Optional signature for verification
            timestamp: Optional timestamp for verification

        Returns:
            Response dict with success status and message info

        Raises:
            ValueError: If signature verification fails or payload is invalid
        """
        slug = project.slug

        # 1. Verify signature if secret is configured
        secret = project.config.get("dingtalk_secret") if project.config else None
        if secret and sign and timestamp:
            if not DingtalkSigner.verify(timestamp, sign, secret):
                logger.warning(f"Signature verification failed for project '{slug}'")
                raise ValueError("Signature verification failed")

            if not DingtalkSigner.is_timestamp_valid(timestamp):
                logger.warning(f"Timestamp expired for project '{slug}'")
                raise ValueError("Timestamp expired")

        # 2. Parse and validate payload (async for attachment downloading)
        message = await self._parse_payload(payload, project)
        if not message:
            raise ValueError("Failed to parse DingTalk payload")

        # 3. Get or create debounce handler for this project
        debouncer = await self._get_debouncer(slug, project)

        # 4. Add message to debounce buffer
        flushed = await debouncer.add(message)

        if flushed:
            # Immediate flush (window expired or max wait reached)
            await self._write_messages(slug, project, flushed)
            return {
                "success": True,
                "action": "flushed",
                "message_count": len(flushed),
            }

        return {
            "success": True,
            "action": "buffered",
            "message_id": message.id,
        }

    async def _parse_payload(
        self,
        payload: Dict[str, Any],
        project: ProjectInventoryEntry,
    ) -> Optional[InboundMessage]:
        """
        Parse DingTalk payload into standardized InboundMessage.

        Supports multiple DingTalk event types:
        - chatbot_message: Direct bot messages
        - conversation: Group chat messages

        Also downloads any attachments and stores them in the artifact store.
        """
        try:
            # Extract message info based on DingTalk format
            msg_type = payload.get("msgtype", "text")

            # Get sender info
            sender_staff_id = payload.get("senderStaffId") or payload.get(
                "sender", {}
            ).get("staff_id")
            sender_nick = payload.get("senderNick") or payload.get("sender", {}).get(
                "nick"
            )

            # Get conversation info
            conversation_id = payload.get("conversationId") or payload.get(
                "conversation", {}
            ).get("id")
            conversation_title = payload.get("conversationTitle") or payload.get(
                "conversation", {}
            ).get("title")
            chat_type = payload.get("chatType") or payload.get("conversation", {}).get(
                "type", ""
            )

            # Determine session type
            session_type = SessionType.GROUP if chat_type == "2" else SessionType.DIRECT

            # Extract content based on message type
            content_text = ""
            if msg_type == "text" and "text" in payload:
                content_text = payload["text"].get("content", "")
            elif msg_type == "markdown" and "markdown" in payload:
                content_text = payload["markdown"].get("text", "")
            else:
                # Try to extract from various payload formats
                content_text = payload.get("content", str(payload))

            # Generate message ID
            msg_id = payload.get("msgId") or payload.get("messageId")
            if not msg_id:
                # Generate from content hash if not provided
                import hashlib

                content_hash = hashlib.sha256(
                    f"{sender_staff_id}:{conversation_id}:{content_text}".encode()
                ).hexdigest()[:16]
                msg_id = content_hash

            message_id = f"{Provider.DINGTALK.value}_{msg_id}"

            # Download attachments if any
            artifacts = []
            if msg_type in ("image", "file", "voice", "video", "rich"):
                try:
                    downloader = await self._get_artifact_downloader(project)
                    artifacts = await downloader.download_from_payload(
                        payload=payload,
                        message_id=message_id,
                    )
                    if artifacts:
                        logger.info(
                            f"Downloaded {len(artifacts)} attachments for {message_id}"
                        )
                except Exception as e:
                    logger.exception(f"Failed to download attachments: {e}")
                    # Continue without attachments rather than failing the entire message

            # Build standardized message
            return InboundMessage(
                id=message_id,
                provider=Provider.DINGTALK,
                session=Session(
                    id=conversation_id or sender_staff_id or "unknown",
                    type=session_type,
                    name=conversation_title,
                    thread_key=None,  # DingTalk doesn't have explicit threads in webhook
                ),
                participants={
                    "from": {
                        "id": sender_staff_id or "unknown",
                        "name": sender_nick or "Unknown",
                        "platform_id": sender_staff_id,
                    },
                    "to": [],  # Bot is the recipient
                },
                timestamp=datetime.now(
                    timezone.utc
                ),  # DingTalk provides createAt in ms
                received_at=datetime.now(timezone.utc),
                type=ContentType.TEXT if msg_type == "text" else ContentType.MARKDOWN,
                content=Content(
                    text=content_text if msg_type == "text" else None,
                    markdown=content_text if msg_type == "markdown" else None,
                ),
                artifacts=artifacts,
                metadata={
                    "dingtalk_raw": payload,
                    "msg_type": msg_type,
                    "conversation_id": conversation_id,
                    "attachment_count": len(artifacts),
                },
            )

        except Exception as e:
            logger.exception(f"Failed to parse DingTalk payload: {e}")
            return None

    async def _get_debouncer(
        self,
        slug: str,
        project: ProjectInventoryEntry,
    ) -> DebounceHandler:
        """Get or create a debounce handler for the project."""
        if slug not in self._debouncers:
            async with self._lock:
                if slug not in self._debouncers:
                    self._debouncers[slug] = DebounceHandler(
                        config=self.debounce_config,
                        flush_callback=lambda msgs: asyncio.create_task(
                            self._write_messages(slug, project, msgs)
                        ),
                    )
        return self._debouncers[slug]

    async def _write_messages(
        self,
        slug: str,
        project: ProjectInventoryEntry,
        messages: List[InboundMessage],
    ) -> None:
        """Write debounced messages to the project's mailbox."""
        # Get or create mailbox store for this project
        store = await self._get_store(slug, project)

        for message in messages:
            try:
                path = store.create_inbound_message(message)
                logger.info(f"Wrote message {message.id} to {path}")
            except Exception as e:
                logger.error(f"Failed to write message {message.id}: {e}")

    async def _get_store(
        self,
        slug: str,
        project: ProjectInventoryEntry,
    ) -> MailboxStore:
        """Get or create a mailbox store for the project."""
        if slug not in self._stores:
            async with self._lock:
                if slug not in self._stores:
                    config = MailboxConfig(
                        root_path=project.mailbox,
                    )
                    self._stores[slug] = MailboxStore(config)
        return self._stores[slug]

    async def _get_artifact_downloader(
        self,
        project: ProjectInventoryEntry,
    ) -> DingTalkArtifactDownloader:
        """Get or create an artifact downloader for the project."""
        slug = project.slug
        if slug not in self._artifact_downloaders:
            async with self._lock:
                if slug not in self._artifact_downloaders:
                    # Get global artifacts directory
                    config = get_config()
                    artifacts_dir = (
                        Path(config.paths.root).expanduser() / ".monoco" / "artifacts"
                    )

                    # Get DingTalk credentials from project config
                    client_id = ""
                    client_secret = ""
                    if project.config:
                        client_id = project.config.get("dingtalk_client_id", "")
                        client_secret = project.config.get("dingtalk_secret", "")

                    self._artifact_downloaders[slug] = DingTalkArtifactDownloader(
                        artifacts_dir=artifacts_dir,
                        client_id=client_id,
                        client_secret=client_secret,
                    )
        return self._artifact_downloaders[slug]

    async def flush_project(self, slug: str) -> Dict[str, Any]:
        """
        Force flush all pending messages for a project.

        Args:
            slug: Project slug

        Returns:
            Flush result with message counts
        """
        debouncer = self._debouncers.get(slug)
        if not debouncer:
            return {"success": True, "flushed": 0}

        results = await debouncer.flush_all()
        total = sum(len(msgs) for msgs in results.values())

        return {
            "success": True,
            "flushed": total,
            "buffers": len(results),
        }

    async def get_stats(self, slug: Optional[str] = None) -> Dict[str, Any]:
        """
        Get adapter statistics.

        Args:
            slug: Optional project slug to filter by

        Returns:
            Statistics dict
        """
        if slug:
            debouncer = self._debouncers.get(slug)
            if debouncer:
                return {
                    "project": slug,
                    "pending": debouncer.get_pending_count(),
                    "buffers": len(debouncer.get_buffer_keys()),
                }
            return {"project": slug, "pending": 0, "buffers": 0}

        # Global stats
        total_pending = sum(d.get_pending_count() for d in self._debouncers.values())
        return {
            "projects": len(self._debouncers),
            "total_pending": total_pending,
        }

    def shutdown(self) -> None:
        """Shutdown the adapter and flush all pending messages."""
        for debouncer in self._debouncers.values():
            debouncer.shutdown()
