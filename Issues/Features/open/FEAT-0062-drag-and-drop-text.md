---
id: FEAT-0062
uid: vsc004
type: feature
status: open
stage: draft
title: Drag-and-Drop Workflow via Text/URL
created_at: "2026-01-14T14:07:00"
opened_at: "2026-01-14T14:07:00"
updated_at: "2026-01-14T14:07:00"
parent: EPIC-0011
dependencies:
  - FEAT-0059
related: []
tags:
  - vscode
  - interaction
  - ux
---

## FEAT-0062: Drag-and-Drop Workflow via Text/URL

## Objective

实现物理感十足的拖拽交互。用户可以将 Issue 卡片直接拖入终端或 Agent Bar，本质上是填充该 Issue 的标识符（URL 或 ID）。

## Acceptance Criteria

- [ ] **看板拖拽导出**:
  - [ ] 为 Issue 卡片配置 HTML5 Drag & Drop。
  - [ ] `dataTransfer` 设置为 Issue 的引用（如 `Issues/Features/open/FEAT-xxxx.md` 或自定义 URL）。
- [ ] **终端集成**:
  - [ ] 验证拖拽到原生终端时的粘贴行为（通常 VS Code 终端会自动粘贴 `text/plain` 内容）。
- [ ] **Agent Bar 适配**:
  - [ ] Agent Bar 的输入框应支持 `drop` 事件，自动填充拖入的 Issue 引用。

## Technical Tasks

- [ ] 在 Kanban 中实现 `DraggableIssue` 包装器。
- [ ] 确定拖拽内容的标准格式，确保 Agent 指令能够无缝解析。
