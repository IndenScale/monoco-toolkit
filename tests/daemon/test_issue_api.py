import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure we can import from monoco
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from monoco.daemon.app import app

client = TestClient(app)


@pytest.fixture
def mock_project(tmp_path):
    # Setup temporary issues directory
    issues_root = tmp_path / "Issues"
    issues_root.mkdir()

    # Initialize standard structure
    for subdir in ["Epics", "Features", "Chores", "Fixes"]:
        (issues_root / subdir).mkdir()
        for status in ["open", "backlog", "closed"]:
            (issues_root / subdir / status).mkdir()

    # Create a mock project object
    mock_proj = MagicMock()
    mock_proj.id = "test-project"
    mock_proj.name = "Test Project"
    mock_proj.issues_root = issues_root

    # Mock async notify_move method
    async def mock_notify_move(old_path: str, new_path: str, issue_data: dict):
        pass

    mock_proj.notify_move = mock_notify_move

    return mock_proj


@pytest.fixture
def mock_project_manager(mock_project):
    mock_pm = MagicMock()
    # Mock get_project to return our mock project
    mock_pm.get_project.return_value = mock_project
    # Mock projects dict for fallback listing
    mock_pm.projects = {"test-project": mock_project}
    return mock_pm


def test_create_issue(mock_project_manager):
    """Test creating an issue via API"""

    with patch("monoco.daemon.app.project_manager", new=mock_project_manager):
        payload = {
            "type": "feature",
            "title": "API Test Feature",
            "status": "open",
            "project_id": "test-project",
        }
        response = client.post("/api/v1/issues", json=payload)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["title"] == "API Test Feature"
        assert data["status"] == "open"
        assert data["id"].startswith("FEAT-")


def test_get_issue(mock_project_manager):
    """Test getting an issue via API"""
    with patch("monoco.daemon.app.project_manager", new=mock_project_manager):
        # 1. Create
        payload = {
            "type": "chore",
            "title": "Chore for Get",
            "project_id": "test-project",
        }
        create_res = client.post("/api/v1/issues", json=payload)
        assert create_res.status_code == 200
        issue_id = create_res.json()["id"]

        # 2. Get
        get_res = client.get(f"/api/v1/issues/{issue_id}?project_id=test-project")
        assert get_res.status_code == 200, get_res.text
        data = get_res.json()
        assert data["id"] == issue_id
        assert data["title"] == "Chore for Get"


def test_update_issue(mock_project_manager):
    """Test updating an issue via API"""
    with patch("monoco.daemon.app.project_manager", new=mock_project_manager):
        # 1. Create
        payload = {
            "type": "fix",
            "title": "Fix to Update",
            "project_id": "test-project",
        }
        res = client.post("/api/v1/issues", json=payload)
        assert res.status_code == 200
        issue_id = res.json()["id"]

        # 2. Update Status to Backlog
        patch_payload = {"status": "backlog", "project_id": "test-project"}
        patch_res = client.patch(f"/api/v1/issues/{issue_id}", json=patch_payload)
        assert patch_res.status_code == 200, patch_res.text
        updated_data = patch_res.json()
        assert updated_data["status"] == "backlog"

        # 3. Verify Persistence (GET)
        get_res = client.get(f"/api/v1/issues/{issue_id}?project_id=test-project")
        assert get_res.json()["status"] == "backlog"


def test_guard_condition_via_api(mock_project_manager):
    """Test that API enforces lifecycle guards"""
    with patch("monoco.daemon.app.project_manager", new=mock_project_manager):
        # 1. Create
        res = client.post(
            "/api/v1/issues",
            json={
                "type": "feature",
                "title": "Guard Test",
                "project_id": "test-project",
            },
        )
        issue_id = res.json()["id"]

        # 2. Move to Doing
        # Note: 'stage' update
        client.patch(
            f"/api/v1/issues/{issue_id}",
            json={"stage": "doing", "project_id": "test-project"},
        )

        # 3. Try to Close (Should Fail)
        patch_res = client.patch(
            f"/api/v1/issues/{issue_id}",
            json={
                "status": "closed",
                "solution": "implemented",
                "project_id": "test-project",
            },
        )
        assert patch_res.status_code == 400
        # The error might be about Review Stage enforcement OR Doing status, depending on solution type.
        # Since we used 'implemented', it catches the Review policy first.
        assert "Lifecycle Policy" in patch_res.json()["detail"]


def test_delete_issue(mock_project_manager):
    """Test deleting an issue via API"""
    with patch("monoco.daemon.app.project_manager", new=mock_project_manager):
        # 1. Create
        payload = {
            "type": "feature",
            "title": "To Delete",
            "project_id": "test-project",
        }
        create_res = client.post("/api/v1/issues", json=payload)
        issue_id = create_res.json()["id"]

        # 2. Delete
        del_res = client.delete(f"/api/v1/issues/{issue_id}?project_id=test-project")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"

        # 3. Verify it's gone
        get_res = client.get(f"/api/v1/issues/{issue_id}?project_id=test-project")
        assert get_res.status_code == 404
