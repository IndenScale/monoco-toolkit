---
id: FEAT-0101
uid: 4e0731
type: feature
status: open
stage: draft
title: Implement Stateless Agent Draft Command
created_at: '2026-01-24T19:10:47'
opened_at: '2026-01-24T19:10:47'
updated_at: '2026-01-24T19:10:47'
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0101'
files: []
parent: EPIC-0019
# solution: null      # Required for Closed state (implemented, cancelled, etc.)
---

## FEAT-0101: Implement Stateless Agent Draft Command

## Objective
Implement a "One-shot" CLI command for Agents to perform atomic tasks without persistent sessions.
Initial use case: `monoco agent draft` to generate Issue files from a short text description.
This decouples Agent intelligence from the Daemon runtime, allowing for quick, scriptable usage.

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [ ] **CLI Command**: `monoco agent draft` available.
- [ ] **Inputs**: Supports `--type` and `--desc` (description).
- [ ] **Output**: Automatically creates a structured Issue file based on the description.
- [ ] **Stateless**: Does not require a running Daemon or Session.

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->
<!-- - [ ] Parent Task -->
<!--   - [ ] Sub Task -->

- [ ] CLI Command Implementation (`monoco agent draft`)
- [x] Mock Generation Logic (Template-based for MVP)
- [ ] Session-based Integration (Run as a short-lived Agent Session)
- [x] Integration with Issue Core (create_issue_file)

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->

## Post-mortem (Session ae71e4f9)
**Date**: 2026-01-24
**Author**: Coroner (System)

### Issue Analysis
The previous session terminated unexpectedly while working on this feature.
Upon inspection, the `monoco agent draft` command was marked as "Done", but the implementation is missing from `monoco/features/scheduler/cli.py`.

### Findings
1.  **Missing CLI Entry Point**: `monoco/features/scheduler/cli.py` only contains `run`, `kill`, `autopsy`, `list`, and `logs`. The `draft` command is not defined.
2.  **Core Logic Exists**: `monoco/features/issue/core.py` correctly defines `create_issue_file`, and `monoco/features/scheduler/worker.py` appears to have `drafter` role logic.
3.  **Inconsistent State**: The tasks were marked as completed in the Issue file, but the code does not reflect this.

### Recovery Plan
-   Reset tasks: "CLI Command Implementation" and "Session-based Integration".
-   Next agent must implement the `draft` command in `monoco/features/scheduler/cli.py`.
-   Verify that `monoco agent draft --desc "..."` correctly invokes the logic to create an issue file.
