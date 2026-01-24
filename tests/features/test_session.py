from monoco.features.scheduler import SessionManager, DEFAULT_ROLES


def test_create_session():
    manager = SessionManager()
    role = DEFAULT_ROLES[0]
    runtime = manager.create_session("ISSUE-456", role)

    assert runtime.model.issue_id == "ISSUE-456"
    assert runtime.model.role_name == "crafter"
    assert runtime.model.status == "pending"
    assert runtime.model.branch_name.startswith("agent/ISSUE-456/")


def test_session_lifecycle():
    manager = SessionManager()
    role = DEFAULT_ROLES[0]
    runtime = manager.create_session("ISSUE-456", role)

    runtime.start()
    assert runtime.model.status == "running"

    runtime.suspend()
    assert runtime.model.status == "suspended"

    runtime.resume()
    assert runtime.model.status == "running"

    # Manager terminate wrapper
    manager.terminate_session(runtime.model.id)
    assert runtime.model.status == "terminated"


def test_list_sessions():
    manager = SessionManager()
    role = DEFAULT_ROLES[0]

    s1 = manager.create_session("ISSUE-A", role)
    s2 = manager.create_session("ISSUE-B", role)

    all_sessions = manager.list_sessions()
    assert len(all_sessions) == 2

    issue_a_sessions = manager.list_sessions("ISSUE-A")
    assert len(issue_a_sessions) == 1
    assert issue_a_sessions[0] == s1
