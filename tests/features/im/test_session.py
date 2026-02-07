"""
Tests for IM Agent Session Management (FEAT-0170).
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock

from monoco.features.im.session import (
    SessionState,
    CommandType,
    Command,
    CommandParser,
    StreamChunk,
    SessionContext,
    IMAgentSessionController,
    IMAgentSessionManager,
)
from monoco.features.im.models import (
    IMMessage,
    IMChannel,
    IMParticipant,
    PlatformType,
    MessageContent,
    ContentType,
)


class TestCommandParser:
    """Tests for CommandParser."""
    
    def test_parse_architect_command(self):
        text = "/architect Design a microservice architecture"
        cmd = CommandParser.parse(text)
        
        assert cmd is not None
        assert cmd.command_type == CommandType.ARCHITECT
        assert cmd.prompt == "Design a microservice architecture"
    
    def test_parse_engineer_command_with_issue(self):
        text = "/engineer FEAT-0123"
        cmd = CommandParser.parse(text)
        
        assert cmd is not None
        assert cmd.command_type == CommandType.ENGINEER
        assert cmd.target_id == "FEAT-0123"
    
    def test_parse_status_command(self):
        text = "/status"
        cmd = CommandParser.parse(text)
        
        assert cmd is not None
        assert cmd.command_type == CommandType.STATUS
        assert cmd.args == []
    
    def test_parse_non_command(self):
        text = "Hello, this is just a regular message"
        cmd = CommandParser.parse(text)
        
        assert cmd is None
    
    def test_is_command(self):
        assert CommandParser.is_command("/help") is True
        assert CommandParser.is_command("Hello") is False
        assert CommandParser.is_command("  /status  ") is True
    
    def test_get_available_commands(self):
        commands = CommandParser.get_available_commands()
        
        assert "/architect [prompt]" in commands
        assert "/engineer [issue_id]" in commands
        assert "/status" in commands
        assert "/help" in commands


class TestSessionContext:
    """Tests for SessionContext."""
    
    def test_add_message(self):
        ctx = SessionContext(window_size=3)
        
        # Create mock messages
        for i in range(5):
            msg = Mock(spec=IMMessage)
            msg.message_id = f"msg_{i}"
            msg.content = Mock()
            msg.content.text = f"Message {i}"
            msg.sender = Mock()
            msg.sender.display_name = "User"
            ctx.add_message(msg)
        
        # Should only keep last 3 messages
        assert len(ctx.messages) == 3
        assert ctx.messages[0].message_id == "msg_2"
        assert ctx.messages[2].message_id == "msg_4"
    
    def test_to_prompt(self):
        ctx = SessionContext(window_size=3)
        
        msg1 = Mock(spec=IMMessage)
        msg1.sender = Mock()
        msg1.sender.display_name = "Alice"
        msg1.content = Mock()
        msg1.content.text = "Hello"
        
        msg2 = Mock(spec=IMMessage)
        msg2.sender = Mock()
        msg2.sender.display_name = "Bob"
        msg2.content = Mock()
        msg2.content.text = "Hi there"
        
        ctx.add_message(msg1)
        ctx.add_message(msg2)
        
        prompt = ctx.to_prompt()
        assert "Alice: Hello" in prompt
        assert "Bob: Hi there" in prompt


class TestIMAgentSessionController:
    """Tests for IMAgentSessionController."""
    
    @pytest.fixture
    def mock_deps(self):
        return {
            'message_store': Mock(),
            'channel_manager': Mock(),
        }
    
    @pytest.fixture
    def session(self, mock_deps):
        return IMAgentSessionController(
            session_id="test-session-123",
            channel_id="channel-456",
            agent_role="architect",
            message_store=mock_deps['message_store'],
            channel_manager=mock_deps['channel_manager'],
            context_window=10,
        )
    
    @pytest.mark.asyncio
    async def test_session_initial_state(self, session):
        assert session.state == SessionState.IDLE
        assert session.is_active() is True
        assert session.is_expired() is False
    
    @pytest.mark.asyncio
    async def test_transition_to(self, session):
        await session.transition_to(SessionState.PROCESSING)
        assert session.state == SessionState.PROCESSING
        
        await session.transition_to(SessionState.STREAMING)
        assert session.state == SessionState.STREAMING
    
    @pytest.mark.asyncio
    async def test_complete_session(self, session):
        await session.complete("Task finished successfully")
        
        assert session.state == SessionState.COMPLETED
        assert session.result_summary == "Task finished successfully"
        assert session.completed_at is not None
        assert session.is_active() is False
    
    @pytest.mark.asyncio
    async def test_fail_session(self, session):
        await session.fail("Something went wrong")
        
        assert session.state == SessionState.ERROR
        assert "Failed: Something went wrong" in session.result_summary
        assert session.is_active() is False
    
    @pytest.mark.asyncio
    async def test_stop_session(self, session):
        await session.stop()
        
        assert session.state == SessionState.STOPPED
        assert session.is_active() is False
    
    @pytest.mark.asyncio
    async def test_streaming(self, session):
        # Start streaming
        queue = await session.start_streaming()
        assert session.state == SessionState.STREAMING
        assert queue is not None
        
        # Add stream chunks
        await session.stream_chunk("Hello ")
        await session.stream_chunk("World")
        
        # End streaming
        await session.end_streaming("Done")
        assert session.state == SessionState.COMPLETED
    
    def test_is_expired_with_timeout(self, session):
        # Set last activity to 31 minutes ago
        session.last_activity = datetime.now() - timedelta(minutes=31)
        session.timeout_minutes = 30
        
        assert session.is_expired() is True
    
    def test_is_not_expired(self, session):
        # Set last activity to 10 minutes ago
        session.last_activity = datetime.now() - timedelta(minutes=10)
        session.timeout_minutes = 30
        
        assert session.is_expired() is False


class TestIMAgentSessionManager:
    """Tests for IMAgentSessionManager."""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        return tmp_path / ".monoco" / "im"
    
    @pytest.fixture
    def mock_deps(self, temp_storage):
        return {
            'message_store': Mock(),
            'channel_manager': Mock(),
        }
    
    @pytest.fixture
    async def manager(self, temp_storage, mock_deps):
        mgr = IMAgentSessionManager(
            storage_dir=temp_storage,
            message_store=mock_deps['message_store'],
            channel_manager=mock_deps['channel_manager'],
        )
        await mgr.start()
        yield mgr
        await mgr.stop()
    
    @pytest.mark.asyncio
    async def test_create_session(self, temp_storage, mock_deps):
        manager = IMAgentSessionManager(
            storage_dir=temp_storage,
            message_store=mock_deps['message_store'],
            channel_manager=mock_deps['channel_manager'],
        )
        await manager.start()
        
        session = await manager.create_session(
            channel_id="channel-123",
            agent_role="engineer",
        )
        
        assert session is not None
        assert session.channel_id == "channel-123"
        assert session.agent_role == "engineer"
        assert session.session_id.startswith("im-")
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_get_session(self, temp_storage, mock_deps):
        manager = IMAgentSessionManager(
            storage_dir=temp_storage,
            message_store=mock_deps['message_store'],
            channel_manager=mock_deps['channel_manager'],
        )
        await manager.start()
        
        session = await manager.create_session(
            channel_id="channel-123",
            agent_role="engineer",
        )
        
        retrieved = manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_get_channel_session(self, temp_storage, mock_deps):
        manager = IMAgentSessionManager(
            storage_dir=temp_storage,
            message_store=mock_deps['message_store'],
            channel_manager=mock_deps['channel_manager'],
        )
        await manager.start()
        
        await manager.create_session(
            channel_id="channel-123",
            agent_role="engineer",
        )
        
        session = manager.get_channel_session("channel-123")
        assert session is not None
        assert session.channel_id == "channel-123"
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_end_session(self, temp_storage, mock_deps):
        manager = IMAgentSessionManager(
            storage_dir=temp_storage,
            message_store=mock_deps['message_store'],
            channel_manager=mock_deps['channel_manager'],
        )
        await manager.start()
        
        session = await manager.create_session(
            channel_id="channel-123",
            agent_role="engineer",
        )
        
        result = await manager.end_session(
            session.session_id,
            status="completed",
            summary="Done",
        )
        
        assert result is True
        
        # Session should no longer be active
        assert manager.get_channel_session("channel-123") is None
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_replace_existing_session(self, temp_storage, mock_deps):
        manager = IMAgentSessionManager(
            storage_dir=temp_storage,
            message_store=mock_deps['message_store'],
            channel_manager=mock_deps['channel_manager'],
        )
        await manager.start()
        
        # Create first session
        session1 = await manager.create_session(
            channel_id="channel-123",
            agent_role="engineer",
        )
        
        # Create second session (should replace first)
        session2 = await manager.create_session(
            channel_id="channel-123",
            agent_role="architect",
            replace_existing=True,
        )
        
        # First session should be stopped
        assert session1.state.name in ["STOPPED", "COMPLETED"]
        
        # Second session should be active
        active = manager.get_channel_session("channel-123")
        assert active.session_id == session2.session_id
        
        await manager.stop()


class TestIntegration:
    """Integration tests for IM Agent workflow."""
    
    @pytest.mark.asyncio
    async def test_full_session_lifecycle(self, tmp_path):
        """Test a complete session lifecycle."""
        storage_dir = tmp_path / ".monoco" / "im"
        
        # Create mock dependencies
        message_store = Mock()
        channel_manager = Mock()
        
        # Create manager
        manager = IMAgentSessionManager(
            storage_dir=storage_dir,
            message_store=message_store,
            channel_manager=channel_manager,
        )
        await manager.start()
        
        try:
            # Create session
            session = await manager.create_session(
                channel_id="channel-123",
                agent_role="engineer",
                linked_issue_id="FEAT-0123",
            )
            
            assert session.state.name == "IDLE"
            
            # Add messages
            for i in range(3):
                msg = Mock(spec=IMMessage)
                msg.message_id = f"msg_{i}"
                msg.content = Mock()
                msg.content.text = f"Message {i}"
                msg.sender = Mock()
                msg.sender.display_name = "User"
                await session.add_message(msg)
            
            assert session.message_count == 3
            
            # Transition to processing
            await session.transition_to(SessionState.PROCESSING)
            
            # Complete session
            await session.complete("All tasks finished")
            
            assert session.state.name == "COMPLETED"
            
        finally:
            await manager.stop()
