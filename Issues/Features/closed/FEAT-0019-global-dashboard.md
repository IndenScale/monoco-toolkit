---
id: FEAT-0019
type: feature
status: closed
stage: done
title: Global Dashboard
created_at: '2026-01-11T13:41:44.193793'
opened_at: '2026-01-11T13:41:44.193781'
updated_at: '2026-01-11T13:41:44.193794'
parent: EPIC-0002
dependencies: []
related: []
tags: []
---

## FEAT-0019: Global Dashboard

## 目标 (Objective)

实现项目级的全局仪表盘 (Dashboard)，作为用户的默认着陆页。
该页面旨在提供"上帝视角"，帮助用户快速掌握项目健康度、近期动态和关键瓶颈，而无需深入 Issue 列表。

## 验收标准 (Acceptance Criteria)

1.  **指标卡片 (Metric Cards)**:
    - 显示 **Total Backlog** (待办总数)。
    - 显示 **Completed This Week** (本周完成数)。
    - 显示 **Blocked Issues** (阻塞中数量)。
    - 显示 **Velocity Trend** (简单趋势图或升降指标)。
2.  **动态流 (Activity Feed)**:
    - 实时(或近实时)显示项目内的关键事件：Issue 创建/关闭/状态流转。
    - (可选) Git Commit 摘要 (如果已集成 VCS)。
3.  **快速操作 (Quick Actions)**:
    - 提供 "Create Issue" 快捷入口。
    - 提供 "Recent Projects" 切换入口。
4.  **后端支持**:
    - 新增 `GET /api/v1/stats/dashboard` 接口，聚合上述指标数据。

## 技术任务 (Technical Tasks)

- [x] **Backend API**: 实现 `monoco.daemon.features.stats` 模块及聚合接口。
    - **现状分析**: 当前 Daemon 仅提供 `list_projects`, `list_issues`, `get_board_data` 接口，无聚合 Stats API。
    - **实现方案**: 新增 `GET /api/v1/stats/dashboard`。
    - **Blocked 定义**: 暂定为 "存在未 Close 的前置依赖 (dependencies)" 的 Issue。
- [x] **Frontend State Management**: 重构前端状态管理 (Zustand)。
    - **Store 设计**: 在 `@monoco/kanban-core` 中扩展或新增 Store，统一管理 Project Stats 与 Issues。
        - `useDashboardStore`: 管理聚合指标 (Stats) 和动态 (Activity)。
        - `useKanbanStore`: 继续管理 Issue 列表数据。
    - **数据同步**: 升级 `useKanbanSync` Hook。
        - 监听 SSE (`issue_upserted`, `issue_deleted`)。
        - 当事件触发时，不仅更新 Issue List，同时触发 `dashboardStore.fetchStats()` 以保持聚合数据实时性。
- [x] **Frontend Layout**: 创建 Dashboard 页面布局 (Grid System)。
    - **现状分析**: `Kanban/apps/web/src/app/components/StatsBoard.tsx` 目前仅支持基于 BoardData 的客户端计算。
    - **迁移计划**: 重构 `StatsBoard` 组件，使其直接从 `useDashboardStore` 消费数据，移除 Props 传递。
- [x] **UI Components**: 实现 MetricCard, ActivityList 等展示组件。
- [x] **Data Integration**: 前后端联调，确保数据实时性。
    - **同步机制**: 复用现有的 SSE (`/api/v1/events`) 机制，当 Issue 变更时触发 Dashboard 刷新。 
