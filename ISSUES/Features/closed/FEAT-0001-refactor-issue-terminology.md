---
id: FEAT-0001
type: feature
status: closed
title: Refactor Issue Terminology to Agent-Native Semantics
created_at: 2026-01-09
solution: implemented
dependencies: []
related: []
tags: [refactor, agent-native]
---

## FEAT-0001: Refactor Issue Terminology to Agent-Native Semantics

## Objective

Transition the Monoco Issue System from Scrum/Jira-based jargon (Epic/Story/Task/Bug) to Agent-Native semantics (Goal/Feature/Chore/Fix) to reduce cognitive load and improve alignment between intent and execution.

## Background

As discussed, "Story" imposes a narrative burden ("As a user...") that is often unnecessary for Agent-Human collaboration, where direct functional definition ("Feature") is more efficient. "Task" is too generic, whereas "Chore" clearly defines maintenance work. "Epic" is too literary; "Goal" is direct.

## Terminology Mapping

| Old   | New         | ID Prefix | Directories |
| :---- | :---------- | :-------- | :---------- |
| Epic  | **Epic**    | `EPIC-`   | `Epics/`    |
| Story | **Feature** | `FEAT-`   | `Features/` |
| Task  | **Chore**   | `CHORE-`  | `Chores/`   |
| Bug   | **Fix**     | `FIX-`    | `Fixes/`    |

## Acceptance Criteria

1. Current codebase (`monoco` CLI) supports the new terminology.
2. Existing issues are migrated to new directory structures and filenames.
3. Internal file content (Frontmatter `type`, links `[[ID]]`) is updated.
4. Documentation (`SKILL.md`) is updated.

## Technical Tasks

- [x] **Refactor Codebase** (Core Logic)
  - [x] Update `IssueType` and `IssueStatus` in `toolkit/monoco/features/issue/models.py`.
  - [x] Update CLI commands in `toolkit/monoco/features/issue/commands.py` to accept new types.
  - [x] Update Lint logic to recognize new directory structures.
- [x] **Data Migration**
  - [x] Rename directories: `Epics`->`Goals`, `Stories`->`Features`, `Tasks`->`Chores`, `Bugs`->`Fixes`.
  - [x] Rename files: Change prefixes (e.g., `FEAT-` -> `FEAT-`).
  - [x] Batch update file content: Replace `type: feature` with `type: feature`, etc.
  - [x] Batch update references: Update double-bracket links `[[FEAT-xx]]` -> `[[FEAT-xx]]`.
- [x] **Documentation**
  - [x] Rewrite `Toolkit/skills/issues-management/SKILL.md` to reflect the new ontology.
