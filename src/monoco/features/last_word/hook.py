"""
Last-Word: Session Lifecycle Hook Integration.

This module provides the SessionLifecycleHook implementation for last-word,
enabling automatic processing at session start and end.
"""

import logging
from typing import Optional

from monoco.core.hooks.base import SessionLifecycleHook, HookResult
from monoco.core.hooks.context import HookContext

from .core import (
    init_session,
    process_session_end,
    ensure_directories,
    get_session_id,
)
from .config import get_effective_config, load_config

logger = logging.getLogger("monoco.features.last_word")


class LastWordHook(SessionLifecycleHook):
    """
    Session lifecycle hook for last-word knowledge delta protocol.
    
    This hook:
    1. Initializes the last-word session on session start
    2. Processes pending updates on session end
    
    Configuration options:
        - enabled: Whether the hook is enabled (default: True)
        - auto_apply: Whether to auto-apply updates on session end (default: False)
        - max_retries: Max retries for file writes (default: 3)
        - load_knowledge: Whether to load knowledge bases into context (default: True)
    """
    
    def __init__(self, name: Optional[str] = None, config: Optional[dict] = None):
        super().__init__(name=name or "last_word", config=config)
        
        self.auto_apply = self.config.get("auto_apply", False)
        self.max_retries = self.config.get("max_retries", 3)
        self.load_knowledge = self.config.get("load_knowledge", True)
        
        # Ensure directories exist
        ensure_directories()
    
    def on_session_start(self, context: HookContext) -> HookResult:
        """
        Initialize last-word session.
        
        - Sets up session buffer
        - Loads knowledge base configuration
        - Optionally injects knowledge into system prompt
        """
        if not self.enabled:
            return HookResult.skipped("Last-word hook disabled")
        
        try:
            # Initialize session
            session_id = init_session(context.session_id)
            
            # Load configuration
            config = get_effective_config(context.workspace_root)
            
            details = {
                "session_id": session_id,
                "knowledge_bases": config.session_bootstrap,
            }
            
            # Load knowledge into context if enabled
            if self.load_knowledge and context.system_prompt is not None:
                knowledge = self._load_knowledge_context(config)
                if knowledge:
                    context.system_prompt += f"\n\n{knowledge}"
                    details["knowledge_loaded"] = True
            
            logger.debug(f"Last-word session initialized: {session_id}")
            
            return HookResult.success(
                f"Last-word session initialized: {session_id}",
                details=details
            )
        
        except Exception as e:
            logger.error(f"Failed to initialize last-word session: {e}")
            return HookResult.failure(
                f"Failed to initialize last-word session: {e}",
                details={"error": str(e)}
            )
    
    def on_session_end(self, context: HookContext) -> HookResult:
        """
        Process last-word updates at session end.
        
        - Validates pending entries
        - Writes to YAML files or staging
        - Optionally auto-applies updates
        """
        if not self.enabled:
            return HookResult.skipped("Last-word hook disabled")
        
        try:
            # Process session buffer
            result = process_session_end(max_retries=self.max_retries)
            
            details = {
                "status": result.get("status"),
                "written": result.get("written", []),
                "staged": result.get("staged_files", []),
            }
            
            # Auto-apply if enabled and there are written files
            if self.auto_apply and result.get("written"):
                from .core import apply_yaml_to_markdown
                
                applied = []
                failed = []
                
                for yaml_path_str in result["written"]:
                    yaml_path = __import__('pathlib').Path(yaml_path_str)
                    apply_results = apply_yaml_to_markdown(yaml_path, dry_run=False)
                    
                    if all(r.success for r in apply_results):
                        yaml_path.unlink()  # Remove after successful apply
                        applied.append(yaml_path_str)
                    else:
                        failed.append(yaml_path_str)
                
                details["auto_applied"] = applied
                details["auto_apply_failed"] = failed
            
            message = f"Last-word processing complete: {result.get('message', '')}"
            
            if result.get("status") == "success":
                return HookResult.success(message, details=details)
            elif result.get("status") == "staged":
                return HookResult.warning(message, details=details)
            else:
                return HookResult.success(message, details=details)
        
        except Exception as e:
            logger.error(f"Failed to process last-word updates: {e}")
            return HookResult.failure(
                f"Failed to process last-word updates: {e}",
                details={"error": str(e)}
            )
    
    def _load_knowledge_context(self, config) -> str:
        """
        Load knowledge bases into system prompt context.
        
        Returns a formatted string with knowledge base information
        that helps the model understand what can be updated.
        """
        lines = ["## Knowledge Base Update Protocol"]
        lines.append("")
        lines.append("You can update knowledge bases using the last-word protocol.")
        lines.append("Available knowledge bases:")
        lines.append("")
        
        for kb_name in config.session_bootstrap:
            kb = config.get_knowledge_base(kb_name)
            if kb and kb.enabled:
                lines.append(f"- **{kb.name}**: {kb.description}")
                lines.append(f"  Path: `{kb.path}`")
        
        lines.append("")
        lines.append("To declare an update, use the following format:")
        lines.append("```")
        lines.append('plan(path="USER.md", heading="Research Interests", '
                    'content="...", operation="update")')
        lines.append("```")
        lines.append("")
        lines.append("Operations: update, clear, delete, no-op")
        
        return "\n".join(lines)


def get_session_id() -> Optional[str]:
    """Get current session ID from buffer (utility function)."""
    from . import core
    return core._session_id
