---
id: FEAT-0063
uid: b2cc31
type: feature
status: closed
stage: done
title: 优化 VS Code 扩展 UI
created_at: "2026-01-14T16:42:55"
opened_at: "2026-01-14T16:42:55"
updated_at: "2026-01-14T16:43:38"
closed_at: "2026-01-14T16:43:38"
solution: implemented
dependencies: []
related: []
tags: []
progress: 4/4
files_count: 0
---

## FEAT-0063: 优化 VS Code 扩展 UI

## 目标

优化工具包扩展 UI 以获得更好的用户体验，专注于美观性和可用性。

## 验收标准

1.  工具栏图标是抽象的、单线的，并且主题一致。
2.  "创建问题"和"设置"在专用视图（卡片）中使用完整表单而不是输入框。
3.  支持 API URL 的动态配置。

## 技术任务

- [x] 在 webview 中用抽象单线 SVG 替换表情符号。
- [x] 在 `index.html` 和 `main.js` 中实现多视图架构（首页、创建、设置）。
- [x] 为问题创建和设置实现原生 HTML 表单。
- [x] 更新扩展宿主（`extension.ts`）以支持 `OPEN_URL` 消息。

## Review Comments

- [x] Self review
