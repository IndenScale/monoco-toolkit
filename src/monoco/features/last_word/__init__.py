"""
Last-Word: Simplified Knowledge Update System.

This module provides a minimal, hook-based approach to knowledge base updates:
- Agenthook at resources/hooks/pre-session-stop outputs guidance
- Agent uses `mdp` tool directly to edit markdown files
- No intermediate layers, no state management

Usage:
    The hook triggers automatically at pre-session-stop event.
    The agent sees the guidance and decides whether to update
    knowledge bases using `mdp` tool.
"""
