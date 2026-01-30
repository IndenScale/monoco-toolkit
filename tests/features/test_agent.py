from pathlib import Path
from unittest.mock import patch, mock_open
from monoco.features.agent import load_scheduler_config, Worker, DEFAULT_ROLES


def test_load_defaults():
    # If no config file, should return defaults
    with patch("pathlib.Path.exists", return_value=False):
        roles = load_scheduler_config(Path("/tmp"))
        # Ensure we have at least the default roles
        expected_names = {r.name for r in DEFAULT_ROLES}
        loaded_names = set(roles.keys())
        assert expected_names.issubset(loaded_names)


def test_load_config_override():
    yaml_content = """
    roles:
      - name: Planner
        description: Modified Planner
        trigger: manual
        goal: test
        system_prompt: "New prompt"
      - name: new_role
        description: New Role
        trigger: always
        goal: something
        system_prompt: "Sys prompt"
    """
    # We define a dummy Path object to avoid real file system checks
    dummy_path = Path("/tmp")

    with patch("pathlib.Path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=yaml_content)
    ):
        roles = load_scheduler_config(dummy_path)

        # Planner should be overwritten
        assert roles["Planner"].description == "Modified Planner"
        # new_role should be added
        assert "new_role" in roles
        # Builder and other defaults should remain
        assert "Builder" in roles


def test_worker_init():
    role = DEFAULT_ROLES[0]
    worker = Worker(role, "ISSUE-123")
    assert worker.status == "pending"
    assert worker.issue_id == "ISSUE-123"
    assert worker.role.name == "Planner"


@patch("subprocess.Popen")
def test_worker_lifecycle(mock_popen):
    # Setup mock process
    mock_process = mock_popen.return_value
    mock_process.pid = 12345
    # Remove wait setup here, check poll
    mock_process.poll.return_value = None
    mock_process.returncode = 0

    role = DEFAULT_ROLES[0]
    worker = Worker(role, "ISSUE-123")

    # Start calls _execute_work which launches Popen and returns.
    worker.start()

    # Async: should be running
    assert worker.status == "running"

    # Check poll()
    assert worker.poll() == "running"

    # Simulate completion
    mock_process.poll.return_value = 0
    assert worker.poll() == "completed"
    assert worker.status == "completed"

    worker.stop()
    assert worker.status == "terminated"
