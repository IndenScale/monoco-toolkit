---
id: EPIC-0012
uid: 1c7c3e
type: epic
status: closed
stage: done
title: 在 VS Code 扩展中启用代理执行
created_at: '2026-01-15T08:55:46'
opened_at: '2026-01-15T08:55:46'
updated_at: '2026-01-19T14:31:49'
closed_at: '2026-01-19T14:31:49'
solution: cancelled
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0012'
files: []
progress: 3/3
files_count: 0
---

## EPIC-0012: 在 VS Code 扩展中启用代理执行

## 目标

使用户能够直接从 VS Code 执行 Monoco 代理配置文件（定义在 `.monoco/execution/SOP.md` 中）。
通过 LSP 识别可用配置文件，并使用可视化界面（代理栏）触发它们。

## 验收标准

- [x] **配置文件发现**: LSP 服务器扫描并返回所有可用的执行配置文件。(Feature Cancelled)
- [x] **代理栏 UI**: 在 VS Code 中有一个专用视图来列出配置文件。(Feature Cancelled)
- [x] **执行**: 单击配置文件会在 VS Code 终端中触发相应的命令。(Feature Cancelled)

## Technical Tasks

- [x] **LSP 服务器**: 实现 `monoco/getExecutionProfiles` 请求处理程序。
- [x] **VS Code 客户端**: 实现 `AgentSidebarProvider` 来渲染配置文件列表。(Cancelled)
- [x] **VS Code 客户端**: 实现 `monoco.runProfile` 命令。(Cancelled)

## Review Comments

- 该特性已被取消。Monoco 的策略目前专注于本地原生执行，暂缓在 VS Code 中直接执行代理的集成，以减少交互复杂性。
