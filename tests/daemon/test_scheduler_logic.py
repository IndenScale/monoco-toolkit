import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from monoco.daemon.scheduler import SchedulerService
from monoco.daemon.services import ProjectManager
from monoco.features.agent.manager import SessionManager
from monoco.features.issue.models import IssueMetadata

@pytest.fixture
def mock_project_manager():
    pm = MagicMock(spec=ProjectManager)
    pm.projects = {}
    return pm

@pytest.fixture
def scheduler(mock_project_manager):
    return SchedulerService(mock_project_manager)

@pytest.mark.anyio
async def test_check_inbox_trigger_spawns_architect(scheduler):
    # Setup
    project_ctx = MagicMock()
    project_ctx.issues_root = Path("/tmp/issues")
    project_ctx.path = Path("/tmp/project")
    project_ctx.id = "test-project"
    
    # Mock SessionManager
    sm = MagicMock(spec=SessionManager)
    am = MagicMock()
    scheduler.get_managers = MagicMock(return_value=(sm, am))
    
    # Mock existing architects (none)
    sm.list_sessions.return_value = []
    
    # Mock spawn_architect
    scheduler.spawn_architect = MagicMock()
    
    # Mock Policy
    with patch("monoco.daemon.scheduler.MemoAccumulationPolicy") as MockPolicy:
        policy_instance = MockPolicy.return_value
        policy_instance.evaluate.return_value = True
        
        # Execute
        await scheduler.process_project(project_ctx)
        
        # Verify
        scheduler.spawn_architect.assert_called_once_with(sm, project_ctx)

@pytest.mark.anyio
async def test_check_handover_trigger_spawns_engineer(scheduler):
    # Setup
    project_ctx = MagicMock()
    project_ctx.issues_root = Path("/tmp/issues")
    project_ctx.path = Path("/tmp/project")
    
    sm = MagicMock(spec=SessionManager)
    am = MagicMock()
    scheduler.get_managers = MagicMock(return_value=(sm, am))
    
    # Mock list_sessions for Architect check (return generic list so it doesn't spawn architect)
    # But wait, logic is: check existing architects. If I return empty, it tries to spawn architect.
    # I want to test Handover.
    # Let's say we have an architect so it doesn't trigger that part.
    architect_session = MagicMock()
    architect_session.model.role_name = "Architect"
    architect_session.model.status = "running"
    
    # sm.list_sessions is called multiple times.
    # 1. Check existing architects
    # 2. Check active sessions for specific issue
    # 3. Monitor active sessions
    
    # We can use side_effect or just return a list that covers needs if filtered.
    # But list_sessions filtering happens in the code: `[s for s in sm.list_sessions() if ...]`
    # So if I return [architect_session], it satisfies "existing architects".
    
    # For the specific issue check: `[s for s in sm.list_sessions(issue_id=issue.id) if ...]`
    # The code calls sm.list_sessions(issue_id=...) which is a different call signature than sm.list_sessions().
    # I need to mock properly.
    
    def list_sessions_side_effect(issue_id=None):
        if issue_id:
            return [] # No active session for the issue
        return [architect_session] # Architect exists
        
    sm.list_sessions.side_effect = list_sessions_side_effect
    
    scheduler.spawn_engineer = MagicMock()
    
    # Mock list_issues
    issue = MagicMock(spec=IssueMetadata)
    issue.id = "FEAT-123"
    issue.status = "open"
    issue.stage = "doing"
    issue.title = "Test Feature"
    
    with patch("monoco.daemon.scheduler.list_issues", return_value=[issue]):
        await scheduler.process_project(project_ctx)
        
        scheduler.spawn_engineer.assert_called_once_with(sm, issue)

