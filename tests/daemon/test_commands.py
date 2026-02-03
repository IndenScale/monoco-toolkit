"""Tests for Monoco Daemon commands."""

import json
import os
import signal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer
from typer.testing import CliRunner

from monoco.daemon.commands import serve_app

runner = CliRunner()


class TestServeStart:
    """Test cases for serve start command."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace with .monoco directory."""
        monoco_dir = tmp_path / ".monoco"
        monoco_dir.mkdir()
        return tmp_path

    @patch("monoco.daemon.commands.uvicorn.run")
    @patch("monoco.daemon.commands.PortManager.is_port_in_use")
    def test_start_success(
        self, mock_is_port_in_use, mock_uvicorn_run, temp_workspace
    ):
        """Test successful daemon start."""
        mock_is_port_in_use.return_value = False

        result = runner.invoke(
            serve_app,
            ["start", "--root", str(temp_workspace), "--port", "8642"],
        )

        assert result.exit_code == 0
        assert "Starting Monoco Daemon" in result.output
        mock_uvicorn_run.assert_called_once()

    @patch("monoco.daemon.commands.PortManager.is_port_in_use")
    def test_start_port_in_use(self, mock_is_port_in_use, temp_workspace):
        """Test start with port already in use."""
        mock_is_port_in_use.return_value = True

        result = runner.invoke(
            serve_app,
            [
                "start",
                "--root",
                str(temp_workspace),
                "--port",
                "8642",
                "--no-auto-port",
            ],
        )

        assert result.exit_code == 1
        assert "already in use" in result.output

    @patch("monoco.daemon.commands.uvicorn.run")
    @patch("monoco.daemon.commands.PortManager.is_port_in_use")
    def test_start_auto_port(
        self, mock_is_port_in_use, mock_uvicorn_run, temp_workspace
    ):
        """Test start with auto port selection."""
        # First call (port 8642) returns True (in use), second returns False
        mock_is_port_in_use.side_effect = [True, False]

        result = runner.invoke(
            serve_app,
            ["start", "--root", str(temp_workspace), "--port", "8642"],
        )

        assert result.exit_code == 0
        assert "Port 8642 is in use, using port 8643 instead" in result.output

    @patch("monoco.daemon.commands.uvicorn.run")
    @patch("monoco.daemon.commands.PortManager.is_port_in_use")
    def test_start_already_running(
        self, mock_is_port_in_use, mock_uvicorn_run, temp_workspace
    ):
        """Test start when daemon already running."""
        mock_is_port_in_use.return_value = False

        # Create PID file to simulate running daemon
        pid_file = temp_workspace / ".monoco" / "run" / "monoco.pid"
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pid_file, "w") as f:
            json.dump(
                {
                    "pid": os.getpid(),
                    "host": "127.0.0.1",
                    "port": 8642,
                    "started_at": "2026-01-01T00:00:00",
                    "version": "0.1.0",
                },
                f,
            )

        result = runner.invoke(
            serve_app,
            ["start", "--root", str(temp_workspace)],
        )

        assert result.exit_code == 0  # Exit gracefully
        assert "already running" in result.output


class TestServeStop:
    """Test cases for serve stop command."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace with .monoco directory."""
        monoco_dir = tmp_path / ".monoco"
        monoco_dir.mkdir()
        return tmp_path

    @patch("monoco.daemon.commands.PIDManager.terminate")
    @patch("monoco.daemon.commands.PIDManager.get_daemon_info")
    def test_stop_success(self, mock_get_info, mock_terminate, temp_workspace):
        """Test successful daemon stop."""
        mock_get_info.return_value = {
            "pid": 12345,
            "host": "127.0.0.1",
            "port": 8642,
        }
        mock_terminate.return_value = True

        result = runner.invoke(
            serve_app,
            ["stop", "--root", str(temp_workspace)],
        )

        assert result.exit_code == 0
        assert "stopped successfully" in result.output
        mock_terminate.assert_called_once()

    def test_stop_not_running(self, temp_workspace):
        """Test stop when daemon not running."""
        result = runner.invoke(
            serve_app,
            ["stop", "--root", str(temp_workspace)],
        )

        assert result.exit_code == 0
        assert "not running" in result.output

    @patch("monoco.daemon.commands.PIDManager.terminate")
    @patch("monoco.daemon.commands.PIDManager.get_daemon_info")
    def test_stop_failure(self, mock_get_info, mock_terminate, temp_workspace):
        """Test stop when termination fails."""
        mock_get_info.return_value = {
            "pid": 12345,
            "host": "127.0.0.1",
            "port": 8642,
        }
        mock_terminate.return_value = False

        result = runner.invoke(
            serve_app,
            ["stop", "--root", str(temp_workspace)],
        )

        assert result.exit_code == 1
        assert "Failed to stop" in result.output


class TestServeStatus:
    """Test cases for serve status command."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace with .monoco directory."""
        monoco_dir = tmp_path / ".monoco"
        monoco_dir.mkdir()
        return tmp_path

    def test_status_not_running(self, temp_workspace):
        """Test status when daemon not running."""
        result = runner.invoke(
            serve_app,
            ["status", "--root", str(temp_workspace)],
        )

        assert result.exit_code == 0
        assert "not running" in result.output

    @patch("monoco.daemon.commands.PIDManager.get_daemon_info")
    def test_status_running(self, mock_get_info, temp_workspace):
        """Test status when daemon is running."""
        mock_get_info.return_value = {
            "pid": 12345,
            "host": "127.0.0.1",
            "port": 8642,
            "version": "0.1.0",
            "started_at": "2026-02-03T10:00:00",
        }

        result = runner.invoke(
            serve_app,
            ["status", "--root", str(temp_workspace)],
        )

        assert result.exit_code == 0
        assert "Running" in result.output
        assert "12345" in result.output
        assert "8642" in result.output
        assert "http://127.0.0.1:8642" in result.output


class TestServeRestart:
    """Test cases for serve restart command."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace with .monoco directory."""
        monoco_dir = tmp_path / ".monoco"
        monoco_dir.mkdir()
        return tmp_path

    @patch("monoco.daemon.commands.serve_start")
    @patch("monoco.daemon.commands.serve_stop")
    @patch("monoco.daemon.commands.PIDManager.get_daemon_info")
    def test_restart_calls_stop_then_start(
        self,
        mock_get_info,
        mock_stop,
        mock_start,
        temp_workspace,
    ):
        """Test restart calls stop then start when daemon is running."""
        mock_get_info.return_value = {
            "pid": 12345,
            "host": "127.0.0.1",
            "port": 8642,
        }

        from monoco.daemon.commands import serve_restart

        serve_restart(root=str(temp_workspace))

        mock_stop.assert_called_once()
        mock_start.assert_called_once()

    @patch("monoco.daemon.commands.serve_start")
    @patch("monoco.daemon.commands.PIDManager.get_daemon_info")
    def test_restart_start_only_when_not_running(
        self, mock_get_info, mock_start, temp_workspace
    ):
        """Test restart only calls start when daemon is not running."""
        mock_get_info.return_value = None

        from monoco.daemon.commands import serve_restart

        serve_restart(root=str(temp_workspace))

        mock_start.assert_called_once()


class TestServeCleanup:
    """Test cases for serve cleanup command."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace with .monoco directory."""
        monoco_dir = tmp_path / ".monoco"
        monoco_dir.mkdir()
        return tmp_path

    @patch("subprocess.run")
    def test_cleanup_no_orphans(self, mock_run, temp_workspace):
        """Test cleanup when no orphaned processes exist."""
        mock_run.return_value = Mock(stdout="", returncode=0)

        result = runner.invoke(
            serve_app,
            ["cleanup", "--root", str(temp_workspace)],
        )

        assert result.exit_code == 0
        assert "No orphaned processes found" in result.output

    @patch("subprocess.run")
    def test_cleanup_with_stale_pid_file(self, mock_run, temp_workspace):
        """Test cleanup removes stale PID file."""
        # Create stale PID file
        pid_file = temp_workspace / ".monoco" / "run" / "monoco.pid"
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pid_file, "w") as f:
            json.dump(
                {
                    "pid": 999999,  # Non-existent PID
                    "host": "127.0.0.1",
                    "port": 8642,
                    "started_at": "2026-01-01T00:00:00",
                    "version": "0.1.0",
                },
                f,
            )

        mock_run.return_value = Mock(stdout="", returncode=0)

        result = runner.invoke(
            serve_app,
            ["cleanup", "--root", str(temp_workspace)],
        )

        assert result.exit_code == 0
        assert not pid_file.exists()  # Should be removed

    @patch("subprocess.run")
    def test_cleanup_dry_run(self, mock_run, temp_workspace):
        """Test cleanup dry run mode."""
        mock_run.return_value = Mock(
            stdout="user 12345 0.0 0.0 12345 12345 ? S 10:00 0:00 uvicorn monoco.daemon.app",
            returncode=0,
        )

        result = runner.invoke(
            serve_app,
            ["cleanup", "--root", str(temp_workspace), "--dry-run"],
        )

        assert result.exit_code == 0
        assert "[DRY RUN]" in result.output


class TestLegacyServe:
    """Test cases for legacy serve command."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace with .monoco directory."""
        monoco_dir = tmp_path / ".monoco"
        monoco_dir.mkdir()
        return tmp_path

    @patch("monoco.daemon.commands.uvicorn.run")
    def test_legacy_serve_with_reload(self, mock_uvicorn_run, temp_workspace):
        """Test legacy serve command with --reload flag."""
        from monoco.daemon.commands import serve_legacy

        serve_legacy(
            host="127.0.0.1",
            port=8642,
            reload=True,
            root=str(temp_workspace),
            max_agents=None,
        )

        mock_uvicorn_run.assert_called_once()
        # Check that reload=True was passed
        call_kwargs = mock_uvicorn_run.call_args[1]
        assert call_kwargs.get("reload") is True

    @patch("monoco.daemon.commands.uvicorn.run")
    @patch("monoco.daemon.commands.PortManager.is_port_in_use")
    def test_legacy_serve_without_reload(
        self, mock_is_port_in_use, mock_uvicorn_run, temp_workspace
    ):
        """Test legacy serve command without --reload flag uses new logic."""
        mock_is_port_in_use.return_value = False

        from monoco.daemon.commands import serve_legacy

        serve_legacy(
            host="127.0.0.1",
            port=8642,
            reload=False,
            root=str(temp_workspace),
            max_agents=None,
        )

        mock_uvicorn_run.assert_called_once()
