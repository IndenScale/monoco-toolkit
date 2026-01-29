---
id: FEAT-0077
type: feature
status: closed
stage: done
title: Migrate Cockpit View to Pure LSP Architecture
parent: EPIC-0005
solution: implemented
domains: []
tags:
- '#EPIC-0005'
- '#FEAT-0077'
---

## FEAT-0077: Migrate Cockpit View to Pure LSP Architecture

本特性旨在将 VS Code 扩展的 Cockpit (Kanban) 视图从当前的 Hybrid 架构（Webview <-> HTTP Daemon）迁移到 Pure LSP 架构（Webview <-> VS Code Client <-> LSP Server）。

## 1. 背景与目标 (Context & Objectives)

**当前痛点**:

- **运行时强依赖**: Cockpit 视图依赖 `monoco serve` 提供的 HTTP API 和 SSE 推送。一旦 Python 进程启动失败或未安装，视图将不可用或白屏。
- **状态不一致**: LSP Server (Node.js) 和 HTTP Daemon (Python) 各自维护一套内存索引，可能导致 IDE 智能提示与看板状态不一致。
- **交互限制**: 看板操作（如拖拽）通过 HTTP 调用 Python API 修改文件，导致 VS Code 无法感知文件变更，也无法通过 `Cmd+Z` 撤销操作。

**目标**:

1.  **移除运行时依赖**: 使 VS Code 扩展在没有 Python 环境的情况下也能提供完整的 Issue 管理和看板交互能力。
2.  **单一真实源**: 统一使用 LSP Server 的索引作为 Single Source of Truth。
3.  **编辑器原生体验**: 通过 LSP 通信，使看板操作转化为 `WorkspaceEdit`，获得原生的撤销/重做支持。

## 2. 详细设计 (Detailed Design)

### 2.1 架构变更

- **Before**:
  - Read: Webview -> fetch(HTTP) -> Python Daemon
  - Write: Webview -> fetch(HTTP) -> Python Daemon -> File System
  - Notify: Python Daemon -> SSE -> Webview
- **After**:
  - Read: Webview -> postMessage -> Client -> sendRequest -> **LSP Server**
  - Write: Webview -> postMessage -> Client -> sendRequest -> **LSP Server** -> **WorkspaceEdit** -> Editor
  - Notify: **LSP Server** -> sendNotification -> Client -> postMessage -> Webview

### 2.2 核心能力迁移

| 功能模块                | 当前实现 (HTTP Daemon)    | 目标实现 (LSP Node.js)                                                      |
| :---------------------- | :------------------------ | :-------------------------------------------------------------------------- |
| **全量数据获取**        | `GET /issues`             | 增强 `indexer.getAll()`，支持看板所需的过滤和层级构建。                     |
| **状态更新 (看板拖拽)** | `PATCH /issues/{id}`      | 在 LSP 端解析 Frontmatter，计算 Diff，返回 `WorkspaceEdit` 给 Client 应用。 |
| **配置读取 (Profiles)** | `GET /execution/profiles` | LSP Server 直接读取 `.monoco/config.yaml` 或 `launch.json`。                |
| **实时更新**            | SSE Stream                | 利用 LSP `connection.sendNotification` 实现双向通信。                       |

### 2.3 与 Monoco Server (HTTP) 的关系

**Monoco HTTP Server (Daemon) 依然保留**，但职责发生变更:

- **不再作为 VS Code 的后端**。
- **专用于**:
  - 独立 Web UI (Browser only access)。
  - 外部系统集成 (Webhooks, API Gateway)。
  - 需要 Python 完整运行时执行的高级任务（如复杂的数据分析或 Agent 编排）。

## 3. 验收标准 (Acceptance Criteria)

- [x] **Zero Python Dependency**: 在未安装 Python 或 `monoco` CLI 的环境中，VS Code 扩展能正常展示看板并进行拖拽操作。
- [x] **LSP Integration**: 所有看板数据均来自 LSP Server 的内存索引。
- [x] **Undo Support**: 在看板中拖拽 Issue 状态后，在 VS Code 中按 `Cmd+Z` 可以撤销该变更。
- [x] **Realtime Sync**: 在外部修改 `.md` 文件，看板应在 100ms 内自动刷新（通过 LSP `onDidChangeWatchedFiles` 触发通知）。

## Technical Tasks

- [x] **LSP Protocol Extension**: 定义用于看板通信的 LSP Custom Requests (e.g., `monoco/getAllIssues`, `monoco/updateIssue`).
- [x] **Server Implementation**:
  - [x] 实现 `monoco/getAllIssues` 处理程序。
  - [x] 实现 `monoco/updateIssue` 处理程序，返回 `WorkspaceEdit`。
  - [x] 实现 Config Watcher 和 Profile 解析。
- [x] **Client Refactor**:
  - [x] 移除 `MonocoAPI` (HTTP client)。
  - [x] 重写 `MonocoKanbanProvider` 以使用 `languageClient.sendRequest`。
  - [x] 桥接 LSP Notification 到 Webview `postMessage`。
- [x] **Cleanup**: 移除扩展中自动启动 Daemon 的逻辑。

## Review Comments

- [x] Self-Review
