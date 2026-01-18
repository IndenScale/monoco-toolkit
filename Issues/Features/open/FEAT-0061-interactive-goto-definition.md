---
id: FEAT-0061
uid: vsc003
type: feature
status: open
stage: backlog
title: Cockpit Navigation Bridge (Webview to Editor)
created_at: '2026-01-14T14:05:00'
opened_at: '2026-01-14T14:05:00'
updated_at: '2026-01-18T08:53:00'
parent: EPIC-0011
dependencies:
- FEAT-0059
related: []
tags:
- '#EPIC-0011'
- '#FEAT-0059'
- '#FEAT-0061'
- interaction
- vscode
---

## FEAT-0061: Cockpit Navigation Bridge (Webview to Editor)

## Objective (目标)

建立看板 Cockpit (Webview) 与 VS Code 编辑器之间的导航桥梁。当用户在看板详情、活动流或 Agent 报告中看到文件路径时，可以一键跳转到编辑器指定位置。

_注：编辑器源代码内的跳转已由 LSP (FEAT-0076) 覆盖，本 Feature 专注于跨环境（Webview -> Editor）通信。_

## Acceptance Criteria (验收标准)

- [ ] **跨环境通信协议**:
  - [ ] 在 `shared/constants/MessageTypes.ts` 中标准化 `OPEN_FILE` 消息。
  - [ ] 协议需支持 `path` (相对/绝对), `line`, `column` 参数。
- [ ] **VS Code 扩展端逻辑**:
  - [ ] 在 `KanbanProvider.ts` 或专门的服务中实现 `handleOpenFile`。
  - [ ] 支持打开非 Markdown 文件并精确定位光标。
- [ ] **Cockpit 端渲染 (依赖于 UI 详情页实现)**:
  - [ ] 在 Webview 的 Markdown 渲染层集成路径检测逻辑（检测 `path/to/file:line` 模式）。
  - [ ] 点击检测到的路径时，通过 `VSCodeBridge` 发送跳转指令。

## Technical Tasks (技术任务)

- [ ] 标准化消息类型定义。
- [ ] 在扩展端实现带有行号定位功能的 `FileOpener` 服务。
- [ ] (待详情页 UI 确认后) 在 Webview 组件中实现路径链接化处理器。
