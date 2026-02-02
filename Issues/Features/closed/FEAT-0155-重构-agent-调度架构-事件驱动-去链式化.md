---
id: FEAT-0155
uid: e5d638
type: feature
status: closed
stage: done
title: 重构 Agent 调度架构：事件驱动 + 去链式化
created_at: '2026-02-02T20:29:43'
updated_at: '2026-02-02T20:42:54'
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
solution: implemented
opened_at: '2026-02-02T20:29:43'
closed_at: '2026-02-02T20:42:54'
isolation:
  type: branch
  ref: feat/feat-0155-重构-agent-调度架构-事件驱动-去链式化
  created_at: '2026-02-02T20:30:43'
---

## FEAT-0155: 重构 Agent 调度架构：事件驱动 + 去链式化

## Objective
重构当前的 `SchedulerService`，将其从轮询+硬编码的架构转变为事件驱动架构。
删除未使用的 Planner 角色，移除 Engineer→Reviewer 的自动链式触发，改为独立事件触发。

## Acceptance Criteria
- [x] 删除 Planner 角色（从配置和 SemaphoreManager 中移除）
- [x] 实现中央 EventBus 事件总线
- [x] 将 Architect/Engineer/Coroner 触发逻辑改造为事件处理器
- [x] 移除 Engineer→Reviewer 链式触发逻辑
- [x] Reviewer 改为独立触发（PR 创建或人工命令）
- [x] 所有事件处理器通过 EventBus 注册，而非硬编码

## Technical Tasks

### Phase 1: 清理与简化
- [x] 删除 Planner 角色引用（`AgentConcurrencyConfig`, `SemaphoreManager`）
- [x] 删除 `handle_completion()` 中的 Engineer→Reviewer 链式逻辑
- [x] 更新文档和配置定义

### Phase 2: 事件总线基础设施
- [x] 创建 `EventBus` 类（基于 asyncio）
- [x] 定义 `AgentEventType` 枚举（memo.created, issue.stage_changed, session.completed 等）
- [x] 实现事件订阅/发布机制

### Phase 3: 事件处理器重构
- [x] 创建 `AgentEventHandler` 基类
- [x] 创建 `ArchitectHandler`（订阅 MEMO_THRESHOLD 事件）
- [x] 创建 `EngineerHandler`（订阅 ISSUE_STAGE_CHANGED 事件）
- [x] 创建 `CoronerHandler`（订阅 SESSION_FAILED/CRASHED 事件）
- [x] 创建 `ReviewerHandler`（订阅 PR_CREATED 事件，人工触发）
- [x] 创建 `EventHandlerRegistry` 管理处理器注册

### Phase 4: 集成与测试
- [x] 更新 `SchedulerService` 使用 EventBus
- [x] 重构为事件驱动架构（保留轻量级轮询用于事件检测）
- [x] 添加 `get_stats()` 用于监控
- [x] 集成测试验证事件流转（基础验证通过，完整测试待后续）

## Review Comments

### 实现总结 (2026-02-02)

**架构变更**:
1. **删除 Planner 角色** - 从 `AgentConcurrencyConfig` 和 `SemaphoreManager` 中完全移除
2. **删除链式触发** - Engineer 完成后不再自动触发 Reviewer
3. **事件驱动架构** - 从轮询+硬编码改为 EventBus + Handler 模式

**新增组件**:
- `monoco/daemon/events.py` - EventBus 事件总线，支持异步发布/订阅
- `monoco/daemon/handlers.py` - 事件处理器基类和具体实现

**角色触发方式**:
| 角色 | 触发事件 | 说明 |
|------|----------|------|
| Architect | `MEMO_THRESHOLD` | Memo 积累达到阈值 |
| Engineer | `ISSUE_STAGE_CHANGED` | Issue 进入 doing 阶段 |
| Reviewer | `PR_CREATED` | PR 创建（人工/外部触发）|
| Coroner | `SESSION_FAILED/CRASHED` | Session 失败/崩溃 |

**4 角色确认**: Architect, Engineer, Reviewer (主工作流) + Coroner (诊断)
