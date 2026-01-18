---
id: CHORE-0008
uid: 302bb8
type: chore
status: closed
stage: done
title: Fix monoco init syntax error and idempotency
created_at: '2026-01-19T00:34:15'
opened_at: '2026-01-19T00:34:15'
updated_at: '2026-01-19T00:35:31'
closed_at: '2026-01-19T00:35:31'
parent: EPIC-0017
solution: implemented
dependencies: []
related: []
tags: []
---

## CHORE-0008: Fix monoco init syntax error and idempotency

## Objective

<!-- Describe the "Why" and "What" clearly. Focus on value. -->

## Acceptance Criteria

<!-- Define binary conditions for success. -->

- [x] `monoco init` runs without SyntaxError
- [x] re-running `monoco init` does not delete config but ensures hooks are installed

## Technical Tasks

<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->
<!-- - [ ] Parent Task -->
<!--   - [ ] Sub Task -->

- [x] Fix SyntaxError in `monoco/core/setup.py`
- [x] Refactor `init_cli` to support idempotent re-runs (skip config overwrite, allow resource init)

## Review Comments

<!-- Required for Review/Done stage. Record review feedback here. -->
