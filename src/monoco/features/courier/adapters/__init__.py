"""
Courier Adapters - Platform-specific message adapters.

Adapters handle communication with external platforms:
- Lark (Feishu)
- Email (IMAP/SMTP)
- Slack
- Discord
- DingTalk (Webhook & Stream)
- Teams (Microsoft)
- WeCom (WeChat Work)
- etc.
"""

import logging
from typing import Dict, Type, Optional
from monoco.features.connector.protocol.schema import Provider
from .base import BaseAdapter, AdapterConfig, SendResult, HealthStatus

logger = logging.getLogger(__name__)

# Registry of adapters
_registry: Dict[str, Type[BaseAdapter]] = {}


def register_adapter(name: str, adapter_class: Type[BaseAdapter]) -> None:
    """Register an adapter class."""
    _registry[name] = adapter_class


def get_adapter(name: str) -> Optional[Type[BaseAdapter]]:
    """Get an adapter class by name."""
    return _registry.get(name)


def list_adapters() -> list[str]:
    """List all registered adapter names."""
    return list(_registry.keys())


def create_adapter(provider: Provider, config: Optional[AdapterConfig] = None) -> Optional[BaseAdapter]:
    """
    Factory function to create an adapter instance for a provider.
    
    For DingTalk, prefers Stream adapter (Flow mode) if credentials available,
    otherwise falls back to Webhook adapter.
    
    Args:
        provider: The provider type
        config: Optional adapter configuration
        
    Returns:
        Adapter instance or None if not available
    """
    import os
    from .stub import (
        LarkAdapter,
        EmailAdapter,
        SlackAdapter,
        TeamsAdapter,
        WeComAdapter,
    )
    
    config = config or AdapterConfig(provider=provider.value, enabled=True)
    
    # Special handling for DingTalk: prefer Stream mode (Flow)
    if provider == Provider.DINGTALK:
        # First try to get credentials from Channel configuration
        client_id = None
        client_secret = None
        robot_code = None
        
        try:
            from monoco.features.channel.store import get_channel_store
            channel_store = get_channel_store()
            channel = channel_store.get_default_send()
            
            if channel and channel.type.value == "dingtalk":
                # Check if channel has Flow mode credentials
                if hasattr(channel, 'client_id') and channel.client_id:
                    client_id = channel.client_id
                if hasattr(channel, 'client_secret') and channel.client_secret:
                    client_secret = channel.client_secret
                if hasattr(channel, 'robot_code') and channel.robot_code:
                    robot_code = channel.robot_code
                    
                if client_id and client_secret:
                    logger.info(f"Using DingTalk Flow mode credentials from channel: {channel.id}")
        except Exception as e:
            logger.debug(f"Could not load channel config: {e}")
        
        # Fallback to environment variables
        if not client_id:
            client_id = os.environ.get("DINGTALK_CLIENT_ID") or os.environ.get("DINGTALK_APP_KEY")
        if not client_secret:
            client_secret = os.environ.get("DINGTALK_CLIENT_SECRET") or os.environ.get("DINGTALK_APP_SECRET")
        if not robot_code:
            robot_code = os.environ.get("DINGTALK_ROBOT_CODE")
        
        if client_id and client_secret:
            # Use Stream adapter (Flow mode) with OpenAPI
            try:
                from .dingtalk_stream import DingTalkStreamAdapter
                
                # Also get webhook_url for fallback
                webhook_url = None
                try:
                    if channel and hasattr(channel, 'webhook_url'):
                        webhook_url = channel.webhook_url
                except:
                    pass
                
                return DingTalkStreamAdapter(
                    client_id=client_id,
                    client_secret=client_secret,
                    robot_code=robot_code or client_id,  # Fallback to client_id
                    webhook_url=webhook_url,
                )
            except ImportError:
                pass  # Fall through to webhook adapter
        
        # Fall back to Webhook adapter
        try:
            from .dingtalk_outbound import DingTalkOutboundAdapter
            return DingTalkOutboundAdapter(config)
        except ImportError:
            return None
    
    adapter_map = {
        Provider.LARK: LarkAdapter,
        Provider.EMAIL: EmailAdapter,
        Provider.SLACK: SlackAdapter,
        Provider.TEAMS: TeamsAdapter,
        Provider.WECOM: WeComAdapter,
    }
    
    adapter_class = adapter_map.get(provider)
    if adapter_class:
        return adapter_class(config)
    return None


# Auto-register built-in adapters
def _register_builtin_adapters():
    """Register all built-in adapters."""
    try:
        from .dingtalk_stream import DingTalkStreamAdapter
        register_adapter("dingtalk_stream", DingTalkStreamAdapter)
    except ImportError:
        pass  # Dependencies not available
    
    try:
        from .dingtalk_outbound import DingTalkOutboundAdapter
        register_adapter("dingtalk_outbound", DingTalkOutboundAdapter)
    except ImportError:
        pass
    
    try:
        from .stub import (
            LarkAdapter,
            EmailAdapter,
            SlackAdapter,
            TeamsAdapter,
            WeComAdapter,
        )
        register_adapter("lark", LarkAdapter)
        register_adapter("email", EmailAdapter)
        register_adapter("slack", SlackAdapter)
        register_adapter("teams", TeamsAdapter)
        register_adapter("wecom", WeComAdapter)
    except ImportError:
        pass


_register_builtin_adapters()


__all__ = [
    "BaseAdapter",
    "AdapterConfig",
    "SendResult",
    "HealthStatus",
    "create_adapter",
    "register_adapter",
    "get_adapter",
    "list_adapters",
]
