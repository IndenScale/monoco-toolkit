"""
Unit tests for LocalProcessScheduler.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from monoco.core.scheduler import (
    LocalProcessScheduler,
    AgentTask,
    AgentStatus,
)


class TestLocalProcessScheduler:
    """Test suite for LocalProcessScheduler."""

    @pytest.fixture
    def scheduler(self, tmp_path):
        """Create a scheduler instance for testing."""
        return LocalProcessScheduler(
            max_concurrent=3,
            project_root=tmp_path,
        )

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return AgentTask(
            task_id="test-task-123",
            role_name="TestRole",
            issue_id="FEAT-123",
            prompt="Test prompt",
            engine="gemini",
            timeout=60,
        )

    def test_scheduler_initialization(self, scheduler):
        """Scheduler should initialize with correct attributes."""
        assert scheduler.max_concurrent == 3
        assert scheduler._running is False
        assert len(scheduler._sessions) == 0

    @pytest.mark.asyncio
    async def test_start_stop(self, scheduler):
        """Scheduler should start and stop correctly."""
        await scheduler.start()
        assert scheduler._running is True
        assert scheduler._monitor_task is not None
        
        await scheduler.stop()
        assert scheduler._running is False

    def test_get_stats_empty(self, scheduler):
        """Stats should reflect empty state."""
        stats = scheduler.get_stats()
        
        assert stats["running"] is False
        assert stats["max_concurrent"] == 3
        assert stats["active_sessions"] == 0
        assert stats["total_sessions"] == 0
        assert stats["available_slots"] == 3

    @pytest.mark.asyncio
    async def test_get_status_nonexistent(self, scheduler):
        """get_status should return None for non-existent session."""
        status = scheduler.get_status("non-existent-id")
        assert status is None

    @pytest.mark.asyncio
    async def test_terminate_nonexistent(self, scheduler):
        """terminate should return False for non-existent session."""
        result = await scheduler.terminate("non-existent-id")
        assert result is False


class TestLocalProcessSchedulerMocked:
    """Test suite with mocked subprocess."""

    @pytest.fixture
    def scheduler(self, tmp_path):
        return LocalProcessScheduler(
            max_concurrent=2,
            project_root=tmp_path,
        )

    @pytest.fixture
    def sample_task(self):
        return AgentTask(
            task_id="test-task-123",
            role_name="Engineer",
            issue_id="FEAT-123",
            prompt="Implement feature",
            engine="gemini",
            timeout=60,
        )

    @pytest.mark.asyncio
    async def test_schedule_creates_session(self, scheduler, sample_task):
        """schedule should create a new session."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Still running
        
        with patch('subprocess.Popen', return_value=mock_process):
            await scheduler.start()
            session_id = await scheduler.schedule(sample_task)
            
            assert session_id is not None
            assert session_id in scheduler._sessions
            assert scheduler._sessions[session_id]["status"] == AgentStatus.RUNNING
            
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_list_active(self, scheduler, sample_task):
        """list_active should return only active sessions."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        
        with patch('subprocess.Popen', return_value=mock_process):
            await scheduler.start()
            session_id = await scheduler.schedule(sample_task)
            
            active = scheduler.list_active()
            assert session_id in active
            assert active[session_id] == AgentStatus.RUNNING
            
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_terminate_running_session(self, scheduler, sample_task):
        """terminate should stop a running session."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_process.wait.return_value = 0
        
        with patch('subprocess.Popen', return_value=mock_process):
            await scheduler.start()
            session_id = await scheduler.schedule(sample_task)
            
            result = await scheduler.terminate(session_id)
            
            assert result is True
            mock_process.terminate.assert_called_once()
            
            await scheduler.stop()


class TestLocalProcessSchedulerConcurrency:
    """Test suite for concurrency control."""

    @pytest.fixture
    def scheduler(self, tmp_path):
        return LocalProcessScheduler(
            max_concurrent=2,  # Limit to 2 concurrent
            project_root=tmp_path,
        )

    def test_concurrency_config(self, scheduler):
        """Scheduler should store concurrency configuration."""
        assert scheduler.max_concurrent == 2
        # Semaphore should be initialized
        assert scheduler._semaphore._value == 2


class TestLocalProcessSchedulerMonitoring:
    """Test suite for session monitoring."""

    @pytest.fixture
    def scheduler(self, tmp_path):
        return LocalProcessScheduler(
            max_concurrent=2,
            project_root=tmp_path,
        )

    @pytest.fixture
    def sample_task(self):
        return AgentTask(
            task_id="test-task",
            role_name="Engineer",
            issue_id="FEAT-123",
            prompt="Test",
            engine="gemini",
            timeout=60,
        )

    @pytest.mark.asyncio
    async def test_handle_completion_updates_status(self, scheduler, sample_task):
        """_handle_completion should update session status."""
        mock_process = Mock()
        mock_process.pid = 12345
        
        with patch('subprocess.Popen', return_value=mock_process):
            await scheduler.start()
            session_id = await scheduler.schedule(sample_task)
            
            # Manually trigger completion handling
            session = scheduler._sessions[session_id]
            await scheduler._handle_completion(session_id, session)
            
            # Status should be updated
            status = scheduler.get_status(session_id)
            assert status == AgentStatus.COMPLETED
            
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_handle_failure_updates_status(self, scheduler, sample_task):
        """_handle_failure should update session status."""
        mock_process = Mock()
        mock_process.pid = 12345
        
        with patch('subprocess.Popen', return_value=mock_process):
            await scheduler.start()
            session_id = await scheduler.schedule(sample_task)
            
            # Manually trigger failure handling
            session = scheduler._sessions[session_id]
            await scheduler._handle_failure(session_id, session, returncode=1)
            
            # Status should be updated
            status = scheduler.get_status(session_id)
            assert status == AgentStatus.FAILED
            
            await scheduler.stop()
