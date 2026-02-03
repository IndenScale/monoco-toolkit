"""Tests for PIDManager and PortManager."""

import json
import os
import signal
import socket
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from monoco.core.daemon.pid import PIDFileError, PIDManager, PortManager


class TestPIDManager:
    """Test cases for PIDManager."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace with .monoco directory."""
        monoco_dir = tmp_path / ".monoco"
        monoco_dir.mkdir()
        return tmp_path

    @pytest.fixture
    def pid_manager(self, temp_workspace):
        """Create a PIDManager instance for testing."""
        return PIDManager(temp_workspace)

    def test_init_creates_pid_dir(self, temp_workspace):
        """Test that initialization creates the PID directory."""
        pid_dir = temp_workspace / ".monoco" / "run"
        assert not pid_dir.exists()

        PIDManager(temp_workspace)

        assert pid_dir.exists()
        assert pid_dir.is_dir()

    def test_get_pid_file_path(self, pid_manager, temp_workspace):
        """Test PID file path generation."""
        expected_path = temp_workspace / ".monoco" / "run" / "monoco.pid"
        assert pid_manager.pid_file == expected_path

    def test_create_pid_file_success(self, pid_manager):
        """Test successful PID file creation."""
        host = "127.0.0.1"
        port = 8642

        pid_file = pid_manager.create_pid_file(host, port, version="0.1.0")

        assert pid_file.exists()
        with open(pid_file, "r") as f:
            data = json.load(f)
            assert data["pid"] == os.getpid()
            assert data["host"] == host
            assert data["port"] == port
            assert data["version"] == "0.1.0"
            assert "started_at" in data

    def test_create_pid_file_already_running(self, pid_manager, temp_workspace):
        """Test that creating PID file fails when daemon already running."""
        # Create a PID file with current process
        pid_manager.create_pid_file("127.0.0.1", 8642)

        # Try to create again - should fail
        with pytest.raises(PIDFileError) as exc_info:
            pid_manager.create_pid_file("127.0.0.1", 8642)

        assert "already running" in str(exc_info.value)

    def test_create_pid_file_stale_cleanup(self, pid_manager, temp_workspace):
        """Test that stale PID files are cleaned up."""
        # Create a PID file with a non-existent PID
        stale_pid = 999999
        pid_data = {
            "pid": stale_pid,
            "host": "127.0.0.1",
            "port": 8642,
            "started_at": "2026-01-01T00:00:00",
            "version": "0.1.0",
        }

        pid_manager.pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pid_manager.pid_file, "w") as f:
            json.dump(pid_data, f)

        # Should succeed because stale PID is not alive
        pid_file = pid_manager.create_pid_file("127.0.0.1", 8643)
        assert pid_file.exists()

        with open(pid_file, "r") as f:
            data = json.load(f)
            assert data["pid"] == os.getpid()

    def test_read_pid_file_success(self, pid_manager):
        """Test reading valid PID file."""
        pid_manager.create_pid_file("127.0.0.1", 8642)

        data = pid_manager.read_pid_file()

        assert data is not None
        assert data["pid"] == os.getpid()
        assert data["host"] == "127.0.0.1"
        assert data["port"] == 8642

    def test_read_pid_file_not_exists(self, pid_manager):
        """Test reading non-existent PID file."""
        data = pid_manager.read_pid_file()
        assert data is None

    def test_read_pid_file_invalid_json(self, pid_manager):
        """Test reading corrupted PID file."""
        pid_manager.pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pid_manager.pid_file, "w") as f:
            f.write("invalid json")

        data = pid_manager.read_pid_file()
        assert data is None

    def test_remove_pid_file_success(self, pid_manager):
        """Test removing existing PID file."""
        pid_manager.create_pid_file("127.0.0.1", 8642)

        result = pid_manager.remove_pid_file()

        assert result is True
        assert not pid_manager.pid_file.exists()

    def test_remove_pid_file_not_exists(self, pid_manager):
        """Test removing non-existent PID file."""
        result = pid_manager.remove_pid_file()
        assert result is False

    def test_is_process_alive_current_process(self):
        """Test checking if current process is alive."""
        assert PIDManager.is_process_alive(os.getpid()) is True

    def test_is_process_alive_non_existent(self):
        """Test checking if non-existent process is alive."""
        # Use a very high PID that shouldn't exist
        assert PIDManager.is_process_alive(999999) is False

    def test_get_daemon_info_running(self, pid_manager):
        """Test getting daemon info when running."""
        pid_manager.create_pid_file("127.0.0.1", 8642)

        info = pid_manager.get_daemon_info()

        assert info is not None
        assert info["pid"] == os.getpid()
        assert info["port"] == 8642

    def test_get_daemon_info_not_running(self, pid_manager):
        """Test getting daemon info when not running."""
        info = pid_manager.get_daemon_info()
        assert info is None

    def test_get_daemon_info_stale_pid(self, pid_manager):
        """Test getting daemon info with stale PID file."""
        # Create a stale PID file
        pid_data = {
            "pid": 999999,
            "host": "127.0.0.1",
            "port": 8642,
            "started_at": "2026-01-01T00:00:00",
            "version": "0.1.0",
        }
        pid_manager.pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pid_manager.pid_file, "w") as f:
            json.dump(pid_data, f)

        info = pid_manager.get_daemon_info()

        assert info is None
        assert not pid_manager.pid_file.exists()  # Should be cleaned up

    def test_send_signal_success(self, pid_manager):
        """Test sending signal to running process."""
        pid_manager.create_pid_file("127.0.0.1", 8642)

        # Sending signal 0 just checks if process exists
        result = pid_manager.send_signal(0)
        assert result is True

    def test_send_signal_no_pid_file(self, pid_manager):
        """Test sending signal when no PID file exists."""
        result = pid_manager.send_signal(signal.SIGTERM)
        assert result is False

    def test_send_signal_dead_process(self, pid_manager):
        """Test sending signal to dead process."""
        pid_data = {
            "pid": 999999,
            "host": "127.0.0.1",
            "port": 8642,
            "started_at": "2026-01-01T00:00:00",
            "version": "0.1.0",
        }
        pid_manager.pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pid_manager.pid_file, "w") as f:
            json.dump(pid_data, f)

        result = pid_manager.send_signal(signal.SIGTERM)
        assert result is False

    @patch("os.kill")
    def test_terminate_success(self, mock_kill, pid_manager):
        """Test terminating daemon process."""
        pid_manager.create_pid_file("127.0.0.1", 8642)

        # Mock os.kill to simulate process termination
        def side_effect(pid, sig):
            if sig == signal.SIGTERM:
                # Simulate process dying after SIGTERM
                pass

        mock_kill.side_effect = side_effect

        with patch.object(pid_manager, "is_process_alive", return_value=False):
            result = pid_manager.terminate(timeout=1)
            assert result is True

    def test_terminate_no_daemon(self, pid_manager):
        """Test terminating when no daemon is running."""
        result = pid_manager.terminate()
        assert result is False


class TestPortManager:
    """Test cases for PortManager."""

    def test_is_port_in_use_free_port(self):
        """Test checking a free port."""
        # Mock socket to simulate a free port
        with patch("socket.socket") as mock_socket_class:
            mock_socket = Mock()
            mock_socket_class.return_value.__enter__ = Mock(return_value=mock_socket)
            mock_socket_class.return_value.__exit__ = Mock(return_value=False)
            # Simulate successful bind (port is free)
            mock_socket.bind = Mock()

            in_use = PortManager.is_port_in_use(65000, "127.0.0.1")
            assert in_use is False

    def test_is_port_in_use_bound_port(self):
        """Test checking a port that's in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            bound_port = s.getsockname()[1]

            # Port should be in use
            in_use = PortManager.is_port_in_use(bound_port, "127.0.0.1")
            assert in_use is True

    def test_find_available_port_success(self):
        """Test finding an available port."""
        # Use a high port range that's likely to be free
        port = PortManager.find_available_port(65000, "127.0.0.1", max_retry=10)

        assert 65000 <= port <= 65009
        # Verify the port is actually free
        assert PortManager.is_port_in_use(port, "127.0.0.1") is False

    def test_find_available_port_failure(self):
        """Test finding a port when all are in use."""
        # Mock is_port_in_use to always return True
        with patch.object(
            PortManager, "is_port_in_use", return_value=True
        ):
            with pytest.raises(PIDFileError) as exc_info:
                PortManager.find_available_port(8642, "127.0.0.1", max_retry=5)

            assert "No available port found" in str(exc_info.value)

    def test_get_port_with_fallback_available(self):
        """Test getting preferred port when available."""
        # Find a free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]

        # This port should be available
        result = PortManager.get_port_with_fallback(
            free_port, "127.0.0.1", auto_increment=False
        )
        assert result == free_port

    def test_get_port_with_fallback_auto_increment(self):
        """Test auto-increment when preferred port is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            bound_port = s.getsockname()[1]

            # This port is in use, should get next available
            result = PortManager.get_port_with_fallback(
                bound_port, "127.0.0.1", auto_increment=True
            )
            assert result != bound_port

    def test_get_port_with_fallback_no_auto_increment(self):
        """Test error when port in use and auto_increment is False."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            bound_port = s.getsockname()[1]

            with pytest.raises(PIDFileError) as exc_info:
                PortManager.get_port_with_fallback(
                    bound_port, "127.0.0.1", auto_increment=False
                )

            assert "already in use" in str(exc_info.value)
