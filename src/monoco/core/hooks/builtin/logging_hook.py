"""
LoggingHook - Logs session lifecycle events.

Simple hook that logs when sessions start and end for auditing/debugging.
"""

import logging
from datetime import datetime
from typing import Optional

from ..base import SessionLifecycleHook, HookResult
from ..context import HookContext

logger = logging.getLogger("monoco.core.hooks.logging")


class LoggingHook(SessionLifecycleHook):
    """
    Hook for logging session lifecycle events.
    
    Configuration options:
        - log_level: The logging level to use (default: INFO)
        - log_start: Whether to log session start (default: True)
        - log_end: Whether to log session end (default: True)
    """

    def __init__(self, name: Optional[str] = None, config: Optional[dict] = None):
        super().__init__(name=name or "logging", config=config)
        
        self.log_level = self._parse_log_level(self.config.get("log_level", "INFO"))
        self.log_start = self.config.get("log_start", True)
        self.log_end = self.config.get("log_end", True)

    def _parse_log_level(self, level: str) -> int:
        """Parse log level string to logging constant."""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return levels.get(level.upper(), logging.INFO)

    def on_session_start(self, context: HookContext) -> HookResult:
        """Log session start."""
        if not self.log_start:
            return HookResult.skipped("Session start logging disabled")
        
        issue_info = f" for issue {context.issue.id}" if context.issue else ""
        log_message = (
            f"Session {context.session_id} started{issue_info} "
            f"(role: {context.role_name})"
        )
        
        logger.log(self.log_level, log_message)
        
        return HookResult.success(f"Logged session start: {context.session_id}")

    def on_session_end(self, context: HookContext) -> HookResult:
        """Log session end with duration."""
        if not self.log_end:
            return HookResult.skipped("Session end logging disabled")
        
        duration = datetime.now() - context.created_at
        duration_seconds = duration.total_seconds()
        
        issue_info = f" for issue {context.issue.id}" if context.issue else ""
        log_message = (
            f"Session {context.session_id} ended{issue_info} "
            f"(duration: {duration_seconds:.2f}s, status: {context.session_status})"
        )
        
        logger.log(self.log_level, log_message)
        
        return HookResult.success(
            f"Logged session end: {context.session_id} (duration: {duration_seconds:.2f}s)"
        )
