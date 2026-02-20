# Last-Word: Simplified Knowledge Update System

## Overview

The knowledge update system has been **significantly simplified**. The complex YAML-based workflow has been replaced with a direct, manual approach using `mdp` tool.

## Architecture

```
PreSessionStop Event
        ↓
   Hook Triggered
        ↓
  Show Guidance
        ↓
Agent Uses mdp → Direct Edit to MD
```

## Hook

**Path**: `resources/hooks/pre-session-stop`

Triggers on `PreSessionStop` event, outputs guidance reminding the agent
to consider updating knowledge bases.

## Knowledge Bases

| File | Path | Purpose |
|------|------|---------|
| USER.md | `~/.config/agents/USER.md` | User identity, preferences, background |
| SOUL.md | `~/.config/agents/SOUL.md` | AI personality, values, thinking framework |
| AGENTS.md | `~/.config/agents/AGENTS.md` | Global best practices across projects |
| ./AGENTS.md | `./AGENTS.md` | Project-specific context |

## Usage

When you see the guidance at session end:

1. Decide if any knowledge bases need updates
2. Use `mdp` tool to edit directly:

```bash
# Append
mdp patch -f ~/.config/agents/USER.md -H '## Research Interests' \
    -i 0 --op append -c '- New item'

# Replace
mdp patch -f ~/.config/agents/USER.md -H '## Notes' \
    -i 0 --op replace -c 'New content' -p 'Old.*'

# Delete
mdp patch -f ~/.config/agents/USER.md -H '## Temp' -i 0 --op delete
```

## Why Simplified?

Old system: `plan() → Buffer → YAML → Validate → Staging → Apply → MD`

New system: `Hook → Guidance → mdp → MD`

- No hidden state
- No intermediate files
- Direct and transparent
- Agent has full control
