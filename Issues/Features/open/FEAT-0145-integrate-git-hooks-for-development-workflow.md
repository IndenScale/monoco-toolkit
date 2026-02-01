---
id: FEAT-0145
uid: 6d6bf7
type: feature
status: open
stage: draft
title: Integrate Git Hooks for Development Workflow
created_at: '2026-02-01T20:57:03'
updated_at: '2026-02-01T20:57:03'
parent: EPIC-0031
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0031'
- '#FEAT-0145'
files: []
criticality: medium
opened_at: '2026-02-01T20:57:03'
---

## FEAT-0145: Integrate Git Hooks for Development Workflow

## Objective
Integrate Git Hooks (pre-commit, pre-push) into the Monoco workflow to ensure data integrity and process compliance.

**Context**:
- **Problem**: Issues with missing required fields (e.g., `solution` for closed issues) can break the indexer or dependencies. Manual fixes are error-prone.
- **Solution**: Use `pre-commit` to run `monoco issue lint` and prevent non-compliant commits.

## Acceptance Criteria
- [ ] `monoco sync` (or similar command) installs/updates git hooks.
- [ ] `pre-commit` hook runs `monoco issue lint` and blocks commit on failure.
- [ ] `pre-push` hook checks for uncompleted critical issues (optional/configurable).

## Technical Tasks
- [ ] Create hook templates in `monoco/assets/hooks`.
- [ ] Extend `monoco sync` to install hooks into `.git/hooks`.
- [ ] Implement the `pre-commit` logic (calling the linter).

## Review Comments