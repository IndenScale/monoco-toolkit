"""
Agent Tool Adapter for Issue Lifecycle Hooks

Bridges between Agent-specific events (Claude Code, Gemini CLI) and
Monoco's canonical Issue lifecycle events.

This adapter:
1. Intercepts Agent tool usage events (e.g., PreToolUse)
2. Parses the command to identify Issue lifecycle commands
3. Translates to canonical IssueEvent
4. Executes hooks via IssueHookDispatcher
5. Translates results back to Agent-compatible format
"""

import re
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from pathlib import Path

from .models import (
    IssueEvent,
    IssueHookContext,
    IssueHookResult,
    HookDecision,
    NamingACL,
    get_events_for_command,
)
from .dispatcher import get_dispatcher

logger = logging.getLogger(__name__)


@dataclass
class ParsedIssueCommand:
    """Result of parsing an issue command."""
    subcommand: str
    issue_id: Optional[str] = None
    args: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.args is None:
            self.args = {}


class AgentToolAdapter:
    """
    Adapter that translates between Agent events and Issue lifecycle events.
    
    This adapter is designed to be used in Agent hook contexts (PreToolUse, etc.)
    to intercept and validate Issue commands before execution.
    """
    
    # Command patterns to match
    ISSUE_COMMAND_PATTERN = re.compile(
        r'(?:monoco\s+)?issue\s+(\w+)\s*(.*)',
        re.IGNORECASE
    )
    
    def __init__(self, project_root: Optional[Path] = None, agent_type: str = "claude"):
        """
        Initialize the adapter.
        
        Args:
            project_root: Project root path
            agent_type: Agent type ("claude", "gemini")
        """
        self.project_root = project_root
        self.agent_type = agent_type
        self.dispatcher = get_dispatcher(project_root)
    
    def parse_command(self, command: str) -> Optional[ParsedIssueCommand]:
        """
        Parse an issue command string.
        
        Args:
            command: The command string to parse
            
        Returns:
            ParsedIssueCommand or None if not an issue command
        """
        match = self.ISSUE_COMMAND_PATTERN.match(command)
        if not match:
            return None
        
        subcommand = match.group(1).lower()
        rest = match.group(2).strip()
        
        # Extract issue ID (first positional argument)
        issue_id = None
        args = {}
        
        # Parse arguments
        tokens = rest.split()
        if tokens and not tokens[0].startswith("-"):
            issue_id = tokens[0].upper()
            tokens = tokens[1:]
        
        # Parse flags
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.startswith("--"):
                key = token[2:].replace("-", "_")
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    args[key] = tokens[i + 1]
                    i += 2
                else:
                    args[key] = True
                    i += 1
            elif token.startswith("-"):
                key = token[1:]
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    args[key] = tokens[i + 1]
                    i += 2
                else:
                    args[key] = True
                    i += 1
            else:
                i += 1
        
        return ParsedIssueCommand(
            subcommand=subcommand,
            issue_id=issue_id,
            args=args,
        )
    
    def translate_event(self, agent_event: str) -> Optional[IssueEvent]:
        """
        Translate Agent event to canonical IssueEvent.
        
        Args:
            agent_event: The Agent-specific event name
            
        Returns:
            IssueEvent or None if not mapped
        """
        # First check if it's already canonical
        try:
            return IssueEvent(agent_event)
        except ValueError:
            pass
        
        # Try to map from Agent event
        canonical = NamingACL.from_agent_event(agent_event, self.agent_type)
        if canonical:
            try:
                return IssueEvent(canonical)
            except ValueError:
                pass
        
        return None
    
    def translate_back(self, result: IssueHookResult) -> Dict[str, Any]:
        """
        Translate IssueHookResult to Agent-compatible format.
        
        Args:
            result: The hook execution result
            
        Returns:
            Dictionary formatted for Agent consumption
        """
        response = {
            "decision": result.decision.value,
            "message": result.message,
            "allow": result.decision == HookDecision.ALLOW,
            "block": result.decision == HookDecision.DENY,
            "warn": result.decision == HookDecision.WARN,
        }
        
        if result.suggestions:
            response["suggestions"] = result.suggestions
        
        if result.diagnostics:
            response["diagnostics"] = [
                {
                    "line": d.line,
                    "column": d.column,
                    "severity": d.severity,
                    "message": d.message,
                    "source": d.source,
                }
                for d in result.diagnostics
            ]
        
        if result.context:
            response["context"] = result.context
        
        return response
    
    def intercept(
        self,
        command: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Intercept and validate an issue command.
        
        This is the main entry point for Agent integration.
        
        Args:
            command: The command string being executed
            context: Additional context from the Agent
            
        Returns:
            Interception result or None if not an issue command
        """
        parsed = self.parse_command(command)
        if not parsed:
            return None
        
        # Get the pre-event for this command
        pre_event, post_event = get_events_for_command(parsed.subcommand)
        if not pre_event:
            return None
        
        # Build hook context
        hook_context = self._build_context(parsed, context, pre_event)
        
        # Execute pre-hook
        result = self.dispatcher.execute(pre_event, hook_context)
        
        # Translate result for Agent
        return self.translate_back(result)
    
    def _build_context(
        self,
        parsed: ParsedIssueCommand,
        agent_context: Optional[Dict[str, Any]],
        event: IssueEvent,
    ) -> IssueHookContext:
        """
        Build IssueHookContext from parsed command and Agent context.
        
        Args:
            parsed: Parsed issue command
            agent_context: Context from Agent
            event: The lifecycle event
            
        Returns:
            Populated IssueHookContext
        """
        if agent_context is None:
            agent_context = {}
        
        # Determine project root
        project_root = self.project_root
        if not project_root and "project_root" in agent_context:
            project_root = Path(agent_context["project_root"])
        
        # Get git info if available
        current_branch = agent_context.get("current_branch")
        default_branch = agent_context.get("default_branch", "main")
        
        return IssueHookContext(
            event=event,
            trigger_source="agent",
            issue_id=parsed.issue_id,
            project_root=project_root,
            current_branch=current_branch,
            default_branch=default_branch,
            force=parsed.args.get("force", False) or parsed.args.get("f", False),
            no_hooks=parsed.args.get("no_hooks", False),
            debug_hooks=parsed.args.get("debug_hooks", False),
            extra=agent_context,
        )
    
    def can_execute(self, command: str) -> bool:
        """
        Check if a command can be executed (hooks pass).
        
        Args:
            command: The command to check
            
        Returns:
            True if execution is allowed
        """
        result = self.intercept(command)
        if result is None:
            return True  # Not an issue command, allow
        
        return result.get("allow", False)


def create_adapter(
    project_root: Optional[Path] = None,
    agent_type: str = "claude",
) -> AgentToolAdapter:
    """
    Create an AgentToolAdapter instance.
    
    Args:
        project_root: Project root path
        agent_type: Agent type ("claude", "gemini")
        
    Returns:
        Configured AgentToolAdapter
    """
    return AgentToolAdapter(project_root, agent_type)
