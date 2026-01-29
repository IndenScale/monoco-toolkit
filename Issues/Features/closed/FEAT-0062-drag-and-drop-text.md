---
id: FEAT-0062
uid: vsc004
type: feature
status: closed
stage: done
title: Drag-and-Drop Workflow via Text/URL
created_at: "2026-01-14T14:07:00"
opened_at: "2026-01-14T14:07:00"
updated_at: "2026-01-19T14:32:00"
solution: implemented
parent: EPIC-0011
dependencies:
  - FEAT-0059
related: []
domains: []
tags:
  - "#EPIC-0011"
  - "#FEAT-0059"
  - "#FEAT-0062"
  - interaction
  - ux
  - vscode
---

## FEAT-0062: Drag-and-Drop Workflow via Text/URL

## Objective

实现物理感十足的拖拽交互。用户可以将 Issue 卡片直接拖入终端或 Agent Bar，本质上是填充该 Issue 的标识符（URL 或 ID）。

## Acceptance Criteria

- [x] **看板拖拽导出**:
  - [x] 为 Issue 卡片配置 HTML5 Drag & Drop。
  - [x] `dataTransfer` 设置为 Issue 的引用（如 `Issues/Features/open/FEAT-xxxx.md` 或自定义 URL）。
- [x] **终端集成**:
  - [x] 验证拖拽到原生终端时的粘贴行为（通常 VS Code 终端会自动粘贴 `text/plain` 内容）。
- [x] **Agent Bar 适配**:
  - [x] Agent Bar 的输入框应支持 `drop` 事件，自动填充拖入的 Issue 引用。

## Solution

实现了完善的拖拽交互支持：

1. `KanbanCard.tsx` 和 `main.js` 均已实现 `draggable` 协议，向 `dataTransfer` 注入 `text/uri-list` (file URI) 和 `text/plain` (Issue ID/Path)。
2. 支持直接将 Issue 拖入 VS Code 终端、编辑器或其他支持标准拖拽的组件。
3. `application/monoco-issue` 格式已标准化，方便未来扩展复杂的内部拖拽逻辑。

## Review Comments

- [x] 终端粘贴功能正常。
- [x] URI 解析逻辑已覆盖多平台路径。

## Technical Tasks

- [x] 在 Kanban 中实现 `DraggableIssue` 包装器。
- [x] 确定拖拽内容的标准格式，确保 Agent 指令能够无缝解析。

```

```
