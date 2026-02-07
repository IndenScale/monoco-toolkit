"""
Courier Constants - Service configuration and default values.
"""

from pathlib import Path

# Service paths
COURIER_PID_DIR = ".monoco/run"
COURIER_LOG_DIR = ".monoco/log"
COURIER_CONFIG_DIR = ".monoco/config"

# Service files
COURIER_PID_FILE = Path(COURIER_PID_DIR) / "courier.pid"
COURIER_STATE_FILE = Path(COURIER_PID_DIR) / "courier.json"
COURIER_LOG_FILE = Path(COURIER_LOG_DIR) / "courier.log"
COURIER_LOCK_FILE = Path(COURIER_PID_DIR) / "courier.lock"

# Service defaults
COURIER_DEFAULT_HOST = "localhost"
COURIER_DEFAULT_PORT = 8644  # Changed from 8080 to avoid common conflicts
COURIER_DEFAULT_LOG_LEVEL = "info"

# Service timeouts
SERVICE_START_TIMEOUT = 30  # seconds
SERVICE_STOP_TIMEOUT = 30  # seconds
SERVICE_HEALTH_CHECK_TIMEOUT = 5  # seconds

# Process management
SIGTERM_TIMEOUT = 10  # seconds before SIGKILL after SIGTERM

# Archive settings
ARCHIVE_RETENTION_DAYS = 30

# Service status enum values
class ServiceState:
    """Service state constants."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"