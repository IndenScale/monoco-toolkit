---
id: FEAT-0056
type: feature
status: closed
stage: done
title: Implement monoco-pty Service via WebSockets
created_at: '2026-01-14T00:00:00'
updated_at: '2026-01-14T08:24:53'
closed_at: '2026-01-14T08:24:53'
parent: EPIC-0010
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0010'
- '#FEAT-0056'
- cli
- daemon
- pty
- websocket
owner: Backend Engineer
uid: '143695'
---

## FEAT-0056: Implement monoco-pty Service via WebSockets

# Feature: Implement monoco-pty Service

## Context

为了支持 EPIC-0010 "Agent Terminal Integration"，我们需要一个专门负责终端会话管理的服务。
根据架构决策，该服务将独立于 `monoco serve` 运行，通过独立的命令 `monoco pty` 启动，以保证系统的解耦与稳定性。

## Goals

1.  实现 `monoco.features.pty` 模块与 `monoco pty` CLI 命令。
2.  提供基于 WebSocket 的 PTY 流式接口。
3.  支持多 Session 管理与自动环境注入。

## Technical Design

### 1. Service Architecture

- **Entry Point**: `monoco pty` (Uvicorn running FastAPI/Starlette).
- **Port**: Default to `3124` (Distinct from main daemon).
- **State Sharing**: 启动时读取 `.monoco/state.json` (或通过参数) 确定 Workspace Root。

### 2. WebSocket Protocol

- **Endpoint**: `ws://localhost:3124/ws/{session_id}`
- **Handshake Params**:
  - `cols`, `rows`: Terminal dimensions.
  - `env`: JSON string identifying context (e.g., `{"CURRENT_ISSUE": "FEAT-123"}`).
  - `command`: (Optional) Auto-run command (e.g., `claude`).

### 3. PTY Manager Logic

- 使用 Python `pty` (Unix) 或 `pywinpty` (Windows) 库。
- **Session Lifecycle**:
  - Connection Open -> Spawn Process.
  - Process Exit -> Close Connection.
  - Connection Drop -> Kill Process (or configurable keep-alive).

## Tasks

- [x] **Core**: 创建 `monoco/features/pty/` 目录结构。
- [x] **Server**: 实现 `monoco pty` CLI 命令与 FastAPI App 初始化。
- [x] **Logic**: 实现 `PTYManager` 类，负责 spawn shell 和 IO forwarding。
- [x] **API**: 实现 WebSocket 路由与双向数据管道 (Input -> Stdin, Stdout -> Output)。
- [x] **Context**: 实现环境变量注入逻辑 (`env` param -> `subprocess.Popen(env=...)`)。
- [x] **Test**: 编写简单的 HTML/JS Client 验证连通性。

## Acceptance Criteria

- [x] 运行 `monoco pty` 后，可以通过 WebSocket 客户端连接并获得交互式 Shell。
- [x] 支持同时打开多个独立的 Shell Session。
- [x] 传递 `env={"TEST": "1"}` 时，在该 Shell 中执行 `echo $TEST` 输出 `1`。
- [x] 进程崩溃或退出时，WebSocket 连接正常关闭。

## Review Comments

- [x] Self-Review
