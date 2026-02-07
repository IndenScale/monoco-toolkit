"""
Courier Daemon - Background process for message handling.

The daemon runs continuously to:
- Process outbound message drafts
- Receive inbound messages via webhooks/adapters
- Maintain message state (locks, retries)
- Provide HTTP API for Mailbox CLI

This module is executed as a subprocess by the service manager.
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

# Setup logging before other imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("courier.daemon")

from monoco.features.connector.protocol.constants import (
    DEFAULT_MAILBOX_ROOT,
    COURIER_DEFAULT_PORT,
    COURIER_DEFAULT_HOST,
)

from .state import LockManager, MessageStateManager
from .api import CourierAPIServer
from .debounce import DebounceHandler, DebounceConfig


class CourierDaemon:
    """
    The Courier daemon process.

    Runs as a background process and manages:
    - HTTP API server
    - Message state
    - Outbound message processing
    - Inbound message ingestion
    """

    def __init__(
        self,
        project_root: Path,
        host: str = COURIER_DEFAULT_HOST,
        port: int = COURIER_DEFAULT_PORT,
        pid_file: Optional[Path] = None,
        debug: bool = False,
    ):
        self.project_root = Path(project_root)
        self.host = host
        self.port = port
        self.pid_file = pid_file
        self.debug = debug

        # Set up paths
        self.mailbox_root = self.project_root / DEFAULT_MAILBOX_ROOT
        self.state_dir = self.mailbox_root / ".state"

        # Components
        self.lock_manager: Optional[LockManager] = None
        self.state_manager: Optional[MessageStateManager] = None
        self.api_server: Optional[CourierAPIServer] = None
        self.debounce_handler: Optional[DebounceHandler] = None

        # Control
        self._shutdown = False
        self._shutdown_signal = False

    def initialize(self) -> bool:
        """Initialize all daemon components."""
        try:
            if self.debug:
                logging.getLogger().setLevel(logging.DEBUG)

            logger.info(f"Initializing Courier daemon in {self.project_root}")

            # Ensure mailbox directory structure exists
            self._ensure_directories()

            # Initialize state management
            self.lock_manager = LockManager(self.state_dir)
            self.state_manager = MessageStateManager(
                self.lock_manager,
                self.mailbox_root,
            )
            self.state_manager.initialize()

            # Initialize debounce handler
            debounce_config = DebounceConfig()
            self.debounce_handler = DebounceHandler(
                debounce_config,
                self._on_debounce_flush,
            )

            # Initialize API server
            self.api_server = CourierAPIServer(
                self.lock_manager,
                self.state_manager,
                host=self.host,
                port=self.port,
            )

            logger.info("Courier daemon initialized successfully")
            return True

        except Exception as e:
            logger.exception("Failed to initialize daemon")
            return False

    def _ensure_directories(self) -> None:
        """Create necessary directory structure."""
        dirs = [
            self.mailbox_root,
            self.mailbox_root / "inbound",
            self.mailbox_root / "outbound",
            self.mailbox_root / "archive",
            self.mailbox_root / ".state",
            self.mailbox_root / ".deadletter",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory: {d}")

    def _on_debounce_flush(self, messages: list) -> None:
        """Callback for debounce flush."""
        logger.info(f"Debounce flush with {len(messages)} messages")
        # Messages would be written to inbound directory here
        # This is handled by the adapters in a full implementation

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._shutdown_signal = True
        self._shutdown = True

    def run(self) -> int:
        """
        Run the daemon main loop.

        Returns:
            Exit code (0 for success, 1 for error)
        """
        if not self.initialize():
            return 1

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Write PID file if specified
        if self.pid_file:
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))

        try:
            # Start API server
            self.api_server.start()

            logger.info(f"Courier daemon running on {self.host}:{self.port}")

            # Main loop
            while not self._shutdown:
                # TODO: Process outbound queue
                # TODO: Poll adapters for inbound messages
                # TODO: Retry failed messages

                time.sleep(1)

                # Check for shutdown signal
                if self._shutdown_signal:
                    break

        except Exception as e:
            logger.exception("Error in main loop")
            return 1

        finally:
            self.shutdown()

        return 0

    def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down Courier daemon...")

        self._shutdown = True

        # Stop API server
        if self.api_server:
            try:
                self.api_server.stop()
            except Exception as e:
                logger.error(f"Error stopping API server: {e}")

        # Flush debounce buffers
        if self.debounce_handler:
            try:
                self.debounce_handler.shutdown()
                # Note: In async context we'd await flush_all()
            except Exception as e:
                logger.error(f"Error flushing debounce buffers: {e}")

        # Clean up PID file
        if self.pid_file and self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except IOError:
                pass

        logger.info("Courier daemon shutdown complete")


def main():
    """Main entry point for the daemon."""
    parser = argparse.ArgumentParser(description="Courier Daemon")
    parser.add_argument(
        "--host",
        default=COURIER_DEFAULT_HOST,
        help="Host to bind API server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=COURIER_DEFAULT_PORT,
        help="Port to bind API server",
    )
    parser.add_argument(
        "--pid-file",
        type=Path,
        help="Path to PID file",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Path to log file (deprecated, logs to stdout)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config file",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory",
    )

    args = parser.parse_args()

    daemon = CourierDaemon(
        project_root=args.project_root,
        host=args.host,
        port=args.port,
        pid_file=args.pid_file,
        debug=args.debug,
    )

    sys.exit(daemon.run())


if __name__ == "__main__":
    main()
