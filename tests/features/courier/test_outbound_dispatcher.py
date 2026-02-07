"""
Tests for OutboundDispatcher - message routing to adapters.
"""

import asyncio
import pytest
from datetime import datetime

from monoco.features.connector.protocol.schema import (
    OutboundMessage,
    Content,
    Provider,
    ContentType,
)
from monoco.features.courier.outbound_dispatcher import OutboundDispatcher
from monoco.features.courier.adapters.base import BaseAdapter, AdapterConfig, SendResult, HealthStatus


class MockAdapter(BaseAdapter):
    """Mock adapter for testing."""
    
    def __init__(self, config: AdapterConfig, should_succeed: bool = True):
        super().__init__(config)
        self.should_succeed = should_succeed
        self.sent_messages = []
        self._connected = False
    
    @property
    def provider(self) -> str:
        return "mock"
    
    async def connect(self) -> None:
        self._connected = True
    
    async def disconnect(self) -> None:
        self._connected = False
    
    async def send(self, message: OutboundMessage) -> SendResult:
        self.sent_messages.append(message)
        if self.should_succeed:
            return SendResult(
                success=True,
                provider_message_id="mock_123",
                timestamp=datetime.utcnow(),
            )
        else:
            return SendResult(
                success=False,
                error="Mock failure",
                timestamp=datetime.utcnow(),
            )
    
    async def health_check(self) -> HealthStatus:
        return HealthStatus.CONNECTED if self._connected else HealthStatus.DISCONNECTED
    
    async def listen(self):
        pass


@pytest.fixture
def dispatcher():
    """Create an OutboundDispatcher instance."""
    return OutboundDispatcher()


@pytest.fixture
def sample_message():
    """Create a sample outbound message."""
    return OutboundMessage(
        to="test_user",
        provider=Provider.DINGTALK,
        type=ContentType.TEXT,
        content=Content(text="Hello, World!"),
    )


class TestOutboundDispatcher:
    """Tests for OutboundDispatcher class."""

    def test_register_adapter(self, dispatcher):
        """Test registering an adapter."""
        config = AdapterConfig(provider="mock")
        
        dispatcher.register_adapter(Provider.DINGTALK, MockAdapter, config)
        
        assert Provider.DINGTALK in dispatcher._adapter_classes
        assert dispatcher.is_provider_available(Provider.DINGTALK)

    def test_get_registered_providers(self, dispatcher):
        """Test getting list of registered providers."""
        dispatcher.register_adapter(Provider.DINGTALK, MockAdapter)
        dispatcher.register_adapter(Provider.LARK, MockAdapter)
        
        providers = dispatcher.get_registered_providers()
        
        assert "dingtalk" in providers
        assert "lark" in providers

    @pytest.mark.asyncio
    async def test_dispatch_success(self, dispatcher, sample_message):
        """Test successful message dispatch."""
        dispatcher.register_adapter(Provider.DINGTALK, MockAdapter)
        
        result = await dispatcher.dispatch(sample_message)
        
        assert result.success is True
        assert result.provider_message_id == "mock_123"

    @pytest.mark.asyncio
    async def test_dispatch_failure(self, dispatcher, sample_message):
        """Test failed message dispatch."""
        config = AdapterConfig(provider="mock")
        dispatcher.register_adapter(Provider.DINGTALK, MockAdapter, config)
        
        # Replace with failing adapter
        adapter = MockAdapter(config, should_succeed=False)
        dispatcher._adapters[Provider.DINGTALK] = adapter
        await adapter.connect()
        
        result = await dispatcher.dispatch(sample_message)
        
        assert result.success is False
        assert "Mock failure" in result.error

    @pytest.mark.asyncio
    async def test_dispatch_no_adapter(self, dispatcher, sample_message):
        """Test dispatch when no adapter is registered."""
        result = await dispatcher.dispatch(sample_message)
        
        assert result.success is False
        assert "No adapter available" in result.error

    @pytest.mark.asyncio
    async def test_health_check(self, dispatcher):
        """Test health check functionality."""
        dispatcher.register_adapter(Provider.DINGTALK, MockAdapter)
        
        # Check before connect - adapter not initialized yet
        health = await dispatcher.health_check(Provider.DINGTALK)
        assert health["dingtalk"]["status"] == "not_initialized"
        
        # Dispatch to trigger connect
        message = OutboundMessage(
            to="test",
            provider=Provider.DINGTALK,
            type=ContentType.TEXT,
            content=Content(text="test"),
        )
        await dispatcher.dispatch(message)
        
        # Check after connect
        health = await dispatcher.health_check(Provider.DINGTALK)
        assert health["dingtalk"]["status"] == "connected"

    @pytest.mark.asyncio
    async def test_shutdown(self, dispatcher):
        """Test shutting down all adapters."""
        dispatcher.register_adapter(Provider.DINGTALK, MockAdapter)
        
        # Create and connect adapter
        message = OutboundMessage(
            to="test",
            provider=Provider.DINGTALK,
            type=ContentType.TEXT,
            content=Content(text="test"),
        )
        await dispatcher.dispatch(message)
        
        adapter = dispatcher._adapters[Provider.DINGTALK]
        assert adapter.is_connected()
        
        # Shutdown
        await dispatcher.shutdown()
        
        assert not adapter.is_connected()
        assert len(dispatcher._adapters) == 0

    @pytest.mark.asyncio
    async def test_adapter_lifecycle(self, dispatcher):
        """Test adapter is created and connected on first use."""
        dispatcher.register_adapter(Provider.DINGTALK, MockAdapter)
        
        # No adapter initially
        assert Provider.DINGTALK not in dispatcher._adapters
        
        # Dispatch creates and connects adapter
        message = OutboundMessage(
            to="test",
            provider=Provider.DINGTALK,
            type=ContentType.TEXT,
            content=Content(text="test"),
        )
        await dispatcher.dispatch(message)
        
        # Adapter now exists and is connected
        assert Provider.DINGTALK in dispatcher._adapters
        assert dispatcher._adapters[Provider.DINGTALK].is_connected()
