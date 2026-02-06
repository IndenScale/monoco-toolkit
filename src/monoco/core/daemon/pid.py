"""PID file management and port utilities for Monoco Daemon."""

import json
import os
import signal
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional


class PIDFileError(Exception):
    """Exception raised for PID file related errors."""

    pass


class PIDManager:
    """Manages PID file for workspace-scoped daemon process.

    PID file format (JSON):
    {
        "pid": 12345,
        "host": "127.0.0.1",
        "port": 8642,
        "started_at": "2026-02-03T12:00:00",
        "version": "0.3.12"
    }
    """

    PID_FILENAME = "monoco.pid"
    PID_DIR = "run"

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root)
        self.pid_file = self._get_pid_file_path()

    def _get_pid_file_path(self) -> Path:
        """Get the PID file path for the workspace."""
        pid_dir = self.workspace_root / ".monoco" / self.PID_DIR
        pid_dir.mkdir(parents=True, exist_ok=True)
        return pid_dir / self.PID_FILENAME

    def create_pid_file(
        self, host: str, port: int, version: str = "0.3.12"
    ) -> Path:
        """Create a PID file with process metadata.

        Args:
            host: The host address the daemon is listening on
            port: The port the daemon is listening on
            version: Monoco version

        Returns:
            Path to the created PID file

        Raises:
            PIDFileError: If PID file already exists and process is still alive
        """
        # Check for existing PID file
        existing = self.read_pid_file()
        if existing and self.is_process_alive(existing["pid"]):
            raise PIDFileError(
                f"Daemon already running (PID: {existing['pid']}, "
                f"port: {existing['port']})"
            )

        # Clean up stale PID file if exists
        if self.pid_file.exists():
            self.remove_pid_file()

        pid_data = {
            "pid": os.getpid(),
            "host": host,
            "port": port,
            "started_at": datetime.now().isoformat(),
            "version": version,
        }

        # Write atomically using temp file
        temp_file = self.pid_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(pid_data, f, indent=2)
            temp_file.rename(self.pid_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise PIDFileError(f"Failed to create PID file: {e}") from e

        return self.pid_file

    def read_pid_file(self) -> Optional[dict]:
        """Read and parse the PID file.

        Returns:
            Dict with pid, host, port, started_at, version or None if not exists
        """
        if not self.pid_file.exists():
            return None

        try:
            with open(self.pid_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def remove_pid_file(self) -> bool:
        """Remove the PID file.

        Returns:
            True if file was removed, False if it didn't exist
        """
        try:
            self.pid_file.unlink()
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def is_process_alive(pid: int) -> bool:
        """Check if a process with given PID is still running.

        Args:
            pid: Process ID to check

        Returns:
            True if process exists and is running
        """
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def get_daemon_info(self) -> Optional[dict]:
        """Get daemon info if it's running.

        Returns:
            Daemon info dict if running, None otherwise
        """
        pid_data = self.read_pid_file()
        if not pid_data:
            return None

        if not self.is_process_alive(pid_data["pid"]):
            # Stale PID file, clean it up
            self.remove_pid_file()
            return None

        return pid_data

    def send_signal(self, sig: int) -> bool:
        """Send a signal to the daemon process.

        Args:
            sig: Signal to send (e.g., signal.SIGTERM)

        Returns:
            True if signal was sent successfully
        """
        pid_data = self.read_pid_file()
        if not pid_data:
            return False

        pid = pid_data["pid"]
        try:
            os.kill(pid, sig)
            return True
        except (OSError, ProcessLookupError):
            return False

    def terminate(self, timeout: int = 5) -> bool:
        """Gracefully terminate the daemon process.

        Args:
            timeout: Seconds to wait for graceful shutdown

        Returns:
            True if process was terminated
        """
        pid_data = self.read_pid_file()
        if not pid_data:
            return False

        pid = pid_data["pid"]

        # Try graceful shutdown first
        try:
            os.kill(pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            # Process already gone
            self.remove_pid_file()
            return True

        # Wait for process to terminate
        import time

        for _ in range(timeout * 10):
            if not self.is_process_alive(pid):
                self.remove_pid_file()
                return True
            time.sleep(0.1)

        # Force kill if still running
        try:
            os.kill(pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass

        self.remove_pid_file()
        return True


class PortManager:
    """Port management utilities for daemon."""

    DEFAULT_PORT = 8642
    MAX_PORT_RETRY = 100

    @staticmethod
    def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
        """Check if a port is already in use.

        Args:
            port: Port number to check
            host: Host address to check

        Returns:
            True if port is in use
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return False
            except OSError:
                return True

    @classmethod
    def find_available_port(
        cls, start_port: int = DEFAULT_PORT, host: str = "127.0.0.1", max_retry: int = MAX_PORT_RETRY
    ) -> int:
        """Find an available port starting from start_port.

        Args:
            start_port: Starting port number
            host: Host address to bind
            max_retry: Maximum number of ports to try

        Returns:
            Available port number

        Raises:
            PIDFileError: If no available port found within range
        """
        for port in range(start_port, start_port + max_retry):
            if not cls.is_port_in_use(port, host):
                return port

        raise PIDFileError(
            f"No available port found in range {start_port}-{start_port + max_retry - 1}"
        )

    @classmethod
    def get_port_with_fallback(
        cls, preferred_port: int = DEFAULT_PORT, host: str = "127.0.0.1", auto_increment: bool = True
    ) -> int:
        """Get a port, either the preferred one or an available fallback.

        Args:
            preferred_port: Preferred port to use
            host: Host address
            auto_increment: If True, find next available port; if False, raise error

        Returns:
            Port number to use

        Raises:
            PIDFileError: If preferred port is in use and auto_increment is False
        """
        if not cls.is_port_in_use(preferred_port, host):
            return preferred_port

        if not auto_increment:
            raise PIDFileError(
                f"Port {preferred_port} is already in use. "
                f"Use --port to specify a different port."
            )

        return cls.find_available_port(preferred_port + 1, host)
