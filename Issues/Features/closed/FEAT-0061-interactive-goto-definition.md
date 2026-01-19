---
id: FEAT-0061
uid: vsc003
type: feature
status: closed
stage: done
title: Cockpit Navigation Bridge (Webview to Editor)
created_at: "2026-01-14T14:05:00"
opened_at: "2026-01-14T14:05:00"
updated_at: "2026-01-19T14:32:00"
solution: Implemented
parent: EPIC-0011
dependencies:
  - FEAT-0059
related: []
domains: []
tags:
  - "#EPIC-0011"
  - "#FEAT-0059"
  - "#FEAT-0061"
  - interaction
  - vscode
---

## FEAT-0061: Cockpit Navigation Bridge (Webview to Editor)

## Objective (目标)

建立看板 Cockpit (Webview) 与 VS Code 编辑器之间的导航桥梁。当用户在看板详情、活动流或 Agent 报告中看到文件路径时，可以一键跳转到编辑器指定位置。

_注：编辑器源代码内的跳转已由 LSP (FEAT-0076) 覆盖，本 Feature 专注于跨环境（Webview -> Editor）通信。_

## Acceptance Criteria (验收标准)

- [x] **跨环境通信协议**:
  - [x] 在 `shared/constants/MessageTypes.ts` 中标准化 `OPEN_FILE` 消息。
  - [x] 协议需支持 `path` (相对/绝对), `line`, `column` 参数。
- [x] **VS Code 扩展端逻辑**:
  - [x] 在 `KanbanProvider.ts` 或专门的服务中实现 `handleOpenFile`。
  - [x] 支持打开非 Markdown 文件并精确定位光标。
- [x] **Cockpit 端渲染 (依赖于 UI 详情页实现)**:
  - [x] 在 Webview 的 Markdown 渲染层集成路径检测逻辑（检测 `path/to/file:line` 模式）。
  - [x] 点击检测到的路径时，通过 `VSCodeBridge` 发送跳转指令。

## Solution

实现了从看板 Webview 到编辑器的跳转功能。

1. 在 `MessageTypes.ts` 中新增 `OPEN_FILE` 协议。
2. 在 `KanbanProvider.ts` 中实现了 `handleOpenFile`，支持 `line` 和 `column` 解析与视图定位。
3. `IssueMarkdown.tsx` 组件已集成路径点击监听，支持 `path/to/file:line` 的高亮与跳转。

## Review Comments

- [x] 跳转逻辑与 LSP 行号对齐。
- [x] 跨环境通信协议标准化。

## Technical Tasks (技术任务)

- [x] 标准化消息类型定义。
- [x] 在扩展端实现带有行号定位功能的 `FileOpener` 服务。
- [x] (待详情页 UI 确认后) 在 Webview 组件中实现路径链接化处理器。
