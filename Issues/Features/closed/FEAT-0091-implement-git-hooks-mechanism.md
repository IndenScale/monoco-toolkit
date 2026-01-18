---
id: FEAT-0091
uid: c64e73
type: feature
status: closed
stage: done
title: Implement Git Hooks Mechanism
created_at: '2026-01-19T00:27:17'
opened_at: '2026-01-19T00:27:17'
updated_at: '2026-01-19T00:30:01'
closed_at: '2026-01-19T00:30:01'
parent: EPIC-0017
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0091: Implement Git Hooks Mechanism

## Objective

<!-- Describe the "Why" and "What" clearly. Focus on value. -->

## Acceptance Criteria

<!-- Define binary conditions for success. -->

- [x] Workspace init creates .git/hooks scripts
- [x] CLI init creates .git/hooks scripts
- [x] Hooks are configurable via workspace.yaml

## Technical Tasks

- [x] Defined `HooksConfig` in `monoco/core/config.py`
- [x] Implemented `install_hooks` in `monoco/core/hooks.py`
- [x] Integrated hook installation into `monoco/core/setup.py` (CLI Init)
- [x] Integrated hook installation into `monoco/cli/workspace.py` (Workspace Init)

## Review Comments

<!-- Required for Review/Done stage. Record review feedback here. -->
