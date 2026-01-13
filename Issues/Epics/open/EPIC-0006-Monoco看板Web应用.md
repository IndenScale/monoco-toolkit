```
---
id: EPIC-0006
type: epic
status: open
stage: doing
title: Monoco 看板 Web 应用 (Monoco Kanban Web App)
created_at: '2026-01-11T10:35:29.959257'
opened_at: '2026-01-11T10:35:29.959240'
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

### [[FEAT-0021]]: 架构/组件视图 (Architecture/Components View) - `/components`

- **状态 (Status)**: Conceptual
- **描述 (Description)**: 可视化展示项目的模块/组件结构。
- **关键组件 (Key Components)**:
  - **依赖图 (Dependency Graph)**: 组件依赖关系图。
  - **文件资源管理器 (File Explorer)**: 关联代码文件与 Issue。
- **依赖 (Dependencies)**: 需要后端提供文件/模块分析能力 (复杂度: 高)。

### [[FEAT-0022]]: 增强上下文管理 (Enhanced Context Management)

- **状态 (Status)**: In Progress (基础已完成)
- **描述 (Description)**: 完善多项目切换体验。
- **项目 (Items)**:
  - 项目选择器 UI (Done).
  - 项目特定设置 (Pending).
  - 最近项目历史 (Pending).
  - 面包屑导航 (Pending).

### [[FEAT-0023]]: 高级 UX 打磨 (Premium UX Polish)

- **状态 (Status)**: Ongoing
- **项目 (Items)**:
  - **玻璃拟态 (Glassmorphism)**: 统一磨砂玻璃质感。
  - **动画 (Animations)**: 页面切换、数据加载的平滑过渡。
  - **暗色模式 (Dark Mode)**: 深度优化的暗色模式（当前已是暗色，需优化对比度）。

## 依赖与阻塞 (Dependencies & Blocking)

1. **项目抽象 (Project Abstraction) (Completed)**: 是一切的基础，已完成。
2. **后端统计 API (Backend Stats API)**: 阻塞 `FEAT-01 (Dashboard)` 的完整实现。
3. **组件分析服务 (Component Analysis Service)**: 阻塞 `FEAT-03 (Components)`。

## 路线图 (Roadmap)

1. **阶段 1: 基础 (Foundation) (Current)**

   - 项目上下文实现 (Done).
   - 修复断链 (`/issues`, `/components`).
   - 立即实现 **FEAT-02 (工程视图)**，提供看板之外的可行替代方案。

2. **阶段 2: 洞察 (Insights)**

   - 实现后端统计 API。
   - 构建 **FEAT-01 (仪表盘)**。

3. **阶段 3: 高级 (Advanced)**
   - 研究组件分析。
   - 实现 **FEAT-03**。
```
