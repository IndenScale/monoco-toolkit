"""
Courier Service - Process lifecycle management.

Manages the Courier daemon process:
- PID file management
- Process start/stop/kill
- Health checking
- Status reporting
"""

import fcntl
import os
import signal
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

from .constants import (
    COURIER_PID_FILE,
    COURIER_STATE_FILE,
    COURIER_LOG_FILE,
    COURIER_LOCK_FILE,
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
        lock_file: Optional[Path] = None,
        host: str = COURIER_DEFAULT_HOST,
        port: int = COURIER_DEFAULT_PORT,
        project_root: Optional[Path] = None,
    ):
        self.pid_file = Path(pid_file) if pid_file else COURIER_PID_FILE
        self.state_file = COURIER_STATE_FILE
        self.log_file = Path(log_file) if log_file else COURIER_LOG_FILE
        self.lock_file = Path(lock_file) if lock_file else COURIER_LOCK_FILE
        self.host = host
        self.port = port
        self.project_root = project_root or Path.cwd()
        self.api_url = f"http://{host}:{port}"
        self._lock_fd: Optional[int] = None

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
        """Write PID to pid file atomically using O_EXCL flag.

        Raises:
            ServiceAlreadyRunningError: If PID file already exists (another instance starting)
        """
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Use O_EXCL to ensure atomic creation - fails if file exists
            fd = os.open(self.pid_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            try:
                os.write(fd, str(pid).encode())
            finally:
                os.close(fd)
        except FileExistsError:
            raise ServiceAlreadyRunningError(
                "Courier PID file already exists - another instance may be starting"
            )

    def _remove_pid(self) -> None:
        """Remove PID file."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except IOError:
            pass

    def _acquire_lock(self) -> None:
        """Acquire exclusive file lock to prevent multiple instances.

        Raises:
            ServiceAlreadyRunningError: If another instance holds the lock
        """
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_RDWR)
            # Try to acquire exclusive lock without blocking
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError) as e:
            if self._lock_fd is not None:
                try:
                    os.close(self._lock_fd)
                except OSError:
                    pass
                self._lock_fd = None
            raise ServiceAlreadyRunningError(
                "Another Courier instance is already running or starting"
            ) from e

    def _release_lock(self) -> None:
        """Release file lock."""
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
            except OSError:
                pass
            finally:
                self._lock_fd = None
        # Clean up lock file if it exists
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
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

    def _check_port_available(self, port: int) -> tuple[bool, Optional[str]]:
        """Check if a port is available for binding.

        Args:
            port: Port number to check

        Returns:
            Tuple of (is_available, error_message)
        """
        try:
            # Try to bind to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, port))
            sock.close()
            return True, None
        except socket.error as e:
            # Port is in use, try to get process info
            error_msg = f"Port {port} is already in use"
            try:
                # Try to find which process is using the port
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split("\n")
                    error_msg += f" (PID: {', '.join(pids)})"
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
            return False, error_msg

    def _find_courier_processes(self) -> List[int]:
        """Find all Courier-related processes by name.

        Returns:
            List of PIDs for Courier daemon processes
        """
        pids = []
        try:
            # Use pgrep to find processes matching the daemon module
            result = subprocess.run(
                ["pgrep", "-f", "monoco.features.courier.daemon"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    try:
                        pids.append(int(line.strip()))
                    except ValueError:
                        continue
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return pids

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
        # Acquire file lock to prevent multiple instances
        self._acquire_lock()

        try:
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

            # Check port availability before starting
            port_available, port_error = self._check_port_available(self.port)
            if not port_available:
                raise ServiceStartError(port_error)

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

        finally:
            # Release lock if start failed, keep it if successful
            status = self.get_status()
            if not status.is_running():
                self._release_lock()

        return self.get_status()

    def stop(
        self,
        timeout: int = SERVICE_STOP_TIMEOUT,
        wait: bool = False,
        all_processes: bool = False,
    ) -> ServiceStatus:
        """
        Stop the Courier service gracefully.

        Args:
            timeout: Seconds to wait before force kill
            wait: Block until service stops
            all_processes: If True, stop all Courier-related processes (orphan cleanup)

        Returns:
            ServiceStatus after stopping

        Raises:
            ServiceNotRunningError: If service is not running
        """
        if all_processes:
            # Find and stop all Courier processes
            pids = self._find_courier_processes()
            if not pids:
                # Also check PID file
                pid = self._read_pid()
                if pid:
                    pids = [pid]
                else:
                    raise ServiceNotRunningError("No Courier processes found")

            stopped_count = 0
            for pid in pids:
                if self._is_process_running(pid):
                    try:
                        os.kill(pid, signal.SIGTERM)
                        stopped_count += 1
                    except OSError:
                        pass

            if wait and stopped_count > 0:
                # Wait for all processes to exit
                start_time = time.time()
                while time.time() - start_time < timeout:
                    all_stopped = all(
                        not self._is_process_running(pid) for pid in pids
                    )
                    if all_stopped:
                        break
                    time.sleep(0.5)
                else:
                    # Timeout - force kill remaining
                    for pid in pids:
                        if self._is_process_running(pid):
                            try:
                                os.kill(pid, signal.SIGKILL)
                            except OSError:
                                pass

            # Clean up PID/state files
            self._remove_pid()
            self._remove_state()
            self._release_lock()

            return ServiceStatus(state=ServiceState.STOPPED)

        # Normal single-process stop
        pid = self._read_pid()
        if not pid:
            raise ServiceNotRunningError("Courier is not running")

        if not self._is_process_running(pid):
            self._remove_pid()
            self._remove_state()
            self._release_lock()
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
                    self._release_lock()
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
        if pid:
            try:
                os.kill(pid, signal_type)
            except (OSError, ProcessLookupError):
                pass  # Process already gone

        # Always clean up files and lock, even if no PID was found
        self._remove_pid()
        self._remove_state()
        self._release_lock()
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
            self.stop(wait=True)
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
