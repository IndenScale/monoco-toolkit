---
id: FEAT-0044
uid: e9c5b2
type: feature
status: open
stage: todo
title: Universal Webview 前端架构
created_at: "2026-01-13T10:17:59"
opened_at: "2026-01-13T10:17:59"
updated_at: "2026-01-13T12:22:00"
parent: EPIC-0006
dependencies: []
related: []
tags: []
---

## FEAT-0044: Universal Webview 前端架构

## Objective

确立 "Universal Webview" 前端架构，拒绝 Electron 重写，保持 Next.js 技术栈，通过 Adapter 模式适配 Web, VS Code (VSX) 和 Desktop。
核心原则：Monoco CLI (Python) 是唯一的大脑，UI 只是皮肤。

## Acceptance Criteria

- [ ] **架构验证**:
  - [ ] 确认 Next.js 静态导出 (Static Export) 方案可行。
  - [ ] 验证 Python 后端服务静态文件的能力。
- [ ] **VS Code 适配**:
  - [ ] 验证 React (Vite) + `vscode-webview-ui-toolkit` 在 VSX 环境下的通信机制 (`acquireVsCodeApi`)。
- [ ] **Desktop 适配**:
  - [ ] 验证使用 PyWebView 或 Tauri v2 作为轻量级外壳加载本地 Web 服务。

## Technical Tasks

- [ ] 制定 Web 与 CLI 的通信协议 (REST/RPC)。
- [ ] 创建 VS Code 插件原型，测试 WebView 加载 React 应用。
- [ ] 创建 PyWebView 启动脚本原型。
- [ ] 编写文档描述 "Dumb Terminal" 架构规范。
