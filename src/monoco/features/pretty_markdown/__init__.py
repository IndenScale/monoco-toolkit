"""
Pretty Markdown - Markdown formatting and linting utilities for Monoco.

This module provides:
- Configuration template management for prettier and markdownlint
- Automatic formatting hooks for Markdown files
- Configuration synchronization between projects
"""

from .core import (
    sync_config,
    check_config,
    enable_hook,
    disable_hook,
    get_template_path,
)

__all__ = [
    "sync_config",
    "check_config",
    "enable_hook",
    "disable_hook",
    "get_template_path",
]
