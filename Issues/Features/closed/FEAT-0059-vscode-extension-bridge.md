---
id: FEAT-0059
uid: vsc001
type: feature
status: closed
stage: done
title: VS Code Extension Scaffold & Webview Bridge
created_at: "2026-01-14T13:40:00"
opened_at: "2026-01-14T13:40:00"
updated_at: "2026-01-15T22:50:00"
solution: >
  Created the VS Code extension project structure.
  Implemented the WebviewProvider to host the Kanban app.
  Established the `VsCodeMessenger` bridge for bidirectional communication between the Webview and the Extension Host.
parent: EPIC-0011
dependencies:
  - FEAT-0044
related: []
tags:
  - vscode
  - infrastructure
---

## FEAT-0059: VS Code Extension Scaffold & Webview Bridge

## Objective

搭建 VS Code 插件的基础脚手架，并建立 Webview 与插件进程、插件进程与 Monoco CLI 之间的双向通信桥梁。

## Acceptance Criteria

- [x] **插件脚手架**:
  - [x] 初始化 VS Code Extension 项目 (TypeScript)。
  - [x] 配置 Activity Bar 图标与 Sidebar View 容器。
- [x] **Webview 桥接**:
  - [x] 实现基础的 `VsCodeMessenger` 类，封装 `postMessage` 调用。
  - [x] 在前端 Kanban 中集成消息监听器，能够响应来自插件的指令。
- [x] **CLI 唤起**:
  - [x] 插件能够自动探测并启动 `monoco serve`（如果尚未启动）。
  - [x] 插件能够通过 HTTP/WebSocket 与 Monoco Daemon 交互。

## Technical Tasks

- [x] 创建 `extensions/vscode` 目录。
- [x] 实现 VS Code 端的 `WebviewProvider`。
- [x] 制定 Webview 指令集定义 (e.g., `OPEN_FILE`, `GET_CONFIG`)。
