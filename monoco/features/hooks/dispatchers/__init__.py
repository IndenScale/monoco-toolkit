"""
Hook Dispatchers for Universal Hooks system.

Provides type-specific dispatchers for Git, IDE, and Agent hooks.
"""

from .git_dispatcher import GitHookDispatcher

__all__ = ["GitHookDispatcher"]
