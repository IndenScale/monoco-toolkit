"""
Unit tests for SemaphoreManager - concurrency control to prevent fork bomb.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from monoco.daemon.services import SemaphoreManager


class TestSemaphoreManager:
    """Test suite for SemaphoreManager."""

    def test_default_limits(self):
        """Test that default conservative limits are applied."""
        manager = SemaphoreManager()
        
        status = manager.get_status()
        assert status["global"]["limit"] == 3
        assert status["roles"]["Engineer"]["limit"] == 1
        assert status["roles"]["Architect"]["limit"] == 1
        assert status["roles"]["Reviewer"]["limit"] == 1

    def test_custom_config(self):
        """Test that custom config overrides defaults."""
        config = MagicMock()
        config.global_max = 5
        config.engineer = 2
        config.architect = 1
        config.reviewer = 2
        config.failure_cooldown_seconds = 120
        
        manager = SemaphoreManager(config)
        
        status = manager.get_status()
        assert status["global"]["limit"] == 5
        assert status["roles"]["Engineer"]["limit"] == 2
        assert status["roles"]["Reviewer"]["limit"] == 2

    def test_acquire_and_release(self):
        """Test basic acquire and release functionality."""
        manager = SemaphoreManager()
        
        # Acquire first slot
        assert manager.can_acquire("Engineer") is True
        assert manager.acquire("session-1", "Engineer") is True
        
        status = manager.get_status()
        assert status["global"]["active"] == 1
        assert status["roles"]["Engineer"]["active"] == 1
        
        # Release slot
        manager.release("session-1")
        
        status = manager.get_status()
        assert status["global"]["active"] == 0
        assert status["roles"]["Engineer"]["active"] == 0

    def test_role_limit_enforcement(self):
        """Test that role-specific limits are enforced."""
        config = MagicMock()
        config.global_max = 10
        config.engineer = 2
        config.architect = 1
        config.reviewer = 1
        config.failure_cooldown_seconds = 60
        
        manager = SemaphoreManager(config)
        
        # Acquire up to limit
        assert manager.can_acquire("Engineer") is True
        assert manager.acquire("eng-1", "Engineer") is True
        
        assert manager.can_acquire("Engineer") is True
        assert manager.acquire("eng-2", "Engineer") is True
        
        # Should not be able to acquire more
        assert manager.can_acquire("Engineer") is False
        
        # But other roles should still work
        assert manager.can_acquire("Architect") is True

    def test_global_limit_enforcement(self):
        """Test that global limit is enforced across all roles."""
        config = MagicMock()
        config.global_max = 3
        config.engineer = 5  # High role limit
        config.architect = 5
        config.reviewer = 5
        config.failure_cooldown_seconds = 60
        
        manager = SemaphoreManager(config)
        
        # Acquire up to global limit with different roles
        assert manager.acquire("eng-1", "Engineer") is True
        assert manager.acquire("arch-1", "Architect") is True
        assert manager.acquire("rev-1", "Reviewer") is True
        
        # Global limit reached
        assert manager.can_acquire("Engineer") is False
        assert manager.can_acquire("Architect") is False
        
        status = manager.get_status()
        assert status["global"]["active"] == 3

    def test_failure_cooldown(self):
        """Test that failure cooldown prevents immediate retry."""
        config = MagicMock()
        config.global_max = 5
        config.engineer = 2
        config.architect = 1
        config.reviewer = 1
        config.failure_cooldown_seconds = 60
        
        manager = SemaphoreManager(config)
        
        # Record a failure
        manager.record_failure("ISSUE-123", "session-1")
        
        # Should not be able to acquire for this issue during cooldown
        assert manager.can_acquire("Engineer", issue_id="ISSUE-123") is False
        
        # But other issues should work
        assert manager.can_acquire("Engineer", issue_id="ISSUE-456") is True

    def test_failure_cooldown_expiration(self):
        """Test that cooldown expires after configured time."""
        config = MagicMock()
        config.global_max = 5
        config.engineer = 2
        config.architect = 1
        config.reviewer = 1
        config.failure_cooldown_seconds = 60
        
        manager = SemaphoreManager(config)
        
        # Record a failure with timestamp in the past
        with patch.object(manager, '_failure_registry', {
            "ISSUE-123": datetime.now() - timedelta(seconds=61)
        }):
            # Cooldown should have expired
            assert manager.can_acquire("Engineer", issue_id="ISSUE-123") is True

    def test_clear_failure(self):
        """Test that clearing failure removes cooldown."""
        config = MagicMock()
        config.global_max = 5
        config.engineer = 2
        config.architect = 1
        config.reviewer = 1
        config.failure_cooldown_seconds = 60
        
        manager = SemaphoreManager(config)
        
        # Record a failure
        manager.record_failure("ISSUE-123")
        assert manager.can_acquire("Engineer", issue_id="ISSUE-123") is False
        
        # Clear the failure
        manager.clear_failure("ISSUE-123")
        assert manager.can_acquire("Engineer", issue_id="ISSUE-123") is True

    def test_release_nonexistent_session(self):
        """Test that releasing a non-existent session is handled gracefully."""
        manager = SemaphoreManager()
        
        # Should not raise
        manager.release("nonexistent-session")
        
        status = manager.get_status()
        assert status["global"]["active"] == 0

    def test_duplicate_acquire(self):
        """Test that acquiring same session twice is handled gracefully."""
        manager = SemaphoreManager()
        
        assert manager.acquire("session-1", "Engineer") is True
        # Second acquire should still return True (idempotent)
        assert manager.acquire("session-1", "Engineer") is True
        
        status = manager.get_status()
        # Should only count once
        assert status["global"]["active"] == 1

    def test_record_failure_releases_slot(self):
        """Test that recording failure also releases the slot."""
        config = MagicMock()
        config.global_max = 5
        config.engineer = 2
        config.architect = 1
        config.reviewer = 1
        config.failure_cooldown_seconds = 60
        
        manager = SemaphoreManager(config)
        
        # Acquire a slot
        manager.acquire("session-1", "Engineer")
        assert manager.get_status()["global"]["active"] == 1
        
        # Record failure with session_id
        manager.record_failure("ISSUE-123", "session-1")
        
        # Slot should be released
        assert manager.get_status()["global"]["active"] == 0
        # Failure should be recorded
        assert manager.can_acquire("Engineer", issue_id="ISSUE-123") is False


class TestSemaphoreManagerIntegration:
    """Integration tests simulating real-world scenarios."""

    def test_prevent_fork_bomb_scenario(self):
        """
        Simulate the fork bomb scenario:
        - Agent fails repeatedly
        - Without semaphore: infinite spawn loop
        - With semaphore: limited spawns and cooldown enforced
        """
        config = MagicMock()
        config.global_max = 3
        config.engineer = 1  # Only 1 engineer allowed
        config.architect = 1
        config.reviewer = 1
        config.failure_cooldown_seconds = 60
        
        manager = SemaphoreManager(config)
        
        issue_id = "ISSUE-FORK-BOMB"
        
        # First spawn attempt
        assert manager.can_acquire("Engineer", issue_id=issue_id) is True
        manager.acquire("session-1", "Engineer")
        
        # Simulate failure
        manager.record_failure(issue_id, "session-1")
        
        # Next tick tries to spawn again
        # Should be blocked by cooldown
        assert manager.can_acquire("Engineer", issue_id=issue_id) is False
        
        # Even if we try multiple times (simulating multiple ticks)
        for _ in range(10):
            assert manager.can_acquire("Engineer", issue_id=issue_id) is False

    def test_mixed_role_scenario(self):
        """
        Test scenario with multiple roles running concurrently.
        """
        config = MagicMock()
        config.global_max = 5
        config.engineer = 2
        config.architect = 1
        config.reviewer = 2
        config.failure_cooldown_seconds = 60
        
        manager = SemaphoreManager(config)
        
        # Spawn 2 Engineers (at limit)
        assert manager.can_acquire("Engineer") is True
        manager.acquire("eng-1", "Engineer")
        assert manager.can_acquire("Engineer") is True
        manager.acquire("eng-2", "Engineer")
        
        # 3rd Engineer should be blocked
        assert manager.can_acquire("Engineer") is False
        
        # But we can still spawn other roles
        assert manager.can_acquire("Architect") is True
        manager.acquire("arch-1", "Architect")
        
        assert manager.can_acquire("Reviewer") is True
        manager.acquire("rev-1", "Reviewer")
        
        # Global limit now at 4/5
        status = manager.get_status()
        assert status["global"]["active"] == 4
        
        # Global limit reached
        assert manager.acquire("rev-2", "Reviewer") is True
        assert manager.can_acquire("Engineer") is False
        assert manager.can_acquire("Reviewer") is False

    def test_graceful_degradation(self):
        """
        Test that system degrades gracefully when limits are reached.
        """
        config = MagicMock()
        config.global_max = 2
        config.engineer = 5  # High role limits
        config.architect = 5
        config.reviewer = 5
        config.failure_cooldown_seconds = 60
        
        manager = SemaphoreManager(config)
        
        # Fill up all slots
        manager.acquire("session-1", "Engineer")
        manager.acquire("session-2", "Architect")
        
        # All subsequent attempts should gracefully fail
        assert manager.can_acquire("Engineer") is False
        assert manager.can_acquire("Reviewer") is False
        
        # Status should still be available
        status = manager.get_status()
        assert status["global"]["active"] == 2
        assert status["global"]["limit"] == 2
