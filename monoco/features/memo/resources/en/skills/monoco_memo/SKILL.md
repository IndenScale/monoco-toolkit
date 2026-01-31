---
name: monoco-memo
description: Lightweight memo system for quickly recording ideas, inspirations, and temporary notes. Distinguished from the formal Issue system.
type: standard
version: 1.0.0
---

# Monoco Memo

Use this skill to quickly capture fleeting notes (fleeting ideas) without creating a formal Issue.

## When to Use Memo vs Issue

| Scenario | Use | Reason |
|----------|-----|--------|
| Temporary ideas, inspirations | **Memo** | No tracking needed, no completion status required |
| Code snippets, link bookmarks | **Memo** | Quick record, organize later |
| Meeting notes | **Memo** | Record first, then extract tasks |
| Actionable work unit | **Issue** | Requires tracking, acceptance criteria, lifecycle |
| Bug fix | **Issue** | Needs to record reproduction steps, verification results |
| Feature development | **Issue** | Needs design, decomposition, delivery |

> **Core Principle**: Memos record **ideas**; Issues handle **actionable tasks**.

## Commands

### Add Memo

```bash
monoco memo add "Your memo content"
```

Optional parameters:
- `-c, --context`: Add context reference (e.g., `file:line`)

Examples:
```bash
# Simple record
monoco memo add "Consider using Redis cache for user sessions"

# Record with context
monoco memo add "Recursion here may cause stack overflow" -c "src/utils.py:42"
```

### View Memo List

```bash
monoco memo list
```

Displays all unarchived memos.

### Open Memo File

```bash
monoco memo open
```

Opens the memo file in the default editor for organizing or batch editing.

## Workflow

```
Idea flashes → monoco memo add "..." → Regular organization → Extract into Issue or archive
```

1. **Capture**: Use `monoco memo add` immediately when you have an idea
2. **Organize**: Regularly (e.g., daily/weekly) run `monoco memo list` to review
3. **Convert**: Transform valuable memos into formal Issues
4. **Archive**: Remove from memos after processing

## Best Practices

1. **Keep concise**: Memos are quick notes, no detailed description needed
2. **Convert timely**: Valuable ideas should be converted to Issue as soon as possible to avoid forgetting
3. **Clean up regularly**: Memos are temporary, don't let them accumulate indefinitely
4. **Use context**: When recording code-related ideas, use `-c` parameter to mark the location
