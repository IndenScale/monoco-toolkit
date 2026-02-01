from unittest.mock import patch
from monoco.features.agent import SessionManager, DEFAULT_ROLES


def test_create_session():
    manager = SessionManager()
    role = DEFAULT_ROLES[0]
    runtime = manager.create_session("ISSUE-456", role)

    assert runtime.model.issue_id == "ISSUE-456"
    assert runtime.model.role_name == "Default"
    assert runtime.model.status == "pending"
    assert runtime.model.branch_name.startswith("agent/ISSUE-456/")


@patch("subprocess.Popen")
def test_session_lifecycle(mock_popen):
    # Setup mock process
    mock_process = mock_popen.return_value
    mock_process.pid = 5555
    mock_process.wait.return_value = None
    mock_process.returncode = 0

    manager = SessionManager()
    role = DEFAULT_ROLES[0]
    runtime = manager.create_session("ISSUE-456", role)

    runtime.start()
    # Async: start() returns immediately, putting session in 'running' state
    assert runtime.model.status == "running"

    # Simulate poll to check completion (mock process has returncode 0)
    # But poll() on mock process object needs to be mocked or the object used correctly
    # worker._process is mock_process.
    # To test running->completed transition, we need to invoke refresh_status()
    # Configure mock poll
    mock_process.poll.return_value = None  # Still running
    assert runtime.refresh_status() == "running"

    # Configure mock poll to finish
    mock_process.poll.return_value = 0
    assert runtime.refresh_status() == "completed"

    # Test suspend/resume flow
    # We need to restart to test suspend (since it's completed now)
    # But worker.start() checks status. We need to reset manualy or start new session.
    # Let's just create new runtime for suspend test to be clean

    runtime2 = manager.create_session("ISSUE-457", role)
    runtime2.start()
    assert runtime2.model.status == "running"

    runtime2.suspend()
    assert runtime2.model.status == "suspended"

    runtime2.resume()
    assert runtime2.model.status == "running"

    # Manager terminate wrapper
    manager.terminate_session(runtime.model.id)
    assert runtime.model.status == "terminated"


def test_list_sessions(tmp_path):
    manager = SessionManager(project_root=tmp_path)
    role = DEFAULT_ROLES[0]

    s1 = manager.create_session("ISSUE-A", role)
    s2 = manager.create_session("ISSUE-B", role)

    all_sessions = manager.list_sessions()
    assert len(all_sessions) == 2

    issue_a_sessions = manager.list_sessions("ISSUE-A")
    assert len(issue_a_sessions) == 1
    assert issue_a_sessions[0] == s1
