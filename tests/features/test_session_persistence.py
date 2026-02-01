import json
import os
from unittest.mock import patch
from monoco.features.agent import SessionManager, DEFAULT_ROLES
from monoco.features.agent.session import Session

def test_session_persistence(project_env):
    """
    Test that sessions are persisted to disk and can be reloaded.
    """
    # 1. Create a session with Manager A
    manager = SessionManager(project_root=project_env)
    role = DEFAULT_ROLES[0]
    runtime = manager.create_session("ISSUE-PERSIST-1", role)
    
    session_id = runtime.model.id
    
    # 2. Verify file exists
    session_file = project_env / ".monoco" / "sessions" / f"{session_id}.json"
    assert session_file.exists()
    
    data = json.loads(session_file.read_text())
    assert data["id"] == session_id
    assert data["status"] == "pending"
    assert data.get("pid") is None

    # 3. Start the session (mocking process)
    with patch("subprocess.Popen") as mock_popen:
        mock_process = mock_popen.return_value
        mock_process.pid = 9999
        mock_process.poll.return_value = None
        
        runtime.start()
        
        # Verify persisted status update
        data = json.loads(session_file.read_text())
        assert data["status"] == "running"
        assert data["pid"] == 9999

    # 4. Create new Manager B (simulating CLI restart)
    # Re-initialize manager to trigger load
    manager_b = SessionManager(project_root=project_env)
    
    # Verify session loaded
    loaded_runtime = manager_b.get_session(session_id)
    assert loaded_runtime is not None
    assert loaded_runtime.model.issue_id == "ISSUE-PERSIST-1"
    assert loaded_runtime.model.pid == 9999
    
    # 5. Verify Observer Mode behavior
    # In this test environment, PID 9999 likely doesn't exist.
    # refresh_status should detect it's gone and mark terminated.
    status = loaded_runtime.refresh_status()
    assert status == "terminated"
    assert loaded_runtime.model.status == "terminated"
    
    # Verify persistence of termination
    data = json.loads(session_file.read_text())
    assert data["status"] == "terminated"

def test_session_observer_mode_alive_process(project_env):
    """
    Test that loaded session correctly identifies running process.
    """
    # Create a dummy session file manually
    my_pid = os.getpid()
    session_id = "test-alive-session"
    session_data = {
        "id": session_id,
        "issue_id": "ISSUE-ALIVE",
        "role_name": "Default",
        "status": "running",
        "branch_name": "agent/test",
        "pid": my_pid, # Point to THIS process which definitely exists
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    
    sessions_dir = project_env / ".monoco" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    (sessions_dir / f"{session_id}.json").write_text(json.dumps(session_data))
    
    # Initialize manager
    manager = SessionManager(project_root=project_env)
    
    loaded_runtime = manager.get_session(session_id)
    assert loaded_runtime is not None
    
    # Since my_pid is running, status should remain "running"
    status = loaded_runtime.refresh_status()
    assert status == "running"
    assert loaded_runtime.model.status == "running"

