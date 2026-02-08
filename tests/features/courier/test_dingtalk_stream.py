
import pytest
import asyncio
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime

# Mock dingtalk_stream if not installed
try:
    from dingtalk_stream.frames import CallbackMessage, AckMessage
except ImportError:
    # Create mocks
    mock_module = MagicMock()
    sys.modules["dingtalk_stream"] = mock_module
    sys.modules["dingtalk_stream.frames"] = mock_module
    
    class AckMessage:
        STATUS_OK = 200
        
    class CallbackMessage:
        pass

from monoco.features.courier.adapters.dingtalk_stream import DingTalkStreamAdapter
from monoco.features.connector.protocol.schema import SessionType, ContentType, InboundMessage

class MockHeaders:
    def __init__(self, topic="/v1.0/im/bot/messages/get", message_id="msg_123"):
        self.topic = topic
        self.message_id = message_id

class MockCallbackMessage:
    def __init__(self, data, topic="/v1.0/im/bot/messages/get"):
        self.data = data
        self.headers = MockHeaders(topic=topic)

    def to_dict(self):
        return self.data

@pytest.fixture
def adapter():
    return DingTalkStreamAdapter(
        app_key="test_app_key",
        app_secret="test_app_secret",
        default_project="test_project"
    )

def test_dingtalk_stream_parsing_text(adapter):
    """Test parsing of a standard DingTalk text message via Stream."""
    raw_payload = {
        "msgtype": "text",
        "senderStaffId": "staff_001",
        "senderNick": "Alice",
        "conversationId": "conv_001",
        "chatType": "2",  # Group
        "text": {"content": "Ping Monoco"},
        "msgId": "ding_msg_001"
    }
    mock_msg = MockCallbackMessage(raw_payload)
    
    inbound = adapter._parse_message(mock_msg)
    
    assert inbound is not None
    assert inbound.id == "dingtalk_ding_msg_001"
    assert inbound.content.text == "Ping Monoco"
    assert inbound.session.type == SessionType.GROUP
    assert inbound.participants["from"]["name"] == "Alice"

def test_dingtalk_stream_parsing_markdown(adapter):
    """Test parsing of a DingTalk markdown message."""
    raw_payload = {
        "msgtype": "markdown",
        "senderStaffId": "staff_002",
        "senderNick": "Bob",
        "conversationId": "conv_002",
        "chatType": "1",  # Direct
        "markdown": {"text": "### Monoco\\nUpdate available"},
        "msgId": "ding_msg_002"
    }
    mock_msg = MockCallbackMessage(raw_payload)
    
    inbound = adapter._parse_message(mock_msg)
    
    assert inbound is not None
    assert inbound.type == ContentType.MARKDOWN
    assert inbound.content.markdown == "### Monoco\\nUpdate available"
    assert inbound.session.type == SessionType.DIRECT

def test_dingtalk_stream_handler_callback(adapter):
    """Test that the internal handler correctly invokes the message handler."""
    message_received = []
    
    def mock_handler(msg, project):
        message_received.append((msg, project))
        
    adapter.set_message_handler(mock_handler)
    
    # We need to test the MonocoChatbotHandler.process which is inside run_sync
    # Since it's nested, we'll simulate the same logic
    raw_payload = {
        "msgtype": "text",
        "senderStaffId": "staff_001",
        "text": {"content": "Hello"},
        "msgId": "id_1"
    }
    mock_msg = MockCallbackMessage(raw_payload)
    
    # Simulate what happens inside the handler's process method
    inbound_msg = adapter._parse_message(mock_msg)
    if inbound_msg:
        adapter._message_handler(inbound_msg, "test_project")
        
    assert len(message_received) == 1
    assert message_received[0][0].content.text == "Hello"
    assert message_received[0][1] == "test_project"

def test_dingtalk_stream_parsing_error_robustness(adapter):
    """Test that parsing handles malformed or minimal data gracefully."""
    # Empty data
    mock_msg = MockCallbackMessage({})
    inbound = adapter._parse_message(mock_msg)
    
    assert inbound is not None
    assert inbound.participants["from"]["id"] == "unknown"
    assert inbound.session.id == "unknown"

@pytest.mark.asyncio
async def test_adapter_lifecycle(adapter):
    """Test basic lifecycle methods."""
    # connect() initializes HTTP client for sending messages
    await adapter.connect()

    assert adapter._connected is True

    status = await adapter.health_check()
    assert status.value == "connected"

    await adapter.disconnect()
    assert adapter._connected is False
