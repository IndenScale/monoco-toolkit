---
id: EPIC-0010
type: epic
status: Closed
stage: done
solution: implemented
title: Agent Terminal Integration (PTY & Console)
created_at: "2026-01-14T00:00:00"
updated_at: "2026-01-15T13:46:02"
dependencies:
  - EPIC-0005
  - EPIC-0006
related: []
tags:
  - agent-native
  - terminal
  - cli
  - websocket
owner: Product Owner
progress: 4/4
files_count: 0
uid: d8a571
---

## EPIC-0010: Agent Terminal Integration (PTY & Console)

# Agent Terminal Integration (PTY & Console)

## Executive Summary

为了实现 Monoco "Agent Cockpit" 的愿景，我们需要在 Kanban 界面中引入原生的终端控制台 (Terminal Console)。这将允许用户直接在一个界面中进行 "战略指挥" (Kanban) 和 "战术执行" (CLI Agents)。

通过引入 PTY (Pseudo-Terminal) 和 WebSocket 支持，用户将能够直接在 Web 界面中运行 `gemini`、`claude` 或 `git` 命令，并享受完整的终端交互体验。

## Outcome & Value

- **God Mode + God Hand**: 用户在查看全局进度的同时，拥有直接操作底层的能力。
- **Agent Native Interaction**: 不再依赖受限的 Chatbot UI，而是拥抱功能最全、生态最丰富的 CLI Agents。
- **Context Awareness**: 终端 session 将能够感知 Kanban 当前的上下文（如选中的 Issue），实现无缝的人机协作。

## Key Results (KRs)

- [x] **KR1**: Toolkit Daemon 实现支持多会话 (Multi-Session) 的 PTY 管理器 (`monoco.daemon.terminal`)。
- [x] **KR2**: Kanban UI 实现带有 Tab 页签切换功能的原生终端面板。
- [x] **KR3**: 实现 "Context Injection" 与 "Auto-Startup"，支持自动运行预设命令 (e.g. `claude`, `gemini`) 并注入上下文，减少冷启动等待。
- [x] **KR4**: 验证主流 CLI Agent 在 Web 终端中的交互流畅性。

## Acceptance Criteria

- [x] Functional PTY manager in Daemon.
- [x] Terminal panel in Kanban UI with tab support.

## Technical Tasks

- [x] Implement PTY manager.
- [x] Integrate xterm.js in Kanban.

## Review Comments

- [x] Self-Review
