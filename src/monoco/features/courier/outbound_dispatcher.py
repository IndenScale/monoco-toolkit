"""
Outbound Dispatcher - Routes outbound messages to appropriate adapters.

Manages adapter instances and dispatches messages based on provider type.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Type

from monoco.features.connector.protocol.schema import Provider, OutboundMessage, Content
from .adapters.base import BaseAdapter, AdapterConfig, SendResult

logger = logging.getLogger("courier.outbound_dispatcher")


class OutboundDispatcher:
    """
    Dispatches outbound messages to the appropriate adapter.

    Responsibilities:
    - Maintain adapter instances for each provider
    - Route messages to the correct adapter based on provider
    - Handle adapter lifecycle (connect/disconnect)
    - Collect and report adapter health status
    """

    def __init__(self):
        """Initialize the dispatcher with empty adapter registry."""
        self._adapters: Dict[Provider, BaseAdapter] = {}
        self._adapter_classes: Dict[Provider, Type[BaseAdapter]] = {}
        self._adapter_configs: Dict[Provider, AdapterConfig] = {}
        self._lock = asyncio.Lock()

    def register_adapter(
        self,
        provider: Provider,
        adapter_class: Type[BaseAdapter],
        config: Optional[AdapterConfig] = None,
    ) -> None:
        """
        Register an adapter class for a provider.

        Args:
            provider: The provider type (dingtalk, lark, etc.)
            adapter_class: The adapter class to instantiate
            config: Optional configuration for the adapter
        """
        self._adapter_classes[provider] = adapter_class
        self._adapter_configs[provider] = config or AdapterConfig(
            provider=provider.value,
            enabled=True,
        )
        logger.info(f"Registered adapter for {provider.value}: {adapter_class.__name__}")
    
    def register_adapter_instance(
        self,
        provider: Provider,
        adapter: BaseAdapter,
    ) -> None:
        """
        Register a pre-configured adapter instance for a provider.
        
        This is useful when the adapter requires custom initialization
        that cannot be done through the standard config-based approach.

        Args:
            provider: The provider type (dingtalk, lark, etc.)
            adapter: The pre-configured adapter instance
        """
        self._adapters[provider] = adapter
        self._adapter_classes[provider] = type(adapter)
        logger.info(f"Registered adapter instance for {provider.value}: {type(adapter).__name__}")

    async def _get_adapter(self, provider: Provider) -> Optional[BaseAdapter]:
        """
        Get or create an adapter instance for the provider.

        Args:
            provider: The provider type

        Returns:
            Adapter instance or None if not registered
        """
        if provider not in self._adapters:
            async with self._lock:
                if provider not in self._adapters:
                    if provider not in self._adapter_classes:
                        logger.warning(f"No adapter registered for {provider.value}")
                        return None

                    config = self._adapter_configs.get(provider)
                    adapter_class = self._adapter_classes[provider]

                    try:
                        adapter = adapter_class(config)
                        await adapter.connect()
                        self._adapters[provider] = adapter
                        logger.info(f"Initialized adapter for {provider.value}")
                    except Exception as e:
                        logger.error(f"Failed to initialize adapter for {provider.value}: {e}")
                        return None

        return self._adapters.get(provider)

    async def dispatch(self, message: OutboundMessage) -> SendResult:
        """
        Dispatch a message to the appropriate adapter.

        Args:
            message: The outbound message to send

        Returns:
            SendResult with success/failure information
        """
        provider = message.provider
        adapter = await self._get_adapter(provider)

        if not adapter:
            return SendResult(
                success=False,
                error=f"No adapter available for provider: {provider.value}",
                timestamp=datetime.utcnow(),
            )

        try:
            result = await adapter.send(message)
            return result
        except Exception as e:
            logger.exception(f"Error dispatching message to {provider.value}: {e}")
            return SendResult(
                success=False,
                error=f"Dispatch error: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def health_check(self, provider: Optional[Provider] = None) -> Dict[str, any]:
        """
        Check health of adapters.

        Args:
            provider: Optional specific provider to check

        Returns:
            Dict with health status for each adapter
        """
        results = {}

        providers = [provider] if provider else list(self._adapters.keys())

        for p in providers:
            adapter = self._adapters.get(p)
            if adapter:
                try:
                    status = await adapter.health_check()
                    results[p.value] = {
                        "status": status.value,
                        "connected": adapter.is_connected(),
                    }
                except Exception as e:
                    results[p.value] = {
                        "status": "error",
                        "error": str(e),
                    }
            else:
                results[p.value] = {
                    "status": "not_initialized",
                }

        return results

    async def shutdown(self) -> None:
        """Shutdown all adapters."""
        for provider, adapter in self._adapters.items():
            try:
                await adapter.disconnect()
                logger.info(f"Disconnected adapter for {provider.value}")
            except Exception as e:
                logger.error(f"Error disconnecting adapter for {provider.value}: {e}")

        self._adapters.clear()

    def get_registered_providers(self) -> List[str]:
        """Get list of registered provider names."""
        return [p.value for p in self._adapter_classes.keys()]

    def is_provider_available(self, provider: Provider) -> bool:
        """Check if a provider has a registered adapter."""
        return provider in self._adapter_classes
