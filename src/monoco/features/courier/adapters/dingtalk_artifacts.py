"""
DingTalk Artifact Download - Handles attachment downloads from DingTalk.

Uses DingTalk OpenAPI to download media files (images, documents, etc.)
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

from monoco.features.connector.protocol.schema import Artifact, ArtifactType, Provider
from monoco.features.artifact.store import ArtifactStore

logger = logging.getLogger(__name__)


class DingTalkArtifactDownloader:
    """Download and store attachments from DingTalk messages."""

    API_BASE = "https://api.dingtalk.com"

    def __init__(
        self,
        artifacts_dir: Path,
        client_id: str = "",
        client_secret: str = "",
        access_token: Optional[str] = None,
    ):
        self.store = ArtifactStore(artifacts_dir)
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = access_token
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    def _get_access_token(self) -> Optional[str]:
        """Get cached or provided access token."""
        return self._access_token

    async def _download_media(
        self,
        download_url: str,
        filename: str,
        message_id: str,
        mime_type: Optional[str] = None,
    ) -> Optional[Tuple[Artifact, Path]]:
        """
        Download media from URL and store as artifact.

        Args:
            download_url: Direct download URL
            filename: Original filename
            message_id: Associated message ID
            mime_type: Optional MIME type

        Returns:
            Tuple of (Artifact, storage_path) or None if failed
        """
        try:
            client = await self._get_http_client()

            logger.debug(f"Downloading media from {download_url[:50]}...")
            response = await client.get(download_url, follow_redirects=True)
            response.raise_for_status()

            content = response.content
            if not content:
                logger.warning(f"Empty content from {download_url}")
                return None

            # Store in artifact store
            artifact, path = self.store.store(
                content=content,
                original_name=filename,
                message_id=message_id,
                provider=Provider.DINGTALK.value,
                mime_type=mime_type or response.headers.get("content-type"),
                url=download_url,
            )

            logger.info(f"Downloaded and stored artifact: {artifact.id[:16]}... ({len(content)} bytes)")
            return artifact, path

        except Exception as e:
            logger.exception(f"Failed to download media: {e}")
            return None

    async def _get_download_url_from_media_id(
        self,
        media_id: str,
    ) -> Optional[str]:
        """
        Get download URL from DingTalk media_id.

        Note: DingTalk doesn't have a direct "get download URL" API.
        Media files need to be handled based on message type.
        For now, we rely on URLs provided in webhook payloads.
        """
        # DingTalk media download is context-dependent
        # Some message types include downloadCode or direct URLs
        logger.debug(f"Media ID resolution not implemented for: {media_id}")
        return None

    async def download_from_payload(
        self,
        payload: Dict,
        message_id: str,
    ) -> List[Artifact]:
        """
        Extract and download attachments from DingTalk message payload.

        Args:
            payload: DingTalk webhook payload
            message_id: Generated message ID

        Returns:
            List of downloaded artifacts
        """
        artifacts = []
        msg_type = payload.get("msgtype", "text")

        # Handle different message types with attachments
        if msg_type == "image":
            artifact = await self._handle_image(payload, message_id)
            if artifact:
                artifacts.append(artifact)

        elif msg_type == "file":
            artifact = await self._handle_file(payload, message_id)
            if artifact:
                artifacts.append(artifact)

        elif msg_type == "voice":
            artifact = await self._handle_voice(payload, message_id)
            if artifact:
                artifacts.append(artifact)

        elif msg_type == "video":
            artifact = await self._handle_video(payload, message_id)
            if artifact:
                artifacts.append(artifact)

        # Handle rich content that might have attachments
        elif msg_type == "rich":
            rich_artifacts = await self._handle_rich_content(payload, message_id)
            artifacts.extend(rich_artifacts)

        return artifacts

    async def _handle_image(
        self,
        payload: Dict,
        message_id: str,
    ) -> Optional[Artifact]:
        """Handle image message type."""
        image_data = payload.get("image", {})
        if not image_data:
            return None

        # DingTalk provides picUrl for images in some contexts
        pic_url = image_data.get("picUrl") or payload.get("picUrl")
        media_id = image_data.get("mediaId") or image_data.get("media_id")

        download_url = pic_url
        if not download_url and media_id:
            # Try to resolve media_id to URL (if API available)
            download_url = await self._get_download_url_from_media_id(media_id)

        if not download_url:
            return None

        # Generate filename from URL or use default
        parsed = urlparse(download_url)
        filename = Path(parsed.path).name or f"image_{media_id or 'unknown'}.jpg"

        result = await self._download_media(
            download_url=download_url,
            filename=filename,
            message_id=message_id,
            mime_type="image/jpeg",  # DingTalk images are usually JPEG
        )

        return result[0] if result else None

    async def _handle_file(
        self,
        payload: Dict,
        message_id: str,
    ) -> Optional[Artifact]:
        """Handle file message type."""
        file_data = payload.get("content", {}) or payload.get("file", {})
        if not file_data:
            return None

        # File messages might have downloadUrl or need media_id resolution
        download_url = file_data.get("downloadUrl") or file_data.get("download_url")
        media_id = file_data.get("mediaId") or file_data.get("media_id")
        filename = file_data.get("fileName", "unknown_file")

        if not download_url and media_id:
            download_url = await self._get_download_url_from_media_id(media_id)

        if not download_url:
            return None

        result = await self._download_media(
            download_url=download_url,
            filename=filename,
            message_id=message_id,
            mime_type=file_data.get("contentType"),
        )

        return result[0] if result else None

    async def _handle_voice(
        self,
        payload: Dict,
        message_id: str,
    ) -> Optional[Artifact]:
        """Handle voice/audio message type."""
        voice_data = payload.get("content", {}) or payload.get("voice", {})
        if not voice_data:
            return None

        download_url = voice_data.get("downloadUrl") or voice_data.get("download_url")
        media_id = voice_data.get("mediaId") or voice_data.get("media_id")
        duration = voice_data.get("duration", 0)

        if not download_url and media_id:
            download_url = await self._get_download_url_from_media_id(media_id)

        if not download_url:
            return None

        filename = f"voice_{duration}s.amr"  # DingTalk voice is usually AMR format

        result = await self._download_media(
            download_url=download_url,
            filename=filename,
            message_id=message_id,
            mime_type="audio/amr",
        )

        return result[0] if result else None

    async def _handle_video(
        self,
        payload: Dict,
        message_id: str,
    ) -> Optional[Artifact]:
        """Handle video message type."""
        video_data = payload.get("content", {}) or payload.get("video", {})
        if not video_data:
            return None

        download_url = video_data.get("downloadUrl") or video_data.get("download_url")
        media_id = video_data.get("mediaId") or video_data.get("media_id")
        filename = video_data.get("filename", "video.mp4")

        if not download_url and media_id:
            download_url = await self._get_download_url_from_media_id(media_id)

        if not download_url:
            return None

        result = await self._download_media(
            download_url=download_url,
            filename=filename,
            message_id=message_id,
            mime_type="video/mp4",
        )

        return result[0] if result else None

    async def _handle_rich_content(
        self,
        payload: Dict,
        message_id: str,
    ) -> List[Artifact]:
        """Handle rich content that might contain multiple attachments."""
        artifacts = []
        # Rich content might have nested attachments
        # This is a placeholder for future expansion
        return artifacts

    def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            # Note: httpx.AsyncClient should be closed async
            # This is a synchronous cleanup method
            pass

    async def aclose(self) -> None:
        """Async close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
