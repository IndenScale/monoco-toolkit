"""
Integration tests for Worker with multi-engine support.
"""

import pytest
from unittest.mock import patch, MagicMock
from monoco.features.agent.worker import Worker
from monoco.features.agent.models import RoleTemplate


class TestWorkerEngineIntegration:
    """Test Worker integration with the engine adapter system."""

    @pytest.fixture
    def gemini_role(self):
        """Create a role template using Gemini engine."""
        return RoleTemplate(
            name="test-drafter",
            description="A test drafter role for unit testing",
            trigger="issue.created",
            engine="gemini",
            system_prompt="You are a test drafter",
            goal="Create test issues",
        )

    @pytest.fixture
    def claude_role(self):
        """Create a role template using Claude engine."""
        return RoleTemplate(
            name="test-reviewer",
            description="A test code reviewer role",
            trigger="pull_request.opened",
            engine="claude",
            system_prompt="You are a code reviewer",
            goal="Review code quality",
        )

    @patch("subprocess.Popen")
    def test_worker_uses_gemini_adapter(self, mock_popen, gemini_role):
        """Worker should use GeminiAdapter for gemini engine."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        worker = Worker(role=gemini_role, issue_id="FEAT-0001")
        worker.start()

        # Verify Popen was called with correct Gemini command
        call_args = mock_popen.call_args[0][0]
        assert call_args[0] == "gemini"
        assert call_args[1] == "-p"
        assert "test drafter" in call_args[2]

    @patch("subprocess.Popen")
    def test_worker_uses_claude_adapter(self, mock_popen, claude_role):
        """Worker should use ClaudeAdapter for claude engine."""
        mock_process = MagicMock()
        mock_process.pid = 12346
        mock_popen.return_value = mock_process

        worker = Worker(role=claude_role, issue_id="FEAT-0002")
        worker.start()

        # Verify Popen was called with correct Claude command
        call_args = mock_popen.call_args[0][0]
        assert call_args[0] == "claude"
        assert call_args[1] == "-p"
        assert "code reviewer" in call_args[2]

    def test_worker_raises_on_unsupported_engine(self):
        """Worker should raise RuntimeError for unsupported engines."""
        unsupported_role = RoleTemplate(
            name="test-agent",
            description="Test agent with unsupported engine",
            trigger="test.event",
            engine="gpt4",  # Not supported
            system_prompt="Test",
            goal="Test",
        )

        worker = Worker(role=unsupported_role, issue_id="FEAT-0003")

        with pytest.raises(RuntimeError) as exc_info:
            worker.start()

        assert "Unsupported engine" in str(exc_info.value)
        assert "gpt4" in str(exc_info.value)

    @patch("subprocess.Popen")
    def test_worker_handles_missing_engine_binary(self, mock_popen, gemini_role):
        """Worker should raise RuntimeError when engine binary is not found."""
        mock_popen.side_effect = FileNotFoundError("gemini not found")

        worker = Worker(role=gemini_role, issue_id="FEAT-0004")

        with pytest.raises(RuntimeError) as exc_info:
            worker.start()

        assert "not found" in str(exc_info.value)
        assert "gemini" in str(exc_info.value)
        assert "PATH" in str(exc_info.value)

    @patch("subprocess.Popen")
    def test_worker_with_draft_context_gemini(self, mock_popen, gemini_role):
        """Worker should handle draft context correctly with Gemini."""
        mock_process = MagicMock()
        mock_process.pid = 12347
        mock_popen.return_value = mock_process

        # Use drafter role name to trigger draft mode
        drafter_role = RoleTemplate(
            name="drafter",
            description="Issue drafter agent",
            trigger="draft.requested",
            engine="gemini",
            system_prompt="You are a drafter",
            goal="Draft issues",
        )

        worker = Worker(role=drafter_role, issue_id="FEAT-0005")
        context = {"type": "feature", "description": "Add new API endpoint"}
        worker.start(context=context)

        # Verify the prompt includes draft-specific instructions
        call_args = mock_popen.call_args[0][0]
        prompt = call_args[2]
        assert "Drafter" in prompt
        assert "feature" in prompt
        assert "Add new API endpoint" in prompt
        assert "monoco issue create" in prompt

    @patch("subprocess.Popen")
    def test_worker_with_draft_context_claude(self, mock_popen):
        """Worker should handle draft context correctly with Claude."""
        mock_process = MagicMock()
        mock_process.pid = 12348
        mock_popen.return_value = mock_process

        drafter_role = RoleTemplate(
            name="drafter",
            description="Issue drafter agent",
            trigger="draft.requested",
            engine="claude",
            system_prompt="You are a drafter",
            goal="Draft issues",
        )

        worker = Worker(role=drafter_role, issue_id="FEAT-0006")
        context = {"type": "chore", "description": "Update dependencies"}
        worker.start(context=context)

        # Verify Claude command is used with draft prompt
        call_args = mock_popen.call_args[0][0]
        assert call_args[0] == "claude"
        assert call_args[1] == "-p"
        prompt = call_args[2]
        assert "chore" in prompt
        assert "Update dependencies" in prompt
