---
id: FEAT-0155
uid: e5d638
type: feature
status: open
stage: doing
title: 重构 Agent 调度架构：事件驱动 + 去链式化
created_at: '2026-02-02T20:29:43'
updated_at: 2026-02-02 20:30:43
parent: EPIC-0025
dependencies: []
related: []
domains:
- AgentEmpowerment
tags:
- '#EPIC-0025'
- '#FEAT-0155'
files: []
criticality: medium
solution: null
opened_at: '2026-02-02T20:29:43'
isolation:
  type: branch
  ref: feat/feat-0155-重构-agent-调度架构-事件驱动-去链式化
  path: null
  created_at: '2026-02-02T20:30:43'
---

## FEAT-0155: 重构 Agent 调度架构：事件驱动 + 去链式化

## Objective
重构当前的 `SchedulerService`，将其从轮询+硬编码的架构转变为事件驱动架构。
删除未使用的 Planner 角色，移除 Engineer→Reviewer 的自动链式触发，改为独立事件触发。

## Acceptance Criteria
- [ ] 删除 Planner 角色（从配置和 SemaphoreManager 中移除）
- [ ] 实现中央 EventBus 事件总线
- [ ] 将 Architect/Engineer/Coroner 触发逻辑改造为事件处理器
- [ ] 移除 Engineer→Reviewer 链式触发逻辑
- [ ] Reviewer 改为独立触发（PR 创建或人工命令）
- [ ] 所有事件处理器通过 EventBus 注册，而非硬编码

## Technical Tasks

### Phase 1: 清理与简化
- [ ] 删除 Planner 角色引用（`AgentConcurrencyConfig`, `SemaphoreManager`）
- [ ] 删除 `handle_completion()` 中的 Engineer→Reviewer 链式逻辑
- [ ] 更新文档和配置定义

### Phase 2: 事件总线基础设施
- [ ] 创建 `EventBus` 类（基于 asyncio）
- [ ] 定义 `AgentEvent` 枚举（memo.created, issue.stage_changed, session.completed 等）
- [ ] 实现事件订阅/发布机制

### Phase 3: 事件处理器重构
- [ ] 创建 `AgentEventHandler` 基类
- [ ] 重构 `ArchitectHandler`（订阅 memo.threshold 事件）
- [ ] 重构 `EngineerHandler`（订阅 issue.stage_changed 事件）
- [ ] 重构 `CoronerHandler`（订阅 session.failed 事件）
- [ ] 保留 `ReviewerHandler` 但不自动订阅（人工触发）

### Phase 4: 集成与测试
- [ ] 更新 `SchedulerService` 使用 EventBus
- [ ] 移除轮询 `monitor_loop`，改为事件驱动
- [ ] 集成测试验证事件流转

## Review Comments
