import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure we can import from monoco
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../vars')))

from monoco.daemon.app import app
from monoco.features.issue.models import IssueType, IssueStatus, IssueStage

client = TestClient(app)

@pytest.fixture
def mock_settings(tmp_path):
    # Setup temporary issues directory
    issues_root = tmp_path / "Issues"
    issues_root.mkdir()
    
    # Initialize standard structure
    for subdir in ["Epics", "Features", "Chores", "Fixes"]:
        (issues_root / subdir).mkdir()
        for status in ["open", "backlog", "closed"]:
            (issues_root / subdir / status).mkdir()

    # Create a mock settings object
    mock_conf = MagicMock()
    # Mocking the nested structure: settings.paths.root
    mock_conf.paths.root = str(tmp_path)
    mock_conf.paths.issues = "Issues"
    return mock_conf

def test_create_issue(mock_settings):
    """Test creating an issue via API"""
    
    with patch("monoco.daemon.app.get_config", return_value=mock_settings):
        payload = {
            "type": "feature",
            "title": "API Test Feature",
            "status": "open"
        }
        response = client.post("/api/v1/issues", json=payload)
        
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["title"] == "API Test Feature"
        assert data["status"] == "open"
        assert data["id"].startswith("FEAT-")

def test_get_issue(mock_settings):
    """Test getting an issue via API"""
    with patch("monoco.daemon.app.get_config", return_value=mock_settings):
        # 1. Create
        payload = {
            "type": "chore",
            "title": "Chore for Get"
        }
        create_res = client.post("/api/v1/issues", json=payload)
        assert create_res.status_code == 200
        issue_id = create_res.json()["id"]
        
        # 2. Get
        get_res = client.get(f"/api/v1/issues/{issue_id}")
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["id"] == issue_id
        assert data["title"] == "Chore for Get"

def test_update_issue(mock_settings):
    """Test updating an issue via API"""
    with patch("monoco.daemon.app.get_config", return_value=mock_settings):
        # 1. Create
        payload = {
            "type": "fix",
            "title": "Fix to Update"
        }
        res = client.post("/api/v1/issues", json=payload)
        assert res.status_code == 200
        issue_id = res.json()["id"]
        
        # 2. Update Status to Backlog
        patch_payload = {
            "status": "backlog"
        }
        patch_res = client.patch(f"/api/v1/issues/{issue_id}", json=patch_payload)
        assert patch_res.status_code == 200, patch_res.text
        updated_data = patch_res.json()
        assert updated_data["status"] == "backlog"
        
        # 3. Verify Persistence (GET)
        get_res = client.get(f"/api/v1/issues/{issue_id}")
        assert get_res.json()["status"] == "backlog"

def test_guard_condition_via_api(mock_settings):
    """Test that API enforces lifecycle guards"""
    with patch("monoco.daemon.app.get_config", return_value=mock_settings):
        # 1. Create
        res = client.post("/api/v1/issues", json={"type": "feature", "title": "Guard Test"})
        issue_id = res.json()["id"]
        
        # 2. Move to Doing
        # Note: 'stage' update
        client.patch(f"/api/v1/issues/{issue_id}", json={"stage": "doing"})
        
        # 3. Try to Close (Should Fail)
        patch_res = client.patch(
            f"/api/v1/issues/{issue_id}", 
            json={"status": "closed", "solution": "implemented"}
        )
        assert patch_res.status_code == 400
        assert "Cannot close issue in progress" in patch_res.json()["detail"]

def test_delete_issue(mock_settings):
    """Test deleting an issue via API"""
    with patch("monoco.daemon.app.get_config", return_value=mock_settings):
        # 1. Create
        payload = {
            "type": "feature",
            "title": "To Delete"
        }
        create_res = client.post("/api/v1/issues", json=payload)
        issue_id = create_res.json()["id"]
        
        # 2. Delete
        del_res = client.delete(f"/api/v1/issues/{issue_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"
        
        # 3. Verify it's gone
        get_res = client.get(f"/api/v1/issues/{issue_id}")
        assert get_res.status_code == 404
