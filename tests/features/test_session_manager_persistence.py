"""
Tests for SessionManager persistence and cross-process session visibility.

This module tests the ability of the Daemon to list sessions created by CLI subprocesses,
ensuring session persistence works correctly across different contexts.
"""

import json
import os
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from monoco.features.agent.manager import SessionManager
from monoco.features.agent.session import Session, RuntimeSession
from monoco.features.agent.models import RoleTemplate


@pytest.fixture
def role_template():
    """Default role template for testing."""
    return RoleTemplate(
        name="TestRole",
        description="Test Role",
        trigger="manual",
        goal="Test goal",
        system_prompt="Test prompt",
        engine="gemini"
    )


def test_session_manager_creates_sessions_directory(project_env):
    """Test that SessionManager creates the sessions directory if it doesn't exist."""
    sessions_dir = project_env / ".monoco" / "sessions"
    
    # Ensure directory doesn't exist initially
    if sessions_dir.exists():
        for f in sessions_dir.glob("*.json"):
            f.unlink()
        sessions_dir.rmdir()
    
    assert not sessions_dir.exists()
    
    # Initialize manager
    manager = SessionManager(project_root=project_env)
    
    # Directory should be created
    assert sessions_dir.exists()
    assert sessions_dir.is_dir()


def test_session_saved_to_disk_on_create(project_env, role_template):
    """Test that creating a session immediately persists it to disk."""
    manager = SessionManager(project_root=project_env)
    
    runtime = manager.create_session("ISSUE-TEST-001", role_template)
    session_id = runtime.model.id
    
    # Verify file exists
    session_file = project_env / ".monoco" / "sessions" / f"{session_id}.json"
    assert session_file.exists()
    
    # Verify content
    data = json.loads(session_file.read_text())
    assert data["id"] == session_id
    assert data["issue_id"] == "ISSUE-TEST-001"
    assert data["role_name"] == "TestRole"
    assert data["status"] == "pending"
    assert data["branch_name"] == runtime.model.branch_name


def test_session_saved_on_status_change(project_env, role_template):
    """Test that session status changes are persisted to disk."""
    manager = SessionManager(project_root=project_env)
    
    runtime = manager.create_session("ISSUE-TEST-002", role_template)
    session_id = runtime.model.id
    session_file = project_env / ".monoco" / "sessions" / f"{session_id}.json"
    
    # Initial status
    data = json.loads(session_file.read_text())
    assert data["status"] == "pending"
    
    # Update status via refresh_status (simulating status change)
    runtime.model.status = "running"
    runtime._save()
    
    # Verify persisted
    data = json.loads(session_file.read_text())
    assert data["status"] == "running"


def test_session_manager_loads_existing_sessions(project_env, role_template):
    """Test that SessionManager loads existing sessions from disk on init."""
    # Create first manager and session
    manager1 = SessionManager(project_root=project_env)
    runtime1 = manager1.create_session("ISSUE-TEST-003", role_template)
    session_id = runtime1.model.id
    
    # Create second manager (simulating CLI restart or Daemon start)
    manager2 = SessionManager(project_root=project_env)
    
    # Verify session is loaded
    loaded_runtime = manager2.get_session(session_id)
    assert loaded_runtime is not None
    assert loaded_runtime.model.id == session_id
    assert loaded_runtime.model.issue_id == "ISSUE-TEST-003"
    assert loaded_runtime.model.role_name == "TestRole"


def test_loaded_session_is_observer_mode(project_env, role_template):
    """Test that loaded sessions start in observer mode (no worker attached)."""
    # Create and start session with first manager
    manager1 = SessionManager(project_root=project_env)
    runtime1 = manager1.create_session("ISSUE-TEST-004", role_template)
    session_id = runtime1.model.id
    
    # Load with second manager
    manager2 = SessionManager(project_root=project_env)
    loaded_runtime = manager2.get_session(session_id)
    
    # Should be in observer mode (no worker)
    assert loaded_runtime.worker is None
    
    # Operations requiring worker should fail
    with pytest.raises(RuntimeError, match="observer mode"):
        loaded_runtime.start()
    
    with pytest.raises(RuntimeError, match="observer mode"):
        loaded_runtime.suspend()
    
    with pytest.raises(RuntimeError, match="observer mode"):
        loaded_runtime.resume()
    
    # But terminate and refresh_status should work
    loaded_runtime.terminate()  # Should not raise
    loaded_runtime.refresh_status()  # Should not raise


def test_session_manager_lists_all_sessions(project_env, role_template):
    """Test that SessionManager can list all sessions."""
    manager = SessionManager(project_root=project_env)
    
    # Create multiple sessions
    runtime1 = manager.create_session("ISSUE-LIST-1", role_template)
    runtime2 = manager.create_session("ISSUE-LIST-2", role_template)
    runtime3 = manager.create_session("ISSUE-LIST-1", role_template)  # Same issue
    
    # List all sessions
    all_sessions = manager.list_sessions()
    assert len(all_sessions) == 3
    
    session_ids = {s.model.id for s in all_sessions}
    assert runtime1.model.id in session_ids
    assert runtime2.model.id in session_ids
    assert runtime3.model.id in session_ids


def test_session_manager_list_filters_by_issue(project_env, role_template):
    """Test that SessionManager can filter sessions by issue_id."""
    manager = SessionManager(project_root=project_env)
    
    # Create sessions for different issues
    runtime1 = manager.create_session("ISSUE-FILTER-A", role_template)
    runtime2 = manager.create_session("ISSUE-FILTER-B", role_template)
    runtime3 = manager.create_session("ISSUE-FILTER-A", role_template)
    
    # List sessions for specific issue
    issue_a_sessions = manager.list_sessions("ISSUE-FILTER-A")
    assert len(issue_a_sessions) == 2
    
    issue_b_sessions = manager.list_sessions("ISSUE-FILTER-B")
    assert len(issue_b_sessions) == 1
    assert issue_b_sessions[0].model.id == runtime2.model.id


def test_cross_manager_session_visibility(project_env, role_template):
    """
    Test that sessions created by one manager are visible to another.
    
    This simulates the scenario where CLI creates a session and Daemon
    needs to list it.
    """
    # CLI creates a session
    cli_manager = SessionManager(project_root=project_env)
    runtime = cli_manager.create_session("ISSUE-CROSS-001", role_template)
    session_id = runtime.model.id
    
    # Daemon loads and lists sessions
    daemon_manager = SessionManager(project_root=project_env)
    daemon_sessions = daemon_manager.list_sessions()
    
    # Daemon should see the CLI-created session
    session_ids = {s.model.id for s in daemon_sessions}
    assert session_id in session_ids
    
    # Daemon can get specific session details
    loaded = daemon_manager.get_session(session_id)
    assert loaded.model.issue_id == "ISSUE-CROSS-001"


def test_session_persists_pid_field(project_env, role_template):
    """Test that the pid field is correctly persisted and loaded."""
    manager = SessionManager(project_root=project_env)
    runtime = manager.create_session("ISSUE-PID-001", role_template)
    session_id = runtime.model.id
    
    # Simulate setting pid (normally done by worker)
    runtime.model.pid = 12345
    runtime._save()
    
    # Verify persisted
    session_file = project_env / ".monoco" / "sessions" / f"{session_id}.json"
    data = json.loads(session_file.read_text())
    assert data["pid"] == 12345
    
    # Load with new manager and verify
    manager2 = SessionManager(project_root=project_env)
    loaded = manager2.get_session(session_id)
    assert loaded.model.pid == 12345


def test_session_with_pid_updates_on_refresh(project_env, role_template):
    """Test that refresh_status correctly checks process existence via pid."""
    manager = SessionManager(project_root=project_env)
    runtime = manager.create_session("ISSUE-PID-002", role_template)
    session_id = runtime.model.id
    
    # Test case 1: No PID set - should mark as terminated when loaded
    runtime.model.pid = None
    runtime.model.status = "running"
    runtime._save()
    
    # Create new manager which will reload and call refresh_status
    manager2 = SessionManager(project_root=project_env)
    loaded = manager2.get_session(session_id)
    
    # Without a valid PID, session should be marked as terminated
    assert loaded.model.status == "terminated"
    
    # Test case 2: With current process PID (exists) - should keep status
    loaded.model.pid = os.getpid()  # Current process definitely exists
    loaded.model.status = "running"
    loaded._save()
    
    # Create another manager to reload
    manager3 = SessionManager(project_root=project_env)
    loaded2 = manager3.get_session(session_id)
    
    # Process exists, so status should remain running
    assert loaded2.model.status == "running"


def test_session_timestamps_persisted(project_env, role_template):
    """Test that created_at and updated_at timestamps are persisted."""
    manager = SessionManager(project_root=project_env)
    runtime = manager.create_session("ISSUE-TIME-001", role_template)
    session_id = runtime.model.id
    
    session_file = project_env / ".monoco" / "sessions" / f"{session_id}.json"
    data = json.loads(session_file.read_text())
    
    # Verify timestamps exist and are valid ISO format
    assert "created_at" in data
    assert "updated_at" in data
    
    # Should be parseable as datetime
    created = datetime.fromisoformat(data["created_at"])
    updated = datetime.fromisoformat(data["updated_at"])
    
    assert isinstance(created, datetime)
    assert isinstance(updated, datetime)


def test_corrupted_session_file_handled(project_env, role_template):
    """Test that corrupted session files are handled gracefully."""
    # Create a valid session first
    manager1 = SessionManager(project_root=project_env)
    runtime = manager1.create_session("ISSUE-CORRUPT-001", role_template)
    valid_session_id = runtime.model.id
    
    # Manually create a corrupted session file
    sessions_dir = project_env / ".monoco" / "sessions"
    (sessions_dir / "corrupted.json").write_text("not valid json{}")
    
    # Create an invalid session file (missing required fields)
    (sessions_dir / "incomplete.json").write_text('{"id": "incomplete"}')
    
    # New manager should load without crashing
    manager2 = SessionManager(project_root=project_env)
    
    # Valid session should still be loaded
    assert manager2.get_session(valid_session_id) is not None
    
    # Corrupted files should be skipped (no exception raised)
    # and valid sessions should still be accessible
    all_sessions = manager2.list_sessions()
    assert len(all_sessions) >= 1


def test_session_file_format(project_env, role_template):
    """Test that session files have the expected JSON structure."""
    manager = SessionManager(project_root=project_env)
    runtime = manager.create_session("ISSUE-FORMAT-001", role_template)
    session_id = runtime.model.id
    
    session_file = project_env / ".monoco" / "sessions" / f"{session_id}.json"
    data = json.loads(session_file.read_text())
    
    # Verify expected fields
    expected_fields = {
        "id", "issue_id", "role_name", "status", "branch_name",
        "pid", "created_at", "updated_at"
    }
    assert set(data.keys()) == expected_fields


def test_terminate_session_updates_file(project_env, role_template):
    """Test that terminating a session updates the persisted file."""
    manager = SessionManager(project_root=project_env)
    runtime = manager.create_session("ISSUE-TERM-001", role_template)
    session_id = runtime.model.id
    
    session_file = project_env / ".monoco" / "sessions" / f"{session_id}.json"
    
    # Verify initial status
    data = json.loads(session_file.read_text())
    assert data["status"] == "pending"
    
    # Terminate
    manager.terminate_session(session_id)
    
    # Verify updated status
    data = json.loads(session_file.read_text())
    assert data["status"] == "terminated"


def test_multiple_managers_same_project(project_env, role_template):
    """Test that multiple managers can coexist for the same project."""
    manager1 = SessionManager(project_root=project_env)
    
    # Create session with first manager
    runtime = manager1.create_session("ISSUE-MULTI-001", role_template)
    session_id = runtime.model.id
    
    # First manager should see the session
    assert manager1.get_session(session_id) is not None
    
    # Create second manager AFTER session is created (simulating new process)
    # This tests that sessions are loaded from disk on initialization
    manager2 = SessionManager(project_root=project_env)
    
    # Second manager should also see the session (loaded from disk)
    assert manager2.get_session(session_id) is not None
    
    # Terminate with first manager
    manager1.terminate_session(session_id)
    
    # Verify file is updated
    session_file = project_env / ".monoco" / "sessions" / f"{session_id}.json"
    data = json.loads(session_file.read_text())
    assert data["status"] == "terminated"
