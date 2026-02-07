"""
Mailbox Protocol Constants - Directory structure and default values.
"""

from pathlib import Path

# Directory structure within .monoco/
MAILBOX_DIR = "mailbox"
INBOUND_DIR = "inbound"
OUTBOUND_DIR = "outbound"
ARCHIVE_DIR = "archive"
STATE_DIR = ".state"
DEADLETTER_DIR = ".deadletter"
TMP_DIR = ".tmp"

# Default mailbox root path (relative to project root)
DEFAULT_MAILBOX_ROOT = Path(".monoco") / MAILBOX_DIR

# File patterns
MESSAGE_FILE_PATTERN = "*.md"
INBOUND_FILE_PATTERN = "*_inbound_*.md"
OUTBOUND_FILE_PATTERN = "*_outbound_*.md"

# Lock/State files
LOCKS_FILE = "locks.json"
CLAIM_TIMEOUT_SECONDS = 300  # 5 minutes default claim timeout

# Retry configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_BASE_MS = 1000
RETRY_BACKOFF_MULTIPLIER = 2.0
RETRY_MAX_BACKOFF_MS = 30000

# Debounce configuration
DEFAULT_DEBOUNCE_WINDOW_MS = 5000
DEFAULT_DEBOUNCE_MAX_WAIT_MS = 30000

# Courier service defaults
COURIER_PID_FILE = ".monoco/run/courier.pid"
COURIER_LOG_FILE = ".monoco/log/courier.log"
COURIER_DEFAULT_PORT = 8080

# API endpoints
API_PREFIX = "/api/v1"
API_MESSAGE_CLAIM = "/messages/{id}/claim"
API_MESSAGE_COMPLETE = "/messages/{id}/complete"
API_MESSAGE_FAIL = "/messages/{id}/fail"
API_MESSAGE_GET = "/messages/{id}"
API_HEALTH = "/health"

# Content preview settings
DEFAULT_PREVIEW_LENGTH = 50
MAX_PREVIEW_LENGTH = 200
