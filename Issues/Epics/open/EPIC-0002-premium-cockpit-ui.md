---
id: EPIC-0002
type: epic
status: open
stage: todo
title: Premium Cockpit UI
created_at: "2026-01-11T10:35:29.959257"
opened_at: "2026-01-11T10:35:29.959240"
updated_at: "2026-01-11T10:35:29.959259"
dependencies: []
related: []
tags: []
---

## EPIC-0002: Premium Cockpit UI

## Objective (目标)

打造一个现代、高效、具有 "Premium" 质感的项目管理驾驶舱。不仅仅是看板，而是提供全方位的项目洞察、工程视图和组件管理能力。支持多项目上下文切换，提供极致的用户体验。

## Core Features (核心功能)

### [[FEAT-0019]]: Global Dashboard (全局仪表盘)

- **Status**: Pending
- **Description**: 项目概览页，提供核心指标的高级视图。
- **Key Components**:
  - **Metric Cards**: 待办总数、本周完成、Block 数量、Velocity 趋势。
  - **Activity Feed**: 实时显示项目动态（Issue 更新、Git 提交）。
  - **Quick Actions**: 快速创建 Issue、跳转最近视图。
- **Dependencies**: Backend Stats API (需新增)。

### [[FEAT-0020]]: Engineering View (工程视图) - `/issues`

- **Status**: Pending
- **Description**: 高密度的 Issue 列表视图，专为工程师设计。
- **Key Components**:
  - **Data Grid**: 支持排序、筛选、列自定义的表格。
  - **Grouping**: 按状态、优先级、Assignee 分组。
  - **Bulk Actions**: 批量状态流转、归档。
  - **Keyboard Shortcuts**: 纯键盘操作支持。
- **Dependencies**: 现有 Issue API 已支持，需前端实现。

### [[FEAT-0021]]: Architecture/Components View (架构视图) - `/components`

- **Status**: Conceptual
- **Description**: 可视化展示项目的模块/组件结构。
- **Key Components**:
  - **Dependency Graph**: 组件依赖关系图。
  - **File Explorer**: 关联代码文件与 Issue。
- **Dependencies**: 需要后端提供文件/模块分析能力 (Complexity: High)。

### [[FEAT-0022]]: Enhanced Context Management (上下文增强)

- **Status**: In Progress (基础已完成)
- **Description**: 完善多项目切换体验。
- **Items**:
  - Project Selector UI (Done).
  - Project-specific Settings (Pending).
  - Recent Projects History (Pending).
  - Breadcrumbs Navigation (Pending).

### [[FEAT-0023]]: Premium UX Polish (视觉与交互打磨)

- **Status**: Ongoing
- **Items**:
  - **Glassmorphism**: 统一磨砂玻璃质感。
  - **Animations**: 页面切换、数据加载的平滑过渡。
  - **Dark Mode**: 深度优化的暗色模式（当前已是暗色，需优化对比度）。

## Dependencies & Blocking (依赖分析与阻塞关系)

1. **Project Abstraction (Completed)**: 是一切的基础，已完成。
2. **Backend Stats API**: 阻塞 `FEAT-01 (Dashboard)` 的完整实现。
3. **Component Analysis Service**: 阻塞 `FEAT-03 (Components)`。

## Roadmap (实施路线图)

1. **Phase 1: Foundation (Current)**

   - Project Context Implementation (Done).
   - Fix Broken Links (`/issues`, `/components`).
   - Implement **FEAT-02 (Engineering View)** immediately to providing a working alternative to Kanban.

2. **Phase 2: Insights**

   - Implement Backend Stats API.
   - Build **FEAT-01 (Dashboard)**.

3. **Phase 3: Advanced**
   - Research Component Analysis.
   - Implement **FEAT-03**.
