# Core Integration Registry

## Overview

The Core Integration Registry is the unified "map" for Monoco's interaction with external Agent environments. It provides a centralized registry for managing integrations with various Agent frameworks (Cursor, Claude, Gemini, Qwen, Antigravity, etc.).

## Core Concepts

### AgentIntegration

The integration configuration for each Agent framework contains the following fields:

- **key**: Unique identifier (e.g., `cursor`, `gemini`)
- **name**: Human-readable framework name
- **system_prompt_file**: Path to the system prompt file (relative to the project root)
- **skill_root_dir**: Path to the skill directory (relative to the project root)
- **enabled**: Whether the integration is enabled (default: `true`)

### Default Integration Table

| Framework       | Key      | System Prompt File | Skill Root Dir    |
| :-------------- | :------- | :----------------- | :---------------- |
| **Cursor**      | `cursor` | `.cursorrules`     | `.cursor/skills/` |
| **Claude Code** | `claude` | `CLAUDE.md`        | `.claude/skills/` |
| **Gemini CLI**  | `gemini` | `GEMINI.md`        | `.gemini/skills/` |
| **Qwen Code**   | `qwen`   | `QWEN.md`          | `.qwen/skills/`   |
| **Antigravity** | `agent`  | `GEMINI.md`        | `.agent/skills/`  |

## Usage

### 1. Using Default Integrations

```python
from monoco.core.integrations import get_integration, DEFAULT_INTEGRATIONS

# Get integration configuration for a specific framework
cursor_integration = get_integration("cursor")
print(cursor_integration.system_prompt_file)  # .cursorrules

# View all default integrations
for key, integration in DEFAULT_INTEGRATIONS.items():
    print(f"{integration.name}: {integration.system_prompt_file}")
```

### 2. Auto-detecting Frameworks in Project

```python
from pathlib import Path
from monoco.core.integrations import detect_frameworks
```
