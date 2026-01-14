---
id: EPIC-0010
type: Epic
title: Agent Terminal Integration (PTY & Console)
status: Open
owner: Product Owner
parent: null
dependencies:
- EPIC-0005
- EPIC-0006
tags:
- agent-native
- terminal
- cli
- websocket
created_at: 2026-01-14
progress: 1/2
files_count: 0
stage: doing
---

# Agent Terminal Integration (PTY & Console)

## Executive Summary

为了实现 Monoco "Agent Cockpit" 的愿景，我们需要在 Kanban 界面中引入原生的终端控制台 (Terminal Console)。这将允许用户直接在一个界面中进行 "战略指挥" (Kanban) 和 "战术执行" (CLI Agents)。

通过引入 PTY (Pseudo-Terminal) 和 WebSocket 支持，用户将能够直接在 Web 界面中运行 `gemini`、`claude` 或 `git` 命令，并享受完整的终端交互体验。

## Outcome & Value

- **God Mode + God Hand**: 用户在查看全局进度的同时，拥有直接操作底层的能力。
- **Agent Native Interaction**: 不再依赖受限的 Chatbot UI，而是拥抱功能最全、生态最丰富的 CLI Agents。
- **Context Awareness**: 终端 session 将能够感知 Kanban 当前的上下文（如选中的 Issue），实现无缝的人机协作。

## Key Results (KRs)

- **KR1**: Toolkit Daemon 实现支持多会话 (Multi-Session) 的 PTY 管理器 (`monoco.daemon.terminal`)。
- **KR2**: Kanban UI 实现带有 Tab 页签切换功能的原生终端面板。
- **KR3**: 实现 "Context Injection" 与 "Auto-Startup"，支持自动运行预设命令 (e.g. `claude`, `gemini`) 并注入上下文，减少冷启动等待。
- **KR4**: 验证主流 CLI Agent 在 Web 终端中的交互流畅性。

## Scope

### Infrastructure (Toolkit)

- **WebSocket & PTY Manager**: 引入 `fastapi-websockets`，实现基于 Session ID 的多路复用 PTY 管理。
- **Auto-Startup Configuration**:
  - 支持配置 "Default Command" (如 `claude` 或 `monoco agent`)，在 Session 建立时自动执行。
  - 实现 "Pre-warming" 机制，让 Agent 进程提前就绪，通过 PTY 保持活跃，避免每次交互都重新握手/加载模型。
- **Security**: Localhost restrictive access.

### User Interface (Kanban)

- **Terminal Emulator**: `xterm.js` + `xterm-addon-fit` 集成.
- **Multi-Tab Interface**:
  - 支持并发管理多个 Terminal Session。
  - 区分 "Global Shell" (主控台) 和 "Task Shell" (任务专用)。
  - Tab 状态指示器 (Idle/Running/Error)。
- **Interaction**:
  - 底部状态栏 Toggle (HUD 风格)。
  - 全局快捷键 (`Cmd+J`) 唤出并聚焦。
  - Theme 自动同步 (Glassmorphism 背景)。

### Experience

- **Context Awareness**: 点击 Issue 上的 "Run" 时，自动创建新 Tab 并注入环境变量 (`export CURRENT_ISSUE=...`)。
- **Seamless Auth**: 确保 CLI Agent 的认证状态（如 OAuth Token）能持久化并在 PTY 中复用，避免重复登录。
