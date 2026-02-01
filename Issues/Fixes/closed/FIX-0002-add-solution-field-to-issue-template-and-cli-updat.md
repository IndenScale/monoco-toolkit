---
id: FIX-0002
uid: d5f310
type: fix
status: closed
stage: done
title: Add 'solution' field to Issue Template and CLI update command
created_at: '2026-02-01T21:42:30'
updated_at: '2026-02-01T21:49:52'
parent: EPIC-0030
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0030'
- '#FIX-0002'
files:
- monoco/features/issue/core.py
- monoco/features/issue/commands.py
criticality: high
solution: implemented
opened_at: '2026-02-01T21:42:30'
closed_at: '2026-02-01T21:49:52'
---

## FIX-0002: Add 'solution' field to Issue Template and CLI update command

## Objective
<!-- Describe the "Why" and "What" clearly. Focus on value. -->
Add the `solution` field to Issue templates and CLI update command to ensure consistency with the close command and improve issue lifecycle management.

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [x] Issue template includes `solution` field with helpful comment
- [x] CLI `update` command supports `--solution` parameter
- [x] Solution field is properly serialized in YAML frontmatter

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->
<!-- - [ ] Parent Task -->
<!--   - [ ] Sub Task -->

- [x] Add `solution` field to `_serialize_metadata()` in `core.py`
- [x] Add YAML comment for solution field guidance
- [x] Add `--solution` parameter to CLI `update` command

## Review Comments
Fix completed. The solution field is now:
1. Included in new issue templates with a helpful comment showing valid values
2. Supported by the `monoco issue update` command via `--solution` parameter
