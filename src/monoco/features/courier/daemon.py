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
import asyncio
import json
import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Setup logging before other imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("courier.daemon")

from monoco.features.connector.protocol.constants import DEFAULT_MAILBOX_ROOT
from .constants import COURIER_DEFAULT_PORT, COURIER_DEFAULT_HOST

from .state import LockManager, MessageStateManager
from .api import CourierAPIServer
from .debounce import DebounceHandler, DebounceConfig
from monoco.core.registry import get_inventory


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
        self.stream_adapter: Optional[Any] = None
        self._stream_thread: Optional[threading.Thread] = None
        
        # IM Agent integration (FEAT-0170)
        self.im_adapter: Optional[Any] = None
        self._im_task: Optional[asyncio.Task] = None

        # Control
        self._shutdown = False
        self._shutdown_signal = False
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    def initialize(self) -> bool:
        """Initialize all daemon components."""
        try:
            if self.debug:
                logging.getLogger().setLevel(logging.DEBUG)

            logger.info(f"Initializing Courier daemon in {self.project_root}")

            # Ensure mailbox directory structure exists
            self._ensure_directories()

            # Initialize global project inventory
            inventory = get_inventory()
            
            # Auto-register the current project as 'default' if not already present
            if not inventory.get("default"):
                inventory.register("default", self.project_root)

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
            
            # Initialize DingTalk Stream adapter if configured
            self._init_stream_adapter()
            
            # Initialize IM Agent adapter (FEAT-0170)
            self._init_im_adapter()

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

    def _init_stream_adapter(self) -> None:
        """Initialize DingTalk Stream adapter if credentials are configured."""
        # Read credentials from environment
        client_id = os.environ.get("DINGTALK_CLIENT_ID") or os.environ.get("DINGTALK_APP_KEY")
        client_secret = os.environ.get("DINGTALK_CLIENT_SECRET") or os.environ.get("DINGTALK_APP_SECRET")
        
        if not client_id or not client_secret:
            logger.info("DingTalk Stream adapter not configured (set DINGTALK_CLIENT_ID and DINGTALK_CLIENT_SECRET)")
            return
        
        try:
            from .adapters.dingtalk_stream import create_dingtalk_stream_adapter
            from monoco.features.mailbox.store import MailboxStore, MailboxConfig
            
            default_project = os.environ.get("DINGTALK_STREAM_DEFAULT_PROJECT", "default")
            
            self.stream_adapter = create_dingtalk_stream_adapter(
                client_id=client_id,
                client_secret=client_secret,
                default_project=default_project,
            )
            
            # Set up message handler to write to mailbox
            self.stream_adapter.set_message_handler(self._handle_stream_message)
            
            logger.info(f"DingTalk Stream adapter initialized for project: {default_project}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize DingTalk Stream adapter: {e}")
    
    def _init_im_adapter(self) -> None:
        """Initialize IM Agent adapter if enabled (FEAT-0170)."""
        try:
            from .im_integration import create_im_adapter
            
            self.im_adapter = create_im_adapter(
                project_root=self.project_root,
                max_concurrent_sessions=5,
                session_timeout_minutes=30,
            )
            
            logger.info("IM Agent adapter initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize IM Agent adapter: {e}")
    
    async def _start_im_adapter(self) -> None:
        """Start IM Agent adapter asynchronously."""
        if self.im_adapter:
            try:
                await self.im_adapter.start()
                logger.info("IM Agent adapter started")
            except Exception as e:
                logger.error(f"Failed to start IM Agent adapter: {e}")
    
    async def _stop_im_adapter(self) -> None:
        """Stop IM Agent adapter asynchronously."""
        if self.im_adapter:
            try:
                await self.im_adapter.stop()
                logger.info("IM Agent adapter stopped")
            except Exception as e:
                logger.error(f"Error stopping IM Agent adapter: {e}")
    
    def _handle_stream_message(self, message, project_slug: str) -> None:
        """Handle incoming Stream message and write to mailbox."""
        try:
            from monoco.features.mailbox.store import MailboxStore, MailboxConfig
            from monoco.core.registry import get_inventory
            
            # Get project path from registry
            inventory = get_inventory()
            project = inventory.get(project_slug)
            
            if not project:
                logger.warning(f"Project '{project_slug}' not found, using default path")
                project_path = self.project_root
            else:
                project_path = project.path
            
            # Create mailbox store for this project
            mailbox_path = project_path / ".monoco" / "mailbox"
            config = MailboxConfig(
                project_path=project_path,
                inbound_path=mailbox_path / "inbound",
                outbound_path=mailbox_path / "outbound",
                archive_path=mailbox_path / "archive",
                state_path=mailbox_path / ".state",
            )
            store = MailboxStore(config)
            
            # Write message to inbound
            path = store.create_inbound_message(message)
            logger.info(f"Stream message written to {path}")
            
        except Exception as e:
            logger.exception(f"Failed to handle Stream message: {e}")
    
    def _start_stream_adapter(self) -> None:
        """Start Stream adapter in background thread."""
        if not self.stream_adapter:
            return
        
        def run_stream():
            """Run stream adapter synchronously."""
            try:
                self.stream_adapter.run_sync()
            except Exception as e:
                logger.exception(f"Stream adapter error: {e}")
        
        self._stream_thread = threading.Thread(target=run_stream, daemon=True, name="DingTalkStream")
        self._stream_thread.start()
        logger.info("DingTalk Stream adapter started in background thread")

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
            
            # Start Stream adapter if configured
            self._start_stream_adapter()
            
            # Start IM adapter (async)
            if self.im_adapter:
                try:
                    # Create event loop for async operations
                    self._event_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._event_loop)
                    self._event_loop.run_until_complete(self._start_im_adapter())
                except Exception as e:
                    logger.error(f"Failed to start IM adapter: {e}")

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
            # Stop IM adapter
            if self.im_adapter and self._event_loop:
                try:
                    self._event_loop.run_until_complete(self._stop_im_adapter())
                except Exception as e:
                    logger.error(f"Error stopping IM adapter: {e}")
            
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
        
        # Stop Stream adapter
        if self.stream_adapter:
            try:
                import asyncio
                asyncio.run(self.stream_adapter.disconnect())
                logger.info("DingTalk Stream adapter stopped")
            except Exception as e:
                logger.error(f"Error stopping Stream adapter: {e}")

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
