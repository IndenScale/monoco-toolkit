---
id: EPIC-0012
uid: 1c7c3e
type: epic
status: open
stage: doing
title: 在 VS Code 扩展中启用代理执行
created_at: '2026-01-15T08:55:46'
opened_at: '2026-01-15T08:55:46'
updated_at: '2026-01-15T08:55:46'
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0012'
progress: 3/3
files_count: 0
---

## EPIC-0012: 在 VS Code 扩展中启用代理执行

## 目标

使用户能够直接从 VS Code 执行 Monoco 代理配置文件（定义在 `.monoco/execution/SOP.md` 中）。
通过 LSP 识别可用配置文件，并使用可视化界面（代理栏）触发它们。

## 验收标准

- [ ] **配置文件发现**: LSP 服务器扫描并返回所有可用的执行配置文件。
- [ ] **代理栏 UI**: 在 VS Code 中有一个专用视图来列出配置文件。
- [ ] **执行**: 单击配置文件会在 VS Code 终端中触发相应的命令。

## Technical Tasks

- [x] **LSP 服务器**: 实现 `monoco/getExecutionProfiles` 请求处理程序。
- [ ] **VS Code 客户端**: 实现 `AgentSidebarProvider` 来渲染配置文件列表。
- [ ] **VS Code 客户端**: 实现 `monoco.runProfile` 命令。
