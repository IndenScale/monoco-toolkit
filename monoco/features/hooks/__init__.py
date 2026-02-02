"""
Git Hooks management feature for Monoco.

Provides distributed hooks architecture where each Feature can contribute
its own hooks in resources/hooks/, aggregated by this feature.
"""

from .core import GitHooksManager, HookDeclaration, HookType
from .adapter import HooksFeature

__all__ = ["GitHooksManager", "HookDeclaration", "HookType", "HooksFeature"]
