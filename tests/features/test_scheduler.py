from pathlib import Path
from unittest.mock import patch, mock_open
from monoco.features.scheduler import load_scheduler_config, Worker, DEFAULT_ROLES


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
      - name: crafter
        description: Modified crafter
        trigger: manual
        goal: test
        tools: []
        system_prompt: "New prompt"
      - name: new_role
        description: New Role
        trigger: always
        goal: something
        tools: [tool1]
        system_prompt: "Sys prompt"
    """
    # We define a dummy Path object to avoid real file system checks
    dummy_path = Path("/tmp")

    with patch("pathlib.Path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=yaml_content)
    ):
        roles = load_scheduler_config(dummy_path)

        # crafter should be overwritten
        assert roles["crafter"].description == "Modified crafter"
        # new_role should be added
        assert "new_role" in roles
        # builder and auditor should remain from defaults
        assert "builder" in roles


def test_worker_init():
    role = DEFAULT_ROLES[0]
    worker = Worker(role, "ISSUE-123")
    assert worker.status == "pending"
    assert worker.issue_id == "ISSUE-123"
    assert worker.role.name == "crafter"


def test_worker_lifecycle():
    role = DEFAULT_ROLES[0]
    worker = Worker(role, "ISSUE-123")
    worker.start()
    assert worker.status == "running"
    worker.stop()
    assert worker.status == "terminated"
