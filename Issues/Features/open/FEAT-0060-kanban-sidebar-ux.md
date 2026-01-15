---
id: FEAT-0060
uid: vsc002
type: feature
status: open
stage: draft
title: Kanban Sidebar UX Optimization
created_at: "2026-01-14T13:42:00"
opened_at: "2026-01-14T13:42:00"
updated_at: "2026-01-14T13:42:00"
parent: EPIC-0011
dependencies:
  - FEAT-0044
  - FEAT-0059
related: []
tags:
  - vscode
  - ui
  - ux
---

## FEAT-0060: Kanban Sidebar UX Optimization

## Objective

针对 VS Code 侧边栏 (Sidebar) 的狭窄宽度进行 UI/UX 专项优化，确保看板在小尺寸下依然可用且美观。

## Acceptance Criteria

- [ ] **自适应布局**:
  - [ ] 实现 "Sidebar Mode" 媒体查询，在宽度极小时自动隐藏非核心列。
  - [ ] 优化侧边栏下的导航栏（转为底部 Tab 或 汉堡菜单）。
- [ ] **高密度视图**:
  - [ ] Issue 列表支持“紧凑模式”。
  - [ ] 优化字体大小与间距，确保 VS Code 风格的视觉一致性。
- [ ] **主题同步**:
  - [ ] 自动检测并匹配 VS Code 的当前主题颜色（背景、前景、Accent Color）。

## Technical Tasks

- [ ] 在 `PageHeader` 中集成侧边栏探测逻辑。
- [ ] 为 `IssueCard` 增加 `compact` 变体。
- [ ] 编写 CSS 变量映射层，对接 VS Code 的 `--vscode-*` CSS 变量。
