---
id: FEAT-0061
uid: vsc003
type: feature
status: open
stage: doing
title: Interactive Context Actions (Go-to & File Linking)
created_at: "2026-01-14T14:05:00"
opened_at: "2026-01-14T14:05:00"
updated_at: "2026-01-14T14:05:00"
parent: EPIC-0011
dependencies:
  - FEAT-0059
related: []
tags:
  - vscode
  - interaction
---

## FEAT-0061: Interactive Context Actions (Go-to & File Linking)

## Objective

实现看板 Webview 与 VS Code 编辑器之间的深度联动，允许用户在看板中点击文件路径直接跳转到编辑器对应位置。

## Acceptance Criteria

- [ ] **双向通信协议**:
  - [ ] 定义 `OPEN_FILE` 消息格式，包含 `path`, `line`, `column`。
- [ ] **VS Code 侧响应**:
  - [ ] 插件进程接收消息后，使用 `vscode.window.showTextDocument` 打开文件并定位光标。
- [ ] **Kanban 侧交互**:
  - [ ] 在 Issue 详情页及活动流中，检测符合 `/path/to/file:line` 格式的文本并渲染为可点击链接。
  - [ ] 实现点击后的消息发送逻辑。

## Technical Tasks

- [ ] 实现 VS Code 端的 `FileOpener` 服务。
- [ ] 在 `Toolkit/Kanban` 中增加路径解析 Common Component。
