---
id: FEAT-0015
type: feature
status: closed
stage: done
title: 看板 UI 增强 (Kanban UI Enhancements)
created_at: '2026-01-11T12:02:00.818615'
opened_at: '2026-01-11T12:02:00.818600'
updated_at: '2026-01-11T13:20:50.734671'
closed_at: '2026-01-11T13:20:50.734702'
solution: implemented
dependencies: []
related: []
tags: []
parent: EPIC-0003
uid: 78a1a1
---

## FEAT-0015: 看板 UI 增强

## 目标 (Objective)

通过优化“概览”结构和引入“Issue 详情模态框”来增强看板体验。这改善了视觉层次结构，允许无需页面跳转即可快速访问上下文。

## 验收标准 (Acceptance Criteria)

1.  **可折叠统计组件 (Collapsible Stats Component)**:
    - 将统计小部件分离为独立的 `StatsBoard` 组件。
    - 用户可以切换（展开/折叠）此部分以节省垂直空间。
    - 状态被持久化（目前可选，但体验更好）。
2.  **Issue 详情模态框 (Issue Detail Modal)** (UI):
    - 点击 Issue 卡片会打开模态覆盖层，而不是跳转离开（或并排显示）。
    - 模态框显示格式化的 Markdown 内容 (预览)。
    - 模态框包含一个“编辑”按钮，可切换到原始 Markdown 编辑器 (Textarea/Monaco)。
    - 存在“保存”按钮，但实现是存根（委托给 FEAT-0016）。

## 技术任务 (Technical Tasks)

- [x] **重构统计**: 将小部件从 `page.tsx` 提取到 `components/StatsBoard.tsx`。
- [x] **实现模态框**: 使用 Blueprint `Dialog` 创建 `IssueDetailModal.tsx`。
- [x] **Markdown 渲染**: 集成 `react-markdown` 或类似库以在模态框中渲染 Issue 正文。
- [x] **编辑器 UI**: 为“编辑”模式添加简单的 textarea/编辑器视图。