"""
Courier Adapters - Platform-specific message adapters.

Adapters handle communication with external platforms:
- Lark (Feishu)
- Email (IMAP/SMTP)
- Slack
- Discord
- DingTalk (Webhook & Stream)
- etc.
"""

from typing import Dict, Type, Optional
from .base import BaseAdapter, AdapterConfig, SendResult, HealthStatus

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


# Auto-register built-in adapters
def _register_builtin_adapters():
    """Register all built-in adapters."""
    try:
        from .dingtalk_stream import DingTalkStreamAdapter
        register_adapter("dingtalk_stream", DingTalkStreamAdapter)
    except ImportError:
        pass  # Dependencies not available


_register_builtin_adapters()


__all__ = [
    "BaseAdapter",
    "AdapterConfig",
    "SendResult",
    "HealthStatus",
    "register_adapter",
    "get_adapter",
    "list_adapters",
]