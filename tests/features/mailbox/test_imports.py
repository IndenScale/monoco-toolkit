"""
Import tests for Mailbox components (FEAT-0199).

This module tests that all new components can be imported correctly.
These are basic sanity tests to ensure the module structure is valid.
"""

import pytest


def test_import_mailbox_watcher():
    """Test that MailboxWatcher components can be imported."""
    from monoco.features.mailbox.watcher import (
        MailboxFileEvent,
        MailboxInboundWatcher,
        MailboxWatcher,
    )

    # Verify imports succeeded
    assert MailboxFileEvent is not None
    assert MailboxWatcher is not None
    assert MailboxInboundWatcher is not None


def test_import_mailbox_handler():
    """Test that MailboxAgentHandler components can be imported."""
    from monoco.features.mailbox.handler import (
        MailboxAgentHandler,
        MessageContext,
        MessageRouter,
        RoutingRule,
        SessionManager,
    )

    # Verify imports succeeded
    assert MailboxAgentHandler is not None
    assert MessageRouter is not None
    assert SessionManager is not None
    assert RoutingRule is not None
    assert MessageContext is not None


def test_import_agent_config():
    """Test that updated agent configuration can be imported."""
    from monoco.features.agent.defaults import DEFAULT_ROLES, ROLE_ALIASES

    # Verify imports succeeded
    assert DEFAULT_ROLES is not None
    assert ROLE_ALIASES is not None

    # Verify Prime Agent is configured
    prime_roles = [role for role in DEFAULT_ROLES if role.name == "Prime"]
    assert len(prime_roles) > 0, "Prime Agent should be in DEFAULT_ROLES"

    # Verify role aliases are configured
    assert len(ROLE_ALIASES) > 0, "ROLE_ALIASES should not be empty"


def test_import_courier_daemon():
    """Test that CourierDaemon can be imported."""
    from monoco.features.courier.daemon import CourierDaemon

    # Verify import succeeded
    assert CourierDaemon is not None


def test_mailbox_file_event_creation():
    """Test creating a MailboxFileEvent instance."""
    from pathlib import Path

    from monoco.features.mailbox.watcher import MailboxFileEvent

    event = MailboxFileEvent(
        path=Path("/test/file.md"),
        change_type="created",
        watcher_name="test_watcher",
        provider="dingtalk",
        session_id="session_123",
        message_id="msg_456",
    )

    assert event.provider == "dingtalk"
    assert event.session_id == "session_123"
    assert event.message_id == "msg_456"
    assert event.change_type == "created"


def test_routing_rule_creation():
    """Test creating a RoutingRule instance."""
    from monoco.features.mailbox.handler import RoutingRule

    rule = RoutingRule(
        name="test_rule",
        condition="keyword",
        pattern="test",
        agent_role="prime",
        priority=50,
    )

    assert rule.name == "test_rule"
    assert rule.condition == "keyword"
    assert rule.pattern == "test"
    assert rule.agent_role == "prime"
    assert rule.priority == 50
    assert rule.enabled is True


def test_message_context_creation():
    """Test creating a MessageContext instance."""
    from datetime import datetime
    from pathlib import Path

    from monoco.features.mailbox.handler import MessageContext

    context = MessageContext(
        message_id="test_001",
        provider="dingtalk",
        session_id="chat_123",
        sender="Test User",
        content="Test message",
        raw_content="Test message",
        mentions=["@Prime"],
        attachments=[],
        metadata={},
        file_path=Path("/test.md"),
        received_at=datetime.now(),
    )

    assert context.message_id == "test_001"
    assert context.provider == "dingtalk"
    assert context.session_id == "chat_123"
    assert context.sender == "Test User"
    assert context.content == "Test message"
    assert "@Prime" in context.mentions


@pytest.mark.asyncio
async def test_session_manager_async():
    """Test SessionManager async operations."""
    from monoco.features.mailbox.handler import SessionManager

    session_manager = SessionManager(session_ttl=60)

    # Test creating a session
    session = await session_manager.get_or_create_session("test_session", "dingtalk")

    assert session["id"] == "test_session"
    assert session["provider"] == "dingtalk"
    assert session["message_count"] == 1

    # Test updating context
    await session_manager.update_session_context(
        "test_session", {"test_key": "test_value"}
    )

    # Test adding agent task
    await session_manager.add_agent_task("test_session", "task_001")

    # Get session again to verify updates
    session = await session_manager.get_or_create_session("test_session", "dingtalk")
    assert session["context"]["test_key"] == "test_value"
    assert "task_001" in session["agent_tasks"]


def test_message_router_basic():
    """Test basic MessageRouter functionality."""
    from datetime import datetime
    from pathlib import Path

    from monoco.features.mailbox.handler import MessageContext, MessageRouter

    router = MessageRouter()

    # Test with a command message
    context = MessageContext(
        message_id="test_cmd_001",
        provider="dingtalk",
        session_id="chat_cmd",
        sender="Test User",
        content="/help I need assistance",
        raw_content="/help I need assistance",
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


def test_component_integration():
    """Test that components work together."""
    # Create a mailbox event
    from pathlib import Path

    from monoco.core.scheduler import AgentEventType
    from monoco.features.mailbox.handler import MessageRouter
    from monoco.features.mailbox.watcher import ChangeType, MailboxFileEvent

    event = MailboxFileEvent(
        path=Path("/test/file.md"),
        change_type=ChangeType.CREATED,
        watcher_name="test_watcher",
        provider="dingtalk",
    )

    # Test event type conversion
    event_type = event.to_agent_event_type()
    assert event_type == AgentEventType.MAILBOX_INBOUND_RECEIVED

    # Test router initialization
    router = MessageRouter()
    assert len(router.rules) > 0

    # Verify fallback rule exists
    fallback_rules = [rule for rule in router.rules if rule.name == "fallback"]
    assert len(fallback_rules) == 1
    assert fallback_rules[0].agent_role == "prime"


def test_agent_role_configuration():
    """Test that agent roles are properly configured."""
    from monoco.features.agent.defaults import DEFAULT_ROLES

    # Check for required roles
    role_names = [role.name for role in DEFAULT_ROLES]

    assert "Prime" in role_names, "Prime Agent should be configured"
    assert "Helper" in role_names, "Helper Agent should be configured"
    assert "Drafter" in role_names, "Drafter Agent should be configured"
    assert "Debugger" in role_names, "Debugger Agent should be configured"

    # Check Prime Agent configuration
    prime_role = next(role for role in DEFAULT_ROLES if role.name == "Prime")
    assert "mailbox.agent.trigger" in prime_role.trigger
    assert "Primary agent" in prime_role.description
    assert prime_role.engine == "gemini"
