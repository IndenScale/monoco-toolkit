import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

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
    return mock_proj


@pytest.fixture
def mock_project_manager(mock_project):
    mock_pm = MagicMock()
    # Mock get_project to return our mock project
    mock_pm.get_project.return_value = mock_project
    # Mock projects dict for fallback listing
    mock_pm.projects = {"test-project": mock_project}
    return mock_pm


def create_issue_file(root, type_dir, status, filename, content):
    path = root / type_dir / status / filename
    path.write_text(content)
    return path


def test_dashboard_stats(mock_project_manager, mock_project):
    """Test dashboard stats aggregation"""

    with patch("monoco.daemon.app.project_manager", new=mock_project_manager):
        # 1. Backlog Issue
        create_issue_file(
            mock_project.issues_root,
            "Features",
            "backlog",
            "FEAT-001.md",
            """---
id: FEAT-001
type: feature
status: backlog
title: Backlog Feature
created_at: '2023-01-01T00:00:00'
---
""",
        )

        # 2. Completed This Week
        now = datetime.now()
        this_week_date = (now - timedelta(days=1)).isoformat()
        create_issue_file(
            mock_project.issues_root,
            "Fixes",
            "closed",
            "FIX-001.md",
            f"""---
id: FIX-001
type: fix
status: closed
title: Fixed This Week
created_at: '2023-01-01T00:00:00'
closed_at: '{this_week_date}'
---
""",
        )

        # 3. Completed Last Week
        last_week_date = (now - timedelta(days=10)).isoformat()
        create_issue_file(
            mock_project.issues_root,
            "Fixes",
            "closed",
            "FIX-002.md",
            f"""---
id: FIX-002
type: fix
status: closed
title: Fixed Last Week
created_at: '2023-01-01T00:00:00'
closed_at: '{last_week_date}'
---
""",
        )

        # 4. Blocked Issue (Open, depends on non-closed)
        # Dependency (Open)
        create_issue_file(
            mock_project.issues_root,
            "Features",
            "open",
            "FEAT-002.md",
            """---
id: FEAT-002
type: feature
status: open
title: Blocking Feature
created_at: '2023-01-01T00:00:00'
---
""",
        )
        # Blocked Issue
        create_issue_file(
            mock_project.issues_root,
            "Features",
            "open",
            "FEAT-003.md",
            """---
id: FEAT-003
type: feature
status: open
title: Blocked Feature
dependencies: ['FEAT-002']
created_at: '2023-01-01T00:00:00'
---
""",
        )

        # 5. Non-blocked Open Issue
        create_issue_file(
            mock_project.issues_root,
            "Features",
            "open",
            "FEAT-004.md",
            """---
id: FEAT-004
type: feature
status: open
title: Normal Feature
created_at: '2023-01-01T00:00:00'
---
""",
        )

        # Call API
        response = client.get("/api/v1/stats/dashboard?project_id=test-project")
        assert response.status_code == 200
        stats = response.json()

        # Check values
        assert stats["total_backlog"] == 1
        assert stats["completed_this_week"] == 1
        assert stats["blocked_issues_count"] == 1

        # Velocity Trend: This Week (1) - Last Week (1) = 0
        assert stats["velocity_trend"] == 0

        # Check Activities
        activities = stats.get("recent_activities", [])
        # FIX-001 closed recently -> should have a closed activity
        closed_activities = [
            a
            for a in activities
            if a["type"] == "closed" and a["issue_id"] == "FIX-001"
        ]
        assert len(closed_activities) == 1
