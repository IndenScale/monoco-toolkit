---
id: FEAT-0029
parent: EPIC-0000
type: feature
status: closed
stage: done
title: Web 看板实现 (Web Kanban Implementation)
created_at: '2026-01-10T21:21:08.666551'
opened_at: '2026-01-10T21:21:08.666551'
updated_at: '2026-01-10T21:34:06.593250'
closed_at: '2026-01-10T21:34:06.593293'
solution: implemented
dependencies: []
related:
- EPIC-0003
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0003'
- '#FEAT-0029'
uid: a8bcfe
---

## FEAT-0029: Web 看板实现 (Web Kanban Implementation)

## 目标 (Objective)

实现一个只读的、基于 Web 的看板，用于可视化 Monoco Issues。架构实现前端 (Next.js) 与后端 (Monoco Daemon) 解耦，通过 REST API 进行通信。

## 验收标准 (Acceptance Criteria)

1.  **后端 API (Backend API)**: `monoco serve` 必须暴露 `/api/v1/board` 端点，返回按阶段 (Todo/Doing/Review/Done) 分组的 Issues。
2.  **前端 UI (Frontend UI)**: 一个 Next.js 应用（`Kanban` Monorepo 的一部分），用于获取并渲染看板。
3.  **实时性 (Real-time)**: 看板应自动刷新（轮询）以反映 CLI 所做的更改。

## 技术任务 (Technical Tasks)

- [x] **后端**: 在 `core.py` 中实现 `get_board_data`。
- [x] **后端**: 在 `daemon/app.py` 中暴露 `GET /api/v1/board`。
- [x] **前端**: 在 `apps/web/src/app/page.tsx` 中创建 `KanbanBoard` 组件。
- [x] **集成**: 连接前端到 Daemon (端口 8642)。

## Review Comments

- [x] Self-Review
