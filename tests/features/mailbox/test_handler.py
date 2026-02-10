"""
Tests for MailboxAgentHandler functionality (FEAT-0199).
"""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from monoco.core.scheduler import AgentEvent, AgentEventType, AgentTask
from monoco.features.mailbox.handler import (
    MailboxAgentHandler,
    MessageContext,
    MessageRouter,
    RoutingRule,
    SessionManager,
)


class TestMessageRouter:
    """Tests for MessageRouter class."""

    def test_initialization(self):
        """Test router initialization with default rules."""
        router = MessageRouter()
        assert len(router.rules) > 0
        # Should have at least the fallback rule
        assert any(rule.name == "fallback" for rule in router.rules)

    def test_add_rule(self):
        """Test adding custom routing rules."""
        router = MessageRouter()
        initial_count = len(router.rules)

        new_rule = RoutingRule(
            name="custom_rule",
            condition="keyword",
            pattern="urgent",
            agent_role="prime",
            priority=80,
        )
        router.add_rule(new_rule)

        assert len(router.rules) == initial_count + 1
        assert router.rules[0].priority >= new_rule.priority  # Sorted by priority

    def test_route_message_command(self):
        """Test routing based on command patterns."""
        router = MessageRouter()

        # Test /help command
        context = MessageContext(
            message_id="test_001",
            provider="dingtalk",
            session_id="chat_123",
            sender="test_user",
            content="/help with something",
            raw_content="/help with something",
            mentions=[],
            attachments=[],
            metadata={},
            file_path=Path("/test.md"),
            received_at=datetime.now(),
        )

        agent_role, metadata = router.route_message(context)
        assert agent_role == "helper"
        assert metadata["rule"] == "help_command"
        assert metadata["command"] == "/help"

    def test_route_message_mention(self):
        """Test routing based on mentions."""
        router = MessageRouter()

        # Test @Prime mention
        context = MessageContext(
            message_id="test_002",
            provider="dingtalk",
            session_id="chat_123",
            sender="test_user",
            content="Hey @Prime, can you help?",
            raw_content="Hey @Prime, can you help?",
            mentions=["@Prime"],
            attachments=[],
            metadata={},
            file_path=Path("/test.md"),
            received_at=datetime.now(),
        )

        agent_role, metadata = router.route_message(context)
        assert agent_role == "prime"
        assert metadata["rule"] == "prime_mention"

    def test_route_message_keyword(self):
        """Test routing based on keywords."""
        router = MessageRouter()

        # Test bug keyword
        context = MessageContext(
            message_id="test_003",
            provider="dingtalk",
            session_id="chat_123",
            sender="test_user",
            content="Found a bug in the system",
            raw_content="Found a bug in the system",
            mentions=[],
            attachments=[],
            metadata={},
            file_path=Path("/test.md"),
            received_at=datetime.now(),
        )

        agent_role, metadata = router.route_message(context)
        assert agent_role == "debugger"
        assert metadata["rule"] == "bug_keyword"

    def test_route_message_fallback(self):
        """Test fallback routing when no other rules match."""
        router = MessageRouter()

        # Test generic message (no commands, mentions, or keywords)
        context = MessageContext(
            message_id="test_004",
            provider="dingtalk",
            session_id="chat_123",
            sender="test_user",
            content="Hello, how are you?",
            raw_content="Hello, how are you?",
            mentions=[],
            attachments=[],
            metadata={},
            file_path=Path("/test.md"),
            received_at=datetime.now(),
        )

        agent_role, metadata = router.route_message(context)
        assert agent_role == "prime"  # Should use fallback rule
        assert metadata["rule"] == "fallback"

    def test_route_message_priority(self):
        """Test that higher priority rules are checked first."""
        router = MessageRouter()

        # Clear default rules and add test rules
        router.rules = []

        # Add low priority rule
        router.add_rule(
            RoutingRule(
                name="low_priority",
                condition="keyword",
                pattern="test",
                agent_role="helper",
                priority=10,
            )
        )

        # Add high priority rule that also matches
        router.add_rule(
            RoutingRule(
                name="high_priority",
                condition="always",
                pattern="",
                agent_role="prime",
                priority=100,
            )
        )

        context = MessageContext(
            message_id="test_005",
            provider="dingtalk",
            session_id="chat_123",
            sender="test_user",
            content="test message",
            raw_content="test message",
            mentions=[],
            attachments=[],
            metadata={},
            file_path=Path("/test.md"),
            received_at=datetime.now(),
        )

        agent_role, metadata = router.route_message(context)
        # Should use high priority rule even though low priority also matches
        assert agent_role == "prime"
        assert metadata["rule"] == "high_priority"


class TestSessionManager:
    """Tests for SessionManager class."""

    @pytest.fixture
    def session_manager(self):
        """Create SessionManager instance."""
        return SessionManager(session_ttl=60)  # 60 seconds TTL for tests

    @pytest.mark.asyncio
    async def test_get_or_create_session(self, session_manager):
        """Test getting or creating a session."""
        session_id = "test_session_123"
        provider = "dingtalk"

        # Get new session
        session = await session_manager.get_or_create_session(session_id, provider)

        assert session["id"] == session_id
        assert session["provider"] == provider
        assert session["message_count"] == 1
        assert "created_at" in session
        assert "last_activity" in session

        # Get existing session (should increment message count)
        session2 = await session_manager.get_or_create_session(session_id, provider)
        assert session2["message_count"] == 2

    @pytest.mark.asyncio
    async def test_update_session_context(self, session_manager):
        """Test updating session context."""
        session_id = "test_session_456"
        provider = "email"

        # Create session first
        await session_manager.get_or_create_session(session_id, provider)

        # Update context
        context_updates = {"last_topic": "bug report", "priority": "high"}
        await session_manager.update_session_context(session_id, context_updates)

        # Get session and check updates
        session = await session_manager.get_or_create_session(session_id, provider)
        assert session["context"]["last_topic"] == "bug report"
        assert session["context"]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_add_agent_task(self, session_manager):
        """Test adding agent task to session."""
        session_id = "test_session_789"
        provider = "slack"
        task_id = "agent_task_001"

        # Create session first
        await session_manager.get_or_create_session(session_id, provider)

        # Add agent task
        await session_manager.add_agent_task(session_id, task_id)

        # Get session and check task was added
        session = await session_manager.get_or_create_session(session_id, provider)
        assert task_id in session["agent_tasks"]

        # Add same task again (should not duplicate)
        await session_manager.add_agent_task(session_id, task_id)
        session = await session_manager.get_or_create_session(session_id, provider)
        assert len(session["agent_tasks"]) == 1  # Still only one entry

    def test_session_expiration(self, session_manager):
        """Test session expiration cleanup."""
        # Manually add an expired session
        expired_session_id = "expired_session"
        session_manager.sessions[expired_session_id] = {
            "id": expired_session_id,
            "provider": "test",
            "created_at": datetime.now(),
            "last_activity": datetime.fromtimestamp(0),  # Very old
            "message_count": 1,
            "agent_tasks": [],
            "context": {},
        }

        # Add a non-expired session
        active_session_id = "active_session"
        session_manager.sessions[active_session_id] = {
            "id": active_session_id,
            "provider": "test",
            "created_at": datetime.now(),
            "last_activity": datetime.now(),  # Recent
            "message_count": 1,
            "agent_tasks": [],
            "context": {},
        }

        # Trigger cleanup
        session_manager._cleanup_sessions()

        # Expired session should be removed
        assert expired_session_id not in session_manager.sessions
        # Active session should remain
        assert active_session_id in session_manager.sessions

    def test_get_session_stats(self, session_manager):
        """Test getting session statistics."""
        # Add some sessions
        session_manager.sessions = {
            "session1": {
                "id": "session1",
                "provider": "test",
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "message_count": 1,
                "agent_tasks": [],
                "context": {},
            },
            "session2": {
                "id": "session2",
                "provider": "test",
                "created_at": datetime.now(),
                "last_activity": datetime.fromtimestamp(0),  # Expired
                "message_count": 1,
                "agent_tasks": [],
                "context": {},
            },
        }

        stats = session_manager.get_session_stats()
        assert stats["total_sessions"] == 2
        assert stats["active_sessions"] == 1  # Only one active


class TestMailboxAgentHandler:
    """Tests for MailboxAgentHandler class."""

    @pytest.fixture
    def temp_mailbox_root(self):
        """Create temporary mailbox root directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mailbox_root = Path(tmpdir)
            # Create standard mailbox structure
            (mailbox_root / "inbound").mkdir(parents=True)
            (mailbox_root / "outbound").mkdir()
            (mailbox_root / "archive").mkdir()
            yield mailbox_root

    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus."""
        event_bus = AsyncMock()
        event_bus.publish = AsyncMock()
        return event_bus

    @pytest.fixture
    def mock_agent_scheduler(self):
        """Create mock agent scheduler."""
        scheduler = AsyncMock()
        scheduler.schedule = AsyncMock(return_value="scheduled_task_001")
        return scheduler

    @pytest.fixture
    def handler(self, temp_mailbox_root, mock_event_bus, mock_agent_scheduler):
        """Create MailboxAgentHandler instance."""
        return MailboxAgentHandler(
            event_bus=mock_event_bus,
            agent_scheduler=mock_agent_scheduler,
            mailbox_root=temp_mailbox_root,
            debounce_window=0.1,  # Short window for tests
        )

    @pytest.mark.asyncio
    async def test_initialization(self, handler):
        """Test handler initialization."""
        assert handler.mailbox_root is not None
        assert handler.debounce_window == 0.1
        assert handler.router is not None
        assert handler.session_manager is not None

    @pytest.mark.asyncio
    async def test_handle_inbound_event(self, handler, temp_mailbox_root):
        """Test handling inbound mailbox event."""
        # Create a test message file
        inbound_dir = temp_mailbox_root / "inbound" / "dingtalk"
        inbound_dir.mkdir(parents=True, exist_ok=True)

        test_file = inbound_dir / "test_message.md"
        test_content = """---
id: dingtalk_msg_001
provider: dingtalk
session:
  id: chat_888
participants:
  sender:
    name: Test User
type: text
---
Hello, this is a test message!
"""
        test_file.write_text(test_content)

        # Create mock event
        event = AgentEvent(
            type=AgentEventType.MAILBOX_INBOUND_RECEIVED,
            payload={
                "path": str(test_file),
                "change_type": "created",
                "provider": "dingtalk",
                "session_id": "chat_888",
                "message_id": "dingtalk_msg_001",
            },
            source="test",
            timestamp=datetime.now(),
        )

        # Handle the event
        await handler.handle_inbound(event)

        # Should have buffered the message
        assert len(handler._message_buffers) > 0

    @pytest.mark.asyncio
    async def test_handle_trigger_event(
        self, handler, temp_mailbox_root, mock_agent_scheduler
    ):
        """Test handling manual trigger event."""
        # Create a test message file
        inbound_dir = temp_mailbox_root / "inbound" / "dingtalk"
        inbound_dir.mkdir(parents=True, exist_ok=True)

        test_file = inbound_dir / "trigger_test.md"
        test_content = """---
id: trigger_msg_001
provider: dingtalk
session:
  id: chat_999
participants:
  sender:
    name: Trigger User
type: text
---
Please trigger an agent!
"""
        test_file.write_text(test_content)

        # Create trigger event
        event = AgentEvent(
            type=AgentEventType.MAILBOX_AGENT_TRIGGER,
            payload={
                "message_id": "trigger_msg_001",
            },
            source="test",
            timestamp=datetime.now(),
        )

        # Handle the event
        await handler.handle_trigger(event)

        # Should have triggered agent scheduling
        assert mock_agent_scheduler.schedule.called

    @pytest.mark.asyncio
    async def test_message_buffering_and_debouncing(self, handler):
        """Test message buffering with debounce window."""
        # Create multiple message contexts for the same session
        session_id = "test_session_123"
        messages = []

        for i in range(3):
            context = MessageContext(
                message_id=f"msg_{i:03d}",
                provider="dingtalk",
                session_id=session_id,
                sender=f"user_{i}",
                content=f"Message {i}",
                raw_content=f"Message {i}",
                mentions=[],
                attachments=[],
                metadata={},
                file_path=Path(f"/test_{i}.md"),
                received_at=datetime.now(),
            )
            messages.append(context)

        # Buffer all messages
        for context in messages:
            await handler._buffer_message(context)

        # Should have created a buffer for this session
        assert session_id in handler._message_buffers
        assert len(handler._message_buffers[session_id]) == 3

        # Wait for debounce window to expire
        await asyncio.sleep(0.2)

        # Buffer should be cleared after processing
        assert session_id not in handler._message_buffers

    @pytest.mark.asyncio
    async def test_process_messages_batch(self, handler, mock_agent_scheduler):
        """Test processing a batch of messages."""
        # Create multiple message contexts
        messages = []
        for i in range(2):
            context = MessageContext(
                message_id=f"batch_msg_{i:03d}",
                provider="dingtalk",
                session_id="batch_session",
                sender=f"user_{i}",
                content=f"Batch message {i}",
                raw_content=f"Batch message {i}",
                mentions=[],
                attachments=[],
                metadata={},
                file_path=Path(f"/batch_{i}.md"),
                received_at=datetime.now(),
            )
            messages.append(context)

        # Process the batch
        await handler._process_messages(messages)

        # Should have scheduled an agent
        assert mock_agent_scheduler.schedule.called

        # Check the scheduled task
        scheduled_task = mock_agent_scheduler.schedule.call_args[0][0]
        assert isinstance(scheduled_task, AgentTask)
        assert "batch" in scheduled_task.task_id
        assert scheduled_task.role_name == "prime"  # Default for generic messages

    @pytest.mark.asyncio
    async def test_build_agent_prompt(self, handler):
        """Test building agent prompt from message context."""
        context = MessageContext(
            message_id="prompt_test_001",
            provider="dingtalk",
            session_id="prompt_session",
            sender="Test User",
            content="How do I create an issue?",
            raw_content="How do I create an issue?",
            mentions=["@Prime"],
            attachments=[{"name": "log.txt", "type": "file"}],
            metadata={"priority": "normal"},
            file_path=Path("/prompt_test.md"),
            received_at=datetime.now(),
        )

        prompt = handler._build_agent_prompt("prime", context)

        # Check that prompt contains relevant information
        assert "Prime Agent" in prompt
        assert "Test User" in prompt
        assert "dingtalk" in prompt
        assert "prompt_session" in prompt
        assert "How do I create an issue?" in prompt
        assert "@Prime" in prompt
        assert "1 files attached" in prompt

    @pytest.mark.asyncio
    async def test_trigger_agent(self, handler, mock_agent_scheduler, mock_event_bus):
        """Test triggering an agent with message context."""
        context = MessageContext(
            message_id="trigger_test_001",
            provider="dingtalk",
            session_id="trigger_session",
            sender="Agent Requester",
            content="Please analyze this bug report",
            raw_content="Please analyze this bug report",
            mentions=[],
            attachments=[],
            metadata={},
            file_path=Path("/trigger_test.md"),
            received_at=datetime.now(),
        )

        # Trigger agent
        task_id = await handler._trigger_agent("debugger", context, "trigger_session")

        assert task_id == "scheduled_task_001"
        assert mock_agent_scheduler.schedule.called

        # Check the scheduled task
        scheduled_task = mock_agent_scheduler.schedule.call_args[0][0]
        assert scheduled_task.task_id == "mailbox_trigger_test_001"
