---
id: FEAT-0036
type: feature
status: closed
stage: done
title: Advanced Kanban Filter
created_at: '2026-01-13T08:43:32.369535'
opened_at: '2026-01-13T08:43:32.369518'
updated_at: '2026-01-13T09:26:20.031330'
closed_at: '2026-01-13T09:26:20.031367'
solution: implemented
dependencies: []
related: []
tags: []
uid: e64f42
---

## FEAT-0036: Advanced Kanban Filter

## Objective

增强看板过滤功能，提供更强大且易用的搜索体验。包括调整 UI 位置以提高可访问性，并支持高级搜索语法以实现精确过滤。

## Acceptance Criteria

- [ ] **UI 位置**: 过滤器输入框从 Popover 移出，直接放置在概览页眉的 "New Issue" 按钮旁边。
- [ ] **高级语法**:
  - 支持普通项 (例如 `0001`): **Nice to have** (评分/可选)。
  - 支持包含项 (例如 `+0001`): 条目**必须包含**此词。
  - 支持排除项 (例如 `-feat`): 条目**必须不包含**此词。
  - 支持短语项 (例如 `"login error"`): 条目**必须包含**此短语。
  - 逻辑为隐式 `AND`。
- [ ] **全面范围**: 搜索适用于所有字段，包括：
  - ID
  - 标题 (Title)
  - 描述 (Description)
  - 标签 (Tags)
  - 依赖项 (Dependencies)
- [ ] **忽略大小写**: 所有匹配均不区分大小写。

## Technical Tasks

- [x] 移除 `overview/page.tsx` 中过滤器输入框外层的 `Popover` 组件。
- [x] 实现 `parseSearchQuery` 工具函数，将输入解析为 `positives` 和 `negatives`。
- [x] 更新 `overview/page.tsx` 中的过滤逻辑 `useMemo` hook:
  - 对 `issues` (包括任务和 Epics) 应用过滤。
  - 确保如果 Epic 本身匹配**或者**其任何子项匹配，该 Epic 均可见。
  - 检查所有相关字段 (`id`, `title`, `tags`, `dependencies`, `body` 等)。
