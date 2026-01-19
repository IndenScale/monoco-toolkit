# Structure Anatomy

A Monoco Issue is essentially an **executable Markdown file**. Its design satisfies both human readability and Agent parsability.

## 1. Physical Composition

A standard Issue file (e.g., `Issues/Features/open/FEAT-001.md`) consists of three parts:

```markdown
---
# YAML Front Matter (Metadata Layer)
id: FEAT-001
type: feature
status: open
stage: doing
title: Implement Dark Mode
files:
  - src/theme.ts
  - src/components/Toggle.tsx
---

## FEAT-001: Implement Dark Mode

<!-- Body (Content Layer) -->

## Acceptance Criteria

- [ ] Support System Preference auto-switch
- [ ] Support manual toggle switch

## Technical Tasks

- [x] Define Theme Interface
- [/] Implemenet Context Provider
```

### 1.1 YAML Front Matter (Machine-Readable)

This is the primary interface for Agents to understand the task.

- **Identity**: `id`, `uid` (unique identifier).
- **Lifecycle**: `status` (physical location), `stage` (logical progress).
- **Topology**: `parent`, `dependencies`, `related` (building the knowledge graph).
- **Context**: `files` list. Records which code files have been modified by this Issue. This allows Agents to instantly load necessary context when resuming a task.

### 1.2 Markdown Body (Human-Machine Shared)

- **Heading**: `## {ID}: {Title}`. Must strictly match metadata as a consistency anchor.
- **Checkbox Matrix**:
  - `[ ]` To Do
  - `[/]` Doing
  - `[x]` Done
  - `[-]` Cancelled
  - Agents update task progress by parsing these checkboxes.

## 2. Static Linting

To prevent Agents (or humans) from writing malformed tasks, Monoco introduces a **Schema-on-Read** strong validation mechanism.

Running `monoco issue lint` checks:

1.  **Completeness**: Are required fields (like `title`) missing? Are `Technical Tasks` missing?
2.  **Consistency**: Do the filename, ID, and Heading match?
3.  **Compliance**: For `Closed` issues, are all checkboxes completed? Are there unresolved `Review Comments`?
4.  **Environment Policy**: Is code being modified on the main branch by mistake?

Only an Issue that passes Lint is considered **"executable."**

---

[Previous: 00. Overview](./00_overview.md) | \*\*Next: 02. Lifecycle Loop](./02_lifecycle.md)
