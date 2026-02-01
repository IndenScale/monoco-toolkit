---
id: EPIC-0031
uid: 7750aa
type: epic
status: open
stage: draft
title: Design and Implement Monoco Native Hook System
created_at: '2026-02-01T20:56:45'
updated_at: '2026-02-01T20:56:45'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0031'
files: []
criticality: high
opened_at: '2026-02-01T20:56:45'
---

## EPIC-0031: Design and Implement Monoco Native Hook System

## Objective
Implement a unified Monoco Native Hook System to manage agent lifecycles and ecosystem tools, addressing the fragmentation of private hooks in CLI tools (gemini, kimi, etc.).

**Context:**
- **Problem**: Current CLI tools (gemini, kimi) implement private agent hooks, leading to ecosystem fragmentation. Standard Git hooks lack the necessary context (e.g., Session ID, Issue ID).
- **Goal**: Create a native hook system that can orchestrate lifecycle events across different agents and tools.
- **Reference**:
    - **Kimi CLI Hooks**: The Kimi CLI supports "Wire Mode" (JSON-RPC over stdio) which emits events like `TurnBegin`, `StepBegin`, `ToolCall`, etc. This is the preferred integration method over internal hooks.

## Acceptance Criteria
- [ ] Monoco Hook System architecture is defined and documented.
- [ ] Core Hook Engine is implemented.
- [ ] Integration with Kimi CLI "Wire Mode" is demonstrated.
- [ ] Standard Git Hooks (pre-commit, pre-push) are integrated via Monoco (see FEAT-0145).

## Technical Tasks
- [ ] Design the Event Bus and Hook Interface.
- [ ] Implement the Hook Registry in `monoco/core/hooks`.
- [ ] Implement Kimi CLI Wire Mode Adapter.
- [ ] Implement Git Hooks integration (see FEAT-0145).

## Review Comments