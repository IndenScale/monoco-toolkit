"""
Last-Word: Session-End Knowledge Delta Protocol.

This module implements the last-word protocol for declarative knowledge base updates
at the end of an agent session.

## Quick Start

```python
from monoco.features.last_word import plan, process_session_end, init_session

# Initialize at session start
init_session()

# During session, declare update intentions
plan(
    path="~/.config/agents/USER.md",
    heading="Research Interests",
    content="- AI Agents\n- Domain Modeling",
    operation="update",
    confidence=0.95,
    reason="User discussed these topics extensively"
)

# At session end (automatic via hook)
result = process_session_end()
```

## Architecture

1. **Session Start**: `init_session()` initializes the buffer
2. **Session Running**: `plan()` stores entries in memory
3. **Pre-Session-Stop**: `process_session_end()` validates and writes to YAML
4. **Apply**: `apply_yaml_to_markdown()` applies updates to .md files

## Operations

| Operation | Content    | Behavior                    |
|-----------|------------|-----------------------------|
| no-op     | null       | No update (placeholder)     |
| update    | "..."      | Create or overwrite heading |
| clear     | ""         | Clear content, keep heading |
| delete    | null       | Delete entire heading       |
"""

from .models import (
    Entry,
    TargetKey,
    EntryMeta,
    OperationType,
    LastWordSchema,
    ValidationResult,
    ApplyResult,
    LastWordConfig,
    KnowledgeBaseConfig,
)

from .core import (
    init_session,
    plan,
    process_session_end,
    get_buffer,
    clear_buffer,
    validate_entries,
    list_staged,
    apply_yaml_to_markdown,
    apply_entry_to_markdown,
    get_last_word_dir,
    get_staging_dir,
    ensure_directories,
)

from .config import (
    load_config,
    save_config,
    get_effective_config,
)

try:
    from .hook import LastWordHook
except ImportError:
    LastWordHook = None  # type: ignore

__all__ = [
    # Models
    "Entry",
    "TargetKey",
    "EntryMeta",
    "OperationType",
    "LastWordSchema",
    "ValidationResult",
    "ApplyResult",
    "LastWordConfig",
    "KnowledgeBaseConfig",
    # Core functions
    "init_session",
    "plan",
    "process_session_end",
    "get_buffer",
    "clear_buffer",
    "validate_entries",
    "list_staged",
    "apply_yaml_to_markdown",
    "apply_entry_to_markdown",
    "get_last_word_dir",
    "get_staging_dir",
    "ensure_directories",
    # Config
    "load_config",
    "save_config",
    "get_effective_config",
    # Hook
    "LastWordHook",
]
