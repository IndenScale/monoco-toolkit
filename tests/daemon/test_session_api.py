"""
Tests for Daemon API endpoints related to session management.

This module tests the Daemon's ability to expose session information via API,
ensuring CLI-created sessions are visible to the Daemon and its clients.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from monoco.features.agent.manager import SessionManager
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


def test_daemon_can_access_cli_created_sessions(project_env, role_template):
    """
    Test that Daemon can access sessions created by CLI subprocesses.
    
    This simulates the workflow:
    1. CLI creates a session
    2. Daemon starts and loads all sessions
    3. Daemon can list and monitor the CLI-created session
    """
    # Step 1: CLI creates a session
    cli_manager = SessionManager(project_root=project_env)
    runtime = cli_manager.create_session("ISSUE-CLI-001", role_template)
    session_id = runtime.model.id
    
    # Step 2: Daemon starts (new SessionManager instance)
    daemon_manager = SessionManager(project_root=project_env)
    
    # Step 3: Daemon lists sessions
    sessions = daemon_manager.list_sessions()
    session_ids = [s.model.id for s in sessions]
    
    # Verify Daemon can see CLI-created session
    assert session_id in session_ids
    
    # Verify session details
    loaded_session = daemon_manager.get_session(session_id)
    assert loaded_session.model.issue_id == "ISSUE-CLI-001"
    assert loaded_session.model.role_name == "TestRole"


def test_daemon_lists_sessions_by_issue(project_env, role_template):
    """Test that Daemon can filter sessions by issue_id."""
    # Create sessions for different issues
    cli_manager = SessionManager(project_root=project_env)
    runtime1 = cli_manager.create_session("ISSUE-FILTER-X", role_template)
    runtime2 = cli_manager.create_session("ISSUE-FILTER-Y", role_template)
    
    # Daemon loads sessions
    daemon_manager = SessionManager(project_root=project_env)
    
    # Filter by issue
    x_sessions = daemon_manager.list_sessions("ISSUE-FILTER-X")
    y_sessions = daemon_manager.list_sessions("ISSUE-FILTER-Y")
    
    assert len(x_sessions) == 1
    assert x_sessions[0].model.id == runtime1.model.id
    
    assert len(y_sessions) == 1
    assert y_sessions[0].model.id == runtime2.model.id


def test_daemon_monitor_detects_session_status(project_env, role_template):
    """
    Test that Daemon can monitor session status changes.
    
    This simulates the Daemon's monitoring loop checking session status.
    """
    # CLI creates a session with a fake PID
    cli_manager = SessionManager(project_root=project_env)
    runtime = cli_manager.create_session("ISSUE-MONITOR-001", role_template)
    
    # Set a fake PID that doesn't exist
    runtime.model.pid = 999999
    runtime.model.status = "running"
    runtime._save()
    
    # Daemon loads session
    daemon_manager = SessionManager(project_root=project_env)
    loaded = daemon_manager.get_session(runtime.model.id)
    
    # Daemon checks status (simulating monitor loop)
    status = loaded.refresh_status()
    
    # Should detect that process doesn't exist
    assert status == "terminated"
    assert loaded.model.status == "terminated"


def test_session_persistence_across_restarts(project_env, role_template):
    """
    Test that sessions persist across multiple manager restarts.
    
    This simulates:
    1. CLI creates session
    2. Daemon starts, sees session
    3. Daemon restarts, still sees session
    4. CLI lists sessions, sees the same session
    """
    # CLI creates session
    cli_manager = SessionManager(project_root=project_env)
    runtime = cli_manager.create_session("ISSUE-PERSIST-001", role_template)
    session_id = runtime.model.id
    
    # First Daemon instance
    daemon_manager_1 = SessionManager(project_root=project_env)
    assert daemon_manager_1.get_session(session_id) is not None
    
    # Second Daemon instance (simulating restart)
    daemon_manager_2 = SessionManager(project_root=project_env)
    assert daemon_manager_2.get_session(session_id) is not None
    
    # New CLI instance
    cli_manager_2 = SessionManager(project_root=project_env)
    assert cli_manager_2.get_session(session_id) is not None


def test_session_json_serialization(project_env, role_template):
    """Test that session data is correctly serialized to JSON."""
    manager = SessionManager(project_root=project_env)
    runtime = manager.create_session("ISSUE-SERIAL-001", role_template)
    session_id = runtime.model.id
    
    # Read the persisted file
    session_file = project_env / ".monoco" / "sessions" / f"{session_id}.json"
    assert session_file.exists()
    
    # Verify it's valid JSON
    with open(session_file) as f:
        data = json.load(f)
    
    # Verify all expected fields
    assert data["id"] == session_id
    assert data["issue_id"] == "ISSUE-SERIAL-001"
    assert data["role_name"] == "TestRole"
    assert data["status"] == "pending"
    assert "branch_name" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "pid" in data


def test_daemon_can_terminate_cli_session(project_env, role_template):
    """Test that Daemon can terminate a session created by CLI."""
    # CLI creates session
    cli_manager = SessionManager(project_root=project_env)
    runtime = cli_manager.create_session("ISSUE-TERM-CLI-001", role_template)
    session_id = runtime.model.id
    
    # Daemon terminates session
    daemon_manager = SessionManager(project_root=project_env)
    daemon_manager.terminate_session(session_id)
    
    # Verify session is terminated
    session_file = project_env / ".monoco" / "sessions" / f"{session_id}.json"
    with open(session_file) as f:
        data = json.load(f)
    assert data["status"] == "terminated"


def test_multiple_cli_sessions_visible_to_daemon(project_env, role_template):
    """Test that multiple CLI-created sessions are all visible to Daemon."""
    cli_manager = SessionManager(project_root=project_env)
    
    # Create multiple sessions
    sessions = []
    for i in range(5):
        runtime = cli_manager.create_session(f"ISSUE-BULK-{i:03d}", role_template)
        sessions.append(runtime.model.id)
    
    # Daemon sees all sessions
    daemon_manager = SessionManager(project_root=project_env)
    daemon_sessions = daemon_manager.list_sessions()
    daemon_session_ids = {s.model.id for s in daemon_sessions}
    
    for session_id in sessions:
        assert session_id in daemon_session_ids


def test_session_branch_name_persistence(project_env, role_template):
    """Test that branch names are correctly persisted and loaded."""
    manager = SessionManager(project_root=project_env)
    runtime = manager.create_session("ISSUE-BRANCH-001", role_template)
    session_id = runtime.model.id
    
    # Verify branch name format
    assert runtime.model.branch_name.startswith("agent/ISSUE-BRANCH-001/")
    
    # Load with new manager
    manager2 = SessionManager(project_root=project_env)
    loaded = manager2.get_session(session_id)
    
    # Branch name should be preserved
    assert loaded.model.branch_name == runtime.model.branch_name
