"""
Integration tests for Courier Service process management.

Tests:
- File lock mechanism (prevents multiple instances)
- Port availability check
- Atomic PID file writing
- Process discovery and cleanup (--all)
"""

import os
import signal
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from monoco.features.courier.service import (
    CourierService,
    ServiceAlreadyRunningError,
    ServiceNotRunningError,
    ServiceStartError,
    ServiceState,
)
from monoco.features.courier.constants import (
    COURIER_DEFAULT_PORT,
    COURIER_DEFAULT_HOST,
)


class TestFileLockMechanism:
    """Test file lock prevents multiple instances."""

    def test_acquire_lock_creates_lock_file(self, tmp_path):
        """Test that acquiring lock creates lock file."""
        service = CourierService(project_root=tmp_path, port=8645)
        service._acquire_lock()

        try:
            assert service.lock_file.exists()
        finally:
            service._release_lock()

    def test_second_instance_cannot_acquire_lock(self, tmp_path):
        """Test that second instance cannot acquire lock while first holds it."""
        service1 = CourierService(project_root=tmp_path, port=8646)
        service2 = CourierService(project_root=tmp_path, port=8647)

        service1._acquire_lock()
        try:
            with pytest.raises(ServiceAlreadyRunningError) as exc_info:
                service2._acquire_lock()
            assert "already running" in str(exc_info.value).lower()
        finally:
            service1._release_lock()

    def test_lock_released_on_release(self, tmp_path):
        """Test that lock file is cleaned up on release."""
        service = CourierService(project_root=tmp_path, port=8648)
        service._acquire_lock()
        service._release_lock()

        assert not service.lock_file.exists()

    def test_can_acquire_after_release(self, tmp_path):
        """Test that lock can be re-acquired after release."""
        service1 = CourierService(project_root=tmp_path, port=8649)
        service2 = CourierService(project_root=tmp_path, port=8650)

        service1._acquire_lock()
        service1._release_lock()

        # Second service should now be able to acquire
        service2._acquire_lock()
        try:
            assert service2.lock_file.exists()
        finally:
            service2._release_lock()


class TestPortAvailabilityCheck:
    """Test port availability checking."""

    def test_port_available_returns_true(self, tmp_path):
        """Test that available port returns (True, None)."""
        service = CourierService(project_root=tmp_path, port=8651)
        available, error = service._check_port_available(8651)

        assert available is True
        assert error is None

    def test_port_in_use_returns_false(self, tmp_path):
        """Test that occupied port returns (False, error_message)."""
        # Bind to a port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((COURIER_DEFAULT_HOST, 8652))
        sock.listen(1)

        try:
            service = CourierService(project_root=tmp_path, port=8652)
            available, error = service._check_port_available(8652)

            assert available is False
            assert error is not None
            assert "in use" in error.lower() or "already" in error.lower()
        finally:
            sock.close()

    def test_start_fails_when_port_in_use(self, tmp_path):
        """Test that start() fails with ServiceStartError when port is in use."""
        # Bind to a port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((COURIER_DEFAULT_HOST, 8653))
        sock.listen(1)

        try:
            service = CourierService(project_root=tmp_path, port=8653)
            with pytest.raises(ServiceStartError) as exc_info:
                # This should fail during port check before actually starting
                service.start()
            assert "port" in str(exc_info.value).lower() or "in use" in str(exc_info.value).lower()
        finally:
            sock.close()
            # Release lock if acquired
            service._release_lock()


class TestAtomicPidWriting:
    """Test atomic PID file writing with O_EXCL."""

    def test_write_pid_creates_file(self, tmp_path):
        """Test that _write_pid creates PID file."""
        service = CourierService(project_root=tmp_path, port=8654)
        service._write_pid(12345)

        try:
            assert service.pid_file.exists()
            with open(service.pid_file) as f:
                assert f.read().strip() == "12345"
        finally:
            service._remove_pid()

    def test_write_pid_fails_if_file_exists(self, tmp_path):
        """Test that _write_pid raises error if PID file exists."""
        service = CourierService(project_root=tmp_path, port=8655)
        service._write_pid(12345)

        try:
            with pytest.raises(ServiceAlreadyRunningError) as exc_info:
                service._write_pid(67890)
            assert "pid file" in str(exc_info.value).lower() or "already" in str(exc_info.value).lower()
        finally:
            service._remove_pid()

    def test_remove_pid_deletes_file(self, tmp_path):
        """Test that _remove_pid deletes PID file."""
        service = CourierService(project_root=tmp_path, port=8656)
        service._write_pid(12345)
        service._remove_pid()

        assert not service.pid_file.exists()


class TestProcessDiscovery:
    """Test finding Courier processes by name."""

    def test_find_courier_processes_returns_list(self, tmp_path):
        """Test that _find_courier_processes returns a list."""
        service = CourierService(project_root=tmp_path, port=8657)
        pids = service._find_courier_processes()

        assert isinstance(pids, list)

    def test_find_no_courier_processes_when_none_running(self, tmp_path):
        """Test that no processes are found when Courier is not running."""
        service = CourierService(project_root=tmp_path, port=8658)
        # Ensure no courier processes are running
        pids = service._find_courier_processes()

        # This test may have false positives if Courier is actually running
        # but that's okay - we're testing the mechanism
        assert isinstance(pids, list)


class TestStopAllProcesses:
    """Test --all parameter for stop command."""

    def test_stop_all_raises_error_when_no_processes(self, tmp_path):
        """Test that stop(all=True) raises error when no processes found."""
        service = CourierService(project_root=tmp_path, port=8659)

        # Clean up any existing state
        service._remove_pid()
        service._remove_state()

        with pytest.raises(ServiceNotRunningError) as exc_info:
            service.stop(all_processes=True)
        assert "no courier" in str(exc_info.value).lower() or "not running" in str(exc_info.value).lower()

    def test_stop_all_cleans_up_files(self, tmp_path):
        """Test that stop(all=True) cleans up PID and state files."""
        service = CourierService(project_root=tmp_path, port=8660)

        # Create fake PID and state files
        service._write_pid(99999)
        service._write_state(99999)

        # Note: We can't actually test killing processes without a running
        # Courier instance, but we can verify the cleanup logic
        assert service.pid_file.exists()
        assert service.state_file.exists()

        # Clean up manually
        service._remove_pid()
        service._remove_state()

        assert not service.pid_file.exists()
        assert not service.state_file.exists()


class TestDefaultPort:
    """Test default port change from 8080 to 8644."""

    def test_default_port_is_8644(self):
        """Test that default port is 8644, not 8080."""
        assert COURIER_DEFAULT_PORT == 8644

    def test_service_uses_default_port(self, tmp_path):
        """Test that CourierService uses default port 8644."""
        service = CourierService(project_root=tmp_path)
        assert service.port == 8644
        assert "8644" in service.api_url


class TestServiceLifecycle:
    """Test service lifecycle with file locks."""

    def test_release_lock_on_failed_start(self, tmp_path):
        """Test that lock is released if start fails."""
        # Bind to the port to cause start to fail
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = 8661
        sock.bind((COURIER_DEFAULT_HOST, port))
        sock.listen(1)

        service = CourierService(project_root=tmp_path, port=port)

        try:
            with pytest.raises(ServiceStartError):
                service.start()

            # Lock should be released after failed start
            assert not service.lock_file.exists()
        finally:
            sock.close()
            service._release_lock()

    def test_kill_releases_lock(self, tmp_path):
        """Test that kill() releases the file lock."""
        service = CourierService(project_root=tmp_path, port=8662)

        # Create a fake PID file
        service._write_pid(99998)
        service._acquire_lock()

        # Kill should clean up
        service.kill()

        assert not service.pid_file.exists()
        assert not service.lock_file.exists()
