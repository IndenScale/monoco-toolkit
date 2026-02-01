---
id: FEAT-0144
uid: 47e02d
type: feature
status: open
stage: draft
title: Enforce Strict Status and Directory Consistency in Issue Linter
created_at: '2026-02-01T20:56:58'
updated_at: '2026-02-01T20:56:58'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0144'
files: []
criticality: medium
opened_at: '2026-02-01T20:56:58'
---

## FEAT-0144: Enforce Strict Status and Directory Consistency in Issue Linter

## Objective
Enhance `monoco issue lint` to enforce strict consistency rules between Issue status and file location.

**Context**:
- Found cases where Issues had illegal statuses (e.g., `done` instead of `closed`) or were in the wrong directory (e.g., `Issues/Features/done/` instead of `closed/`).
- The current linter failed to catch these anomalies.

## Acceptance Criteria
- [ ] Linter reports error if `status` is not one of: `open`, `closed`, `backlog`.
- [ ] Linter reports error if file is not in the directory matching its status.
- [ ] Linter reports error for illegal directory names (e.g., `done/`).
- [ ] Linter verifies `stage` is valid (e.g., `draft`, `doing`, `review`, `done`).

## Technical Tasks
- [ ] Update `monoco/features/issue/linter.py`.
- [ ] Add validation rules for Status enum.
- [ ] Add validation rules for Directory <-> Status mapping.
- [ ] Add unit tests for invalid cases.

## Review Comments
