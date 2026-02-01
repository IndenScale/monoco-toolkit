---
id: FIX-0002
uid: d5f310
type: fix
status: open
stage: doing
title: Add 'solution' field to Issue Template and CLI update command
created_at: '2026-02-01T21:42:30'
updated_at: '2026-02-01T21:51:23'
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
opened_at: '2026-02-01T21:42:30'
---

## FIX-0002: Add 'solution' field to Issue Template and CLI update command

## Objective
<!-- Describe the "Why" and "What" clearly. Focus on value. -->
Add the `solution` field to Issue templates and CLI update command to ensure consistency with the close command and improve issue lifecycle management.

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [ ] Issue template includes `solution` field with helpful comment
- [ ] CLI `update` command supports `--solution` parameter
- [ ] Solution field is properly serialized in YAML frontmatter

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->
<!-- - [ ] Parent Task -->
<!--   - [ ] Sub Task -->

- [ ] Add `solution` field to `_serialize_metadata()` in `core.py`
- [ ] Add YAML comment for solution field guidance
- [ ] Add `--solution` parameter to CLI `update` command

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
