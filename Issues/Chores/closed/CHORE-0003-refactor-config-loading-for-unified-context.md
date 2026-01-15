---
id: CHORE-0003
uid: ee962c
type: chore
status: closed
stage: done
title: Refactor Config Loading for Unified Context
created_at: '2026-01-15T12:55:25'
opened_at: '2026-01-15T12:55:25'
updated_at: '2026-01-15T13:06:28'
closed_at: '2026-01-15T13:06:28'
solution: implemented
dependencies: []
related: []
tags: []
---

## CHORE-0003: Consolidate Configuration to `.monoco/` directory

## Context

Currently, the system supports both `monoco.yaml` (in file root) and `.monoco/config.yaml`.
This dual support creates ambiguity and maintenance overhead.
**Decision**: We will standardize on using the **`.monoco/` directory** as the sole indicator of a Monoco context.

## Objective

Remove all dependencies on `monoco.yaml` from the codebase.
Configuration must reside in `.monoco/config.yaml`.

## Parent

EPIC-0013

## Technical Tasks

- [x] **Update Config Loader**: Modify `monoco.core.config.py` to stop looking for `monoco.yaml`.
- [x] **Update Workspace Scanner**: Modify `monoco.core.workspace.py` (and any `ProjectManager` logic) to identify projects solely by the existence of a `.monoco/` directory.
- [x] **Migration Utility (Optional)**: Add a logic snippet to warn users if `monoco.yaml` is found and suggest moving it.

## Acceptance Criteria

- [x] `monoco.core.config.get_config` is marked as legacy/deprecated or strictly scoped to CWD only.
- [x] `ProjectManager` can load Project A and Project B, and `ProjectContext(A).config` is different from `ProjectContext(B).config`.
- [x] `monoco serve` starts up correctly.

## Solution

Refactored configuration loading to standardize on `.monoco/config.yaml`. Removed all dependencies on `monoco.yaml`.
Migrated existing `monoco.yaml` files in the repository to their respective `.monoco/` directories.
Added a legacy warning in `monoco.core.config.py` for users still using `monoco.yaml`.
Updated `core.workspace.is_project_root` to identify projects solely by the existence of a `.monoco/` directory.
