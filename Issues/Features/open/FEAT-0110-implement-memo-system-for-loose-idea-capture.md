---
id: FEAT-0110
uid: ce5d27
type: feature
status: open
stage: review
title: Implement Memo System for loose idea capture
created_at: '2026-01-29T17:08:49'
updated_at: '2026-01-29T17:11:54'
parent: EPIC-0001
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0001'
- '#FEAT-0110'
files: []
opened_at: '2026-01-29T17:08:49'
isolation:
  type: branch
  ref: feat/feat-0110-implement-memo-system-for-loose-idea-capture
  created_at: '2026-01-29T17:08:54'
---

## FEAT-0110: Implement Memo System for loose idea capture

## Objective
Provide a low-friction CLI mechanism to capture fleeting ideas (Memos) into a simple Markdown inbox (`Memos/inbox.md`) without the overhead of creating structured issues.

## Acceptance Criteria
- [x] CLI `monoco memo add <content>` appends a new memo to `Memos/inbox.md`.
- [x] CLI `monoco memo list` displays the most recent memos.
- [x] Data persistence uses simple Markdown Append-Only structure.

## Technical Tasks

- [x] Implement `monoco/features/memo` package structure.
- [x] Implement `core.py`: Add/List logic using regex parsing.
- [x] Implement `cli.py`: Typer commands for `add` and `list`.
- [x] Integrate with `monoco/main.py` CLI registry.
- [x] Verify context/config resolution logic handles `issues_root` correctly.

## Review Comments
- Manually tested `monoco memo add` and `monoco memo list`.
- Verified storage file format in `Memos/inbox.md`.
