---
id: FEAT-0097
uid: 73e66e
type: feature
status: open
stage: review
title: 'Scheduler: Worker Management & Role Templates'
created_at: '2026-01-24T18:45:11'
opened_at: '2026-01-24T18:45:11'
updated_at: '2026-01-24T18:50:53'
isolation:
  type: branch
  ref: feat/feat-0097-scheduler-worker-management-role-templates
  created_at: '2026-01-24T18:48:41'
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0097'
files: []
---

## FEAT-0097: Scheduler: Worker Management & Role Templates

## Objective
实现 Agent Scheduler 的基石：Worker 定义与 Role Templates。这允许系统定义具有特定触发器、目标和工具的不同类型 Agent（如 Crafter, Builder, Auditor），正如 `RFC/agent-scheduler-design.md` 所定义。

## Acceptance Criteria
- [x] **配置加载**: 支持从 `.monoco/scheduler.yaml` 加载角色配置。
- [x] **默认角色**: 如果缺少配置，则定义默认角色（Crafter, Builder, Auditor）。
- [x] **Worker 模型**: 在 Python 中实现 `Worker` 类 (`monoco.features.scheduler.worker`)，封装角色和运行时状态。
- [x] **验证**: 确保角色模板经过验证（工具必须存在，触发器必须有效）。

## Technical Tasks
- [x] 定义 `RoleTemplate` Pydantic 模型 (`monoco/features/scheduler/models.py`)。
- [x] 实现配置加载器，允许从 `.monoco/scheduler.yaml` 覆盖 (`monoco/features/scheduler/config.py`)。
- [x] 创建基于 `RoleTemplate` 实例化的 `Worker` 类 (`monoco/features/scheduler/worker.py`)。
- [x] 创建默认配置文件或常量。
- [x] 添加加载和 Worker 实例化的单元测试。

## Review Comments
- Self-review: 实现了核心模型、配置加载器和基础 Worker 类。测试已通过。准备评审。
