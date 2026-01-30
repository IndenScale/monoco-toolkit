from unittest.mock import patch
from monoco.features.agent import SessionManager, ApoptosisManager, DEFAULT_ROLES


@patch("subprocess.Popen")
def test_apoptosis_flow(mock_popen):
    # Setup mock process
    mock_process = mock_popen.return_value
    mock_process.pid = 6666
    mock_process.wait.return_value = None
    mock_process.returncode = 0

    manager = SessionManager()
    apoptosis = ApoptosisManager(manager)

    # 1. Start a victim session
    role = DEFAULT_ROLES[0]  # Planner
    victim = manager.create_session("ISSUE-666", role)
    victim.start()

    # In async mode, it stays running
    assert victim.model.status == "running"

    # 2. Simulate Crash & Trigger Apoptosis
    apoptosis.trigger_apoptosis(victim.model.id)

    # 3. Validation
    # Victim should be crashed
    assert victim.model.status == "crashed"

    # Coroner should have run (we can't easily check internal print output in unit test without capturing stdout,
    # but we can check if a new session was created for coroner)
    # The current _perform_autopsy implementation creates a session but doesn't store it in the MAIN manager
    # in a way that is easily retrievable unless we mocking inputs.
    # However, SessionManager stores all sessions.

    sessions = manager.list_sessions("ISSUE-666")
    # Should have at least 2 sessions now: Victim (crashed) and Coroner (completed)
    assert len(sessions) >= 2

    coroner_sessions = [s for s in sessions if s.model.role_name == "Coroner"]
    assert len(coroner_sessions) > 0
    # Coroner ran start(), so status should be running
    assert coroner_sessions[0].model.status == "running"
