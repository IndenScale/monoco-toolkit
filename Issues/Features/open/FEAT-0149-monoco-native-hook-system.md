---
id: FEAT-0149
uid: 7750aa
type: feature
status: open
stage: draft
title: Design and Implement Monoco Native Hook System
created_at: '2026-02-01T20:56:45'
updated_at: '2026-02-01T22:42:00'
parent: EPIC-0025
dependencies: []
related:
- EPIC-0025
domains:
- AgentScheduling
tags:
- '#EPIC-0000'
- '#EPIC-0025'
- '#FEAT-0149'
files: []
criticality: high
opened_at: '2026-02-01T20:56:45'
---

## FEAT-0149: Design and Implement Monoco Native Hook System

## 背景与目标

本 Epic 旨在设计和实现 Monoco 原生钩子系统，用于统一管理代理生命周期和生态系统工具。通过建立标准化的事件总线和钩子接口，解决当前 CLI 工具（如 gemini、kimi）私有钩子导致的生态碎片化问题。该系统将提供比标准 Git 钩子更丰富的上下文信息（如会话 ID、Issue ID），支持跨不同代理和工具的生命周期事件编排。

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