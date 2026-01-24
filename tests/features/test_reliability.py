from monoco.features.scheduler import SessionManager, ApoptosisManager, DEFAULT_ROLES


def test_apoptosis_flow():
    manager = SessionManager()
    apoptosis = ApoptosisManager(manager)

    # 1. Start a victim session
    role = DEFAULT_ROLES[0]  # crafter
    victim = manager.create_session("ISSUE-666", role)
    victim.start()

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
    # Should have at least 2 sessions now: Victim (crashed) and Coroner (terminated)
    assert len(sessions) >= 2

    coroner_sessions = [s for s in sessions if s.model.role_name == "coroner"]
    assert len(coroner_sessions) > 0
    assert coroner_sessions[0].model.status == "terminated"
