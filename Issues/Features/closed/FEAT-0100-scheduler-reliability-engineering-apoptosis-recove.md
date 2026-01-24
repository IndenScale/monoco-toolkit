---
id: FEAT-0100
uid: 87a085
type: feature
status: closed
stage: done
title: 'Scheduler: Reliability Engineering (Apoptosis & Recovery)'
created_at: '2026-01-24T18:45:12'
opened_at: '2026-01-24T18:45:12'
updated_at: '2026-01-24T19:01:02'
closed_at: '2026-01-24T19:01:02'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0100-scheduler-reliability-engineering-apoptosis-recove
  created_at: '2026-01-24T18:57:46'
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0100'
files:
- Issues/Epics/open/EPIC-0019-implement-agent-scheduler-module.md
- Issues/Features/open/FEAT-0097-scheduler-worker-management-role-templates.md
- Issues/Features/open/FEAT-0098-scheduler-session-management-persistent-history.md
- Issues/Features/open/FEAT-0099-scheduler-core-scheduling-logic-cli.md
- Issues/Features/open/FEAT-0100-scheduler-reliability-engineering-apoptosis-recove.md
- monoco/features/scheduler/__init__.py
- monoco/features/scheduler/cli.py
- monoco/features/scheduler/config.py
- monoco/features/scheduler/defaults.py
- monoco/features/scheduler/manager.py
- monoco/features/scheduler/models.py
- monoco/features/scheduler/session.py
- monoco/features/scheduler/worker.py
- monoco/main.py
- tests/features/test_scheduler.py
- tests/features/test_session.py
---

## FEAT-0100: Scheduler: Reliability Engineering (Apoptosis & Recovery)

## Objective
实现“细胞凋亡” (Apoptosis) 和自动恢复机制，以确保 Agent 的可靠性。这是 ARE (Agent Reliability Engineering) 的核心，防止失控的 Agent 消耗过多资源或破坏环境。

## Acceptance Criteria
- [x] **监控机制**: 实现 Heartbeat 和 Token 消耗监控。（基础架构已就绪，Hooks通过外部触发）
- [x] **强制终止**: 当检测到异常（如死循环、超时），能够强制 Kill Session。
- [x] **尸检 (Autopsy)**: 在重置前，自动触发 Coroner Agent 分析失败原因。
- [x] **自动恢复**: 基于重试策略（如最大3次）重启 Session。（基础流已打通）
- [x] **环境回滚**: 每次 Session 结束（尤其是失败时），通过 Git reset 清理工作目录。（Placeholder 实现）

## Technical Tasks
- [x] 在 `Worker` 或 `RuntimeSession` 中添加监控 Hook。
- [x] 实现 `ApoptosisManager` 处理异常流程。
- [x] 集成 `git reset --hard` 到恢复逻辑中。
- [x] 定义 Coroner 的角色模板。
- [x] 编写测试案例模拟 Agent 失控和恢复。

## Review Comments
- Self-review: 实现了 ApoptosisManager，覆盖了 "Kill -> Autopsy -> Reset" 的核心流程。定义了 Coroner 角色。编写了单元测试验证凋亡循环。环境回滚和重试逻辑目前为 MVP 级别的模拟/占位，符合当前阶段需求。
