"""
Courier Service - Process lifecycle management.

Manages the Courier daemon process:
- PID file management
- Process start/stop/kill
- Health checking
- Status reporting
"""

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
import json

from .constants import (
    COURIER_PID_FILE,
    COURIER_STATE_FILE,
    COURIER_LOG_FILE,
    COURIER_DEFAULT_HOST,
    COURIER_DEFAULT_PORT,
    SERVICE_START_TIMEOUT,
    SERVICE_STOP_TIMEOUT,
    SIGTERM_TIMEOUT,
    ServiceState,
)


class ServiceError(Exception):
    """Base exception for service errors."""
    pass


class ServiceAlreadyRunningError(ServiceError):
    """Raised when trying to start an already running service."""
    pass


class ServiceNotRunningError(ServiceError):
    """Raised when trying to stop a service that isn't running."""
    pass


class ServiceStartError(ServiceError):
    """Raised when service fails to start."""
    pass


@dataclass
class ServiceStatus:
    """Status information for the Courier service."""
    state: str
    pid: Optional[int] = None
    uptime_seconds: Optional[int] = None
    version: str = "1.0.0"
    api_url: str = ""
    error_message: Optional[str] = None
    adapters: Dict[str, Any] = None
    metrics: Dict[str, int] = None

    def __post_init__(self):
        if self.adapters is None:
            self.adapters = {}
        if self.metrics is None:
            self.metrics = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state": self.state,
            "pid": self.pid,
            "uptime_seconds": self.uptime_seconds,
            "version": self.version,
            "api_url": self.api_url,
            "error_message": self.error_message,
            "adapters": self.adapters,
            "metrics": self.metrics,
        }

    def is_running(self) -> bool:
        """Check if service is running."""
        return self.state == ServiceState.RUNNING


class CourierService:
    """
    Manages the Courier daemon process lifecycle.

    Handles:
    - Starting the daemon process
    - Stopping gracefully (SIGTERM)
    - Killing forcefully (SIGKILL)
    - Checking health/status
    - PID file management
    """

    def __init__(
        self,
        pid_file: Optional[Path] = None,
        log_file: Optional[Path] = None,
        host: str = COURIER_DEFAULT_HOST,
        port: int = COURIER_DEFAULT_PORT,
        project_root: Optional[Path] = None,
    ):
        self.pid_file = Path(pid_file) if pid_file else COURIER_PID_FILE
        self.state_file = COURIER_STATE_FILE
        self.log_file = Path(log_file) if log_file else COURIER_LOG_FILE
        self.host = host
        self.port = port
        self.project_root = project_root or Path.cwd()
        self.api_url = f"http://{host}:{port}"

        # Make paths relative to project root if not absolute
        if not self.pid_file.is_absolute():
            self.pid_file = self.project_root / self.pid_file
        if not self.state_file.is_absolute():
            self.state_file = self.project_root / self.state_file
        if not self.log_file.is_absolute():
            self.log_file = self.project_root / self.log_file

    def _read_pid(self) -> Optional[int]:
        """Read PID from pid file."""
        if not self.pid_file.exists() or not self.state_file.exists():
            return None
        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            # Verify against state file just in case, or read port/host from it
            # For strict consistency, we could return the int from state file too
            return pid
        except (ValueError, IOError):
            return None

    def _write_pid(self, pid: int) -> None:
        """Write PID to pid file."""
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.pid_file, "w") as f:
            f.write(str(pid))

    def _remove_pid(self) -> None:
        """Remove PID file."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except IOError:
            pass

    def _write_state(self, pid: int) -> None:
        """Write state file with process metadata."""
        state = {
            "pid": pid,
            "host": self.host,
            "port": self.port,
            "started_at": datetime.now().isoformat(),
        }
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def _remove_state(self) -> None:
        """Remove state file."""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
        except IOError:
            pass

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with the given PID is running."""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def get_status(self) -> ServiceStatus:
        """Get current service status."""
        pid = self._read_pid()

        if not pid:
            return ServiceStatus(state=ServiceState.STOPPED)

        if not self._is_process_running(pid):
            # Stale PID file
            self._remove_pid()
            self._remove_state()
            return ServiceStatus(
                state=ServiceState.ERROR,
                error_message="Stale PID file found - process not running",
            )

        # Read state for runtime configuration
        api_url = self.api_url # Fallback
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    host = state.get("host", self.host)
                    port = state.get("port", self.port)
                    api_url = f"http://{host}:{port}"
            except (json.JSONDecodeError, IOError):
                pass

        # Process is running, try to get more info from health endpoint
        try:
            import urllib.request
            health_url = f"{api_url}/health"
            req = urllib.request.Request(health_url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return ServiceStatus(
                        state=ServiceState.RUNNING,
                        pid=pid,
                        api_url=api_url,
                        version=data.get("version", "1.0.0"),
                        adapters=data.get("adapters", {}),
                        metrics=data.get("metrics", {}),
                    )
        except Exception:
            pass

        # Process running but health check failed (starting or error)
        return ServiceStatus(
            state=ServiceState.STARTING,
            pid=pid,
            api_url=api_url,
        )

    def start(
        self,
        foreground: bool = False,
        debug: bool = False,
        config_path: Optional[Path] = None,
    ) -> ServiceStatus:
        """
        Start the Courier service.

        Args:
            foreground: Run in foreground (don't daemonize)
            debug: Enable debug logging
            config_path: Optional config file path

        Returns:
            ServiceStatus after starting

        Raises:
            ServiceAlreadyRunningError: If service is already running
            ServiceStartError: If service fails to start
        """
        # Check if already running
        current_status = self.get_status()
        if current_status.is_running():
            raise ServiceAlreadyRunningError(
                f"Courier is already running (PID: {current_status.pid})"
            )

        if current_status.state == ServiceState.STARTING:
            raise ServiceAlreadyRunningError(
                f"Courier is starting (PID: {current_status.pid})"
            )

        # Clean up stale PID file if exists
        if self.pid_file.exists():
            self._remove_pid()
        if self.state_file.exists():
            self._remove_state()

        # Prepare log directory
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = [
            sys.executable,
            "-m",
            "monoco.features.courier.daemon",
            "--host", self.host,
            "--port", str(self.port),
            "--pid-file", str(self.pid_file),
            "--log-file", str(self.log_file),
        ]

        if debug:
            cmd.append("--debug")

        if config_path:
            cmd.extend(["--config", str(config_path)])

        if foreground:
            # Run in foreground (for debugging)
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                raise ServiceStartError(f"Failed to start courier: {e}")
        else:
            # Daemonize - run in background
            log_fd = open(self.log_file, "a")
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_fd,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,  # Detach from terminal
                )
                # Write PID and State file
                self._write_pid(process.pid)
                self._write_state(process.pid)
            finally:
                log_fd.close()

            # Wait for service to be ready
            start_time = time.time()
            while time.time() - start_time < SERVICE_START_TIMEOUT:
                status = self.get_status()
                if status.is_running():
                    return status
                if status.state == ServiceState.ERROR:
                    raise ServiceStartError(
                        f"Service failed to start: {status.error_message}"
                    )
                time.sleep(0.5)

            raise ServiceStartError("Service did not start within timeout")

        return self.get_status()

    def stop(self, timeout: int = SERVICE_STOP_TIMEOUT, wait: bool = False) -> ServiceStatus:
        """
        Stop the Courier service gracefully.

        Args:
            timeout: Seconds to wait before force kill
            wait: Block until service stops

        Returns:
            ServiceStatus after stopping

        Raises:
            ServiceNotRunningError: If service is not running
        """
        pid = self._read_pid()
        if not pid:
            raise ServiceNotRunningError("Courier is not running")

        if not self._is_process_running(pid):
            self._remove_pid()
            self._remove_state()
            raise ServiceNotRunningError("Courier process not found (stale PID file)")

        # Send SIGTERM for graceful shutdown
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as e:
            raise ServiceNotRunningError(f"Failed to stop courier: {e}")

        if wait:
            # Wait for process to exit
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self._is_process_running(pid):
                    self._remove_pid()
                    self._remove_state()
                    return ServiceStatus(state=ServiceState.STOPPED)
                time.sleep(0.5)

            # Timeout reached, force kill
            self.kill()

        return self.get_status()

    def kill(self, signal_type: int = signal.SIGKILL) -> ServiceStatus:
        """
        Force stop the Courier service.

        Warning: This is not graceful and may result in:
        - Lost lock state
        - Incomplete message processing
        - Resource leaks

        Args:
            signal_type: Signal to send (default: SIGKILL)

        Returns:
            ServiceStatus after kill
        """
        pid = self._read_pid()
        if not pid:
            return ServiceStatus(state=ServiceState.STOPPED)

        try:
            os.kill(pid, signal_type)
        except (OSError, ProcessLookupError):
            pass  # Process already gone

        self._remove_pid()
        self._remove_state()
        return ServiceStatus(state=ServiceState.STOPPED)

    def restart(
        self,
        force: bool = False,
        debug: bool = False,
    ) -> ServiceStatus:
        """
        Restart the Courier service.

        Args:
            force: Force restart if stop fails
            debug: Enable debug logging

        Returns:
            ServiceStatus after restart
        """
        try:
            self.stop()
        except ServiceNotRunningError:
            pass  # Already stopped
        except ServiceError:
            if not force:
                raise
            # Force kill if stop failed
            self.kill()

        return self.start(debug=debug)

    def get_logs(self, lines: int = 100) -> str:
        """
        Get recent log output.

        Args:
            lines: Number of lines to return

        Returns:
            Log content
        """
        if not self.log_file.exists():
            return ""

        try:
            with open(self.log_file, "r") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except IOError:
            return ""
