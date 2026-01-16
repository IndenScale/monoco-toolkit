---
id: EPIC-0012
uid: 1c7c3e
type: epic
status: open
stage: doing
title: Enable Agent Execution in VS Code Extension
created_at: '2026-01-15T08:55:46'
opened_at: '2026-01-15T08:55:46'
updated_at: '2026-01-15T08:55:46'
dependencies: []
related: []
tags: []
progress: 3/3
files_count: 0
---

## EPIC-0012: Enable Agent Execution in VS Code Extension

## Objective

Enable users to execute Monoco Agent profiles (defined in `.monoco/execution/SOP.md`) directly from VS Code.
Identify available profiles via LSP and trigger them using a visual interface (Agent Bar).

## Acceptance Criteria

- [ ] **Profile Discovery**: LSP server scans and returns all available execution profiles.
- [ ] **Agent Bar UI**: A dedicated view in VS Code to list profiles.
- [ ] **Execution**: Clicking a profile triggers the corresponding command in a VS Code terminal.

## Technical Tasks

- [x] **LSP Server**: Implement `monoco/getExecutionProfiles` request handler.
- [ ] **VS Code Client**: Implement `AgentSidebarProvider` to render the list of profiles.
- [ ] **VS Code Client**: Implement `monoco.runProfile` command.
