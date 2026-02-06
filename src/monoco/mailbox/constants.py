"""
Mailbox Protocol Constants.

This module defines directory paths, filename patterns, and timing constants
for the Mailbox protocol.
"""

from pathlib import Path

# =============================================================================
# Directory Structure
# =============================================================================

MAILBOX_DIR = Path(".monoco/mailbox")
"""Root mailbox directory (relative to project root)."""

INBOUND_DIR = MAILBOX_DIR / "inbound"
"""Inbound messages from external providers."""

OUTBOUND_DIR = MAILBOX_DIR / "outbound"
"""Outbound messages to be sent by Courier."""

ARCHIVE_DIR = MAILBOX_DIR / "archive"
"""Archived messages (completed lifecycle)."""

DROPZONE_DIR = Path(".monoco/dropzone")
"""Attachment dropzone for Mailroom processing."""

# =============================================================================
# Directory Structure (Mirrored with Provider Subdirectories)
# =============================================================================

PROVIDER_SUBDIRS = ["lark", "email", "discord", "slack", "wechat", "telegram", "custom"]
"""Provider-specific subdirectories under inbound/outbound/archive."""

# =============================================================================
# Filename Patterns
# =============================================================================

# Format: {ISO8601}_{Provider}_{UID}.md
# Example: 20260206T204530_lark_abc123.md
INBOUND_FILENAME_PATTERN = "{timestamp:%Y%m%dT%H%M%S}_{provider}_{uid}.md"
OUTBOUND_FILENAME_PATTERN = "{timestamp:%Y%m%dT%H%M%S}_{provider}_{uid}.md"
DRAFT_FILENAME_PATTERN = "draft_{timestamp:%Y%m%dT%H%M%S}_{uid}.md"

# =============================================================================
# Debounce Windows (Courier-side)
# =============================================================================

DEFAULT_DEBOUNCE_WINDOW_IM = 30  # seconds
"""Default debounce window for IM messages (streaming chat)."""

DEFAULT_DEBOUNCE_WINDOW_EMAIL = 0  # seconds
"""Default debounce window for Email (atomic, no debounce)."""

# =============================================================================
# Size Limits
# =============================================================================

MAX_MESSAGE_SIZE_BYTES = 1024 * 1024  # 1 MB
"""Maximum message content size."""

MAX_ARTIFACTS_PER_MESSAGE = 10
"""Maximum number of artifacts per message."""

MAX_FILENAME_LENGTH = 255
"""Maximum filename length (filesystem limit)."""

# =============================================================================
# YAML Frontmatter Settings
# =============================================================================

YAML_START = "---\n"
YAML_END = "---\n"

# =============================================================================
# CLI Settings
# =============================================================================

AGENT_DRAFT_DIR = Path("Issues/Features/work/drafts")
"""Recommended directory for Agent draft files (relative to project root)."""

DRAFT_EXTENSIONS = [".md", ".txt"]
"""Allowed draft file extensions."""
