---
id: FEAT-0108
uid: 0bb83e
type: feature
status: closed
stage: done
title: Remove prune flag from submit command
created_at: '2026-01-26T00:01:40'
updated_at: 2026-01-26 00:13:11
parent: null
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0108'
files: []
opened_at: '2026-01-26T00:01:40'
closed_at: '2026-01-26T00:13:06'
solution: implemented
---

## FEAT-0108: Remove prune flag from submit command

## Objective

### Why
Currently, `monoco issue submit` includes `--prune` and `--force` flags for deleting branches/worktrees. This is semantically incorrect because:

1. **Submit ≠ Complete**: `submit` moves an issue to Review stage, not completion. The work may require further iteration if review feedback is provided.
2. **Premature Cleanup**: Deleting the working environment before review approval creates unnecessary friction and potential data loss.
3. **Lifecycle Misalignment**: Environment cleanup should occur at the **end** of an issue's lifecycle (`close`), not at the handoff point (`submit`).

### What
Remove `--prune` and `--force` flags from `monoco issue submit` command. Environment cleanup should only be available via `monoco issue close --prune`.

## Acceptance Criteria

- [x] `monoco issue submit --help` does not show `--prune` or `--force` options
- [x] `monoco issue close --help` continues to show `--prune` and `--force` options
- [x] Existing tests are updated to reflect the new behavior
- [x] Documentation (GEMINI.md, CLI help text) reflects this change

## Technical Tasks

- [x] Remove `--prune` and `--force` flags from `submit` command definition
  - [x] Update `monoco/features/issue/commands.py` - remove flags from `submit` function
  - [x] Remove branch/worktree cleanup logic from `submit` implementation
- [x] Verify `close` command retains cleanup functionality
  - [x] Confirm `--prune` and `--force` flags exist in `close` command
  - [x] Test cleanup behavior works correctly
- [x] Update tests
  - [x] No tests existed for `submit --prune` behavior (verified via grep)
  - [x] Existing workflow tests still pass
- [x] Update documentation
  - [x] CLI help text for `submit` command is automatically updated
  - [x] Add guidance in `Toolkit/GEMINI.md` about proper cleanup timing

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
