import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from monoco.daemon.scheduler import SchedulerService
from monoco.daemon.services import ProjectManager
from monoco.features.issue.models import IssueMetadata
from monoco.core.scheduler import AgentEventType

@pytest.fixture
def mock_project_manager():
    pm = MagicMock(spec=ProjectManager)
    pm.projects = {}
    return pm

@pytest.fixture
def scheduler(mock_project_manager):
    return SchedulerService(mock_project_manager)

@pytest.mark.anyio
async def test_memo_threshold_emits_event(scheduler, mock_project_manager):
    """Test that crossing the memo threshold emits a MEMO_THRESHOLD event."""
    # Setup project context
    project_ctx = MagicMock()
    project_ctx.id = "test-project"
    project_ctx.issues_root = Path("/tmp/issues")
    mock_project_manager.projects = {"test-project": project_ctx}
    
    # Mock load_memos to return 6 pending memos (threshold is 5)
    mock_memo = MagicMock()
    mock_memo.status = "pending"
    
    with patch("monoco.daemon.scheduler.load_memos", return_value=[mock_memo] * 6), \
         patch("monoco.daemon.scheduler.event_bus.publish", new_callable=AsyncMock) as mock_publish:
        
        # Execute check
        await scheduler._check_memo_thresholds()
        
        # Verify event published
        mock_publish.assert_called_once()
        args, kwargs = mock_publish.call_args
        assert args[0] == AgentEventType.MEMO_THRESHOLD
        assert args[1]["project_id"] == "test-project"
        assert args[1]["memo_count"] == 6

@pytest.mark.anyio
async def test_issue_stage_change_emits_event(scheduler, mock_project_manager):
    """Test that issue stage changes emit ISSUE_STAGE_CHANGED events."""
    project_ctx = MagicMock()
    project_ctx.id = "test-project"
    project_ctx.issues_root = Path("/tmp/issues")
    mock_project_manager.projects = {"test-project": project_ctx}
    
    # Initial state: stage is None
    issue = MagicMock(spec=IssueMetadata)
    issue.id = "FEAT-123"
    issue.status = "open"
    issue.stage = "doing"
    issue.title = "Test Issue"
    
    with patch("monoco.daemon.scheduler.list_issues", return_value=[issue]), \
         patch("monoco.daemon.scheduler.event_bus.publish", new_callable=AsyncMock) as mock_publish:
        
        # Establishing state - first check will emit event for new issue discovered
        await scheduler._check_issue_changes()
        assert mock_publish.call_count == 2  # One for stage change (None->doing), one for status change (None->open)
        mock_publish.reset_mock()
        
        # Change stage
        issue.stage = "review"
        await scheduler._check_issue_changes()
        
        # Verify event
        mock_publish.assert_called_once()
        args, kwargs = mock_publish.call_args
        assert args[0] == AgentEventType.ISSUE_STAGE_CHANGED
        assert args[1]["issue_id"] == "FEAT-123"
        assert args[1]["old_stage"] == "doing"
        assert args[1]["new_stage"] == "review"

@pytest.mark.anyio
async def test_session_completion_emits_event(scheduler):
    """Test that session completion emits SESSION_COMPLETED event."""
    sm = MagicMock()
    scheduler.session_managers = {"proj1": sm}
    
    session = MagicMock()
    session.model.id = "sess-1"
    session.model.issue_id = "FEAT-123"
    session.model.role_name = "Engineer"
    session.model.status = "completed"
    
    # Mock refresh_status to return "completed" while model.status was "running"
    session.refresh_status.return_value = "completed"
    session.model.status = "running"
    
    sm.list_sessions.return_value = [session]
    
    with patch("monoco.daemon.scheduler.event_bus.publish", new_callable=AsyncMock) as mock_publish:
        await scheduler._monitor_sessions()
        
        mock_publish.assert_called_once_with(
            AgentEventType.SESSION_COMPLETED,
            {
                "session_id": "sess-1",
                "issue_id": "FEAT-123",
                "role_name": "Engineer",
            },
            source="scheduler.session_monitor"
        )
