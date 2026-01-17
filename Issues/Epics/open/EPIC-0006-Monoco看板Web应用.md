```
---
id: EPIC-0006
type: epic
status: open
stage: doing
title: Monoco 看板 Web 应用 (Monoco Kanban Web App)
created_at: '2026-01-11T10:35:29.959257'
opened_at: '2026-01-11T10:35:29.959257'
updated_at: '2026-01-11T10:35:29.959259'
dependencies:
- EPIC-0002
- EPIC-0005
related: []
tags:
- frontend
- visualization
- ux
progress: 1/4
files_count: 0
uid: b7c0c7
---

## EPIC-0006: Monoco 看板 Web 应用 (Monoco Kanban Web App)

## 目标 (Objective)

打造一个现代、高效、具有 "Premium" 质感的项目管理 **Web 前端**。
本 Epic 关注 **UI/UX 体验与可视化**，消费由 EPIC-0003 提供的核心 API，提供全方位的项目洞察。不仅仅是看板，更是提供组件管理与架构视图的驾驶舱。

## 核心功能 (Core Features)

### [[FEAT-0019]]: 全局仪表盘 (Global Dashboard)

- **状态 (Status)**: Pending
- **描述 (Description)**: 项目概览页，提供核心指标的高级视图。
- **关键组件 (Key Components)**:
  - **指标卡片 (Metric Cards)**: 待办总数、本周完成、Block 数量、速率趋势。
  - **活动流 (Activity Feed)**: 实时显示项目动态（Issue 更新、Git 提交）。
  - **快速操作 (Quick Actions)**: 快速创建 Issue、跳转最近视图。
- **依赖 (Dependencies)**: Backend Stats API (需新增)。

### [[FEAT-0020]]: 工程视图 (Engineering View) - `/issues`

- **状态 (Status)**: Pending
- **描述 (Description)**: 高密度的 Issue 列表视图，专为工程师设计。
- **关键组件 (Key Components)**:
  - **数据网格 (Data Grid)**: 支持排序、筛选、列自定义的表格。
  - **分组 (Grouping)**: 按状态、优先级、负责人分组。
  - **批量操作 (Bulk Actions)**: 批量状态流转、归档。
  - **键盘快捷键 (Keyboard Shortcuts)**: 纯键盘操作支持。
- **依赖 (Dependencies)**: 现有 Issue API 已支持，需前端实现。


## Acceptance Criteria

- [ ] Global Dashboard implemented.
- [ ] Engineering View implemented.

## Technical Tasks

- [ ] Setup Next.js project.
- [ ] Integrate with Daemon API.

## Review Comments```
