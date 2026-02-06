---
id: FEAT-0140
type: feature
status: closed
stage: done
solution: cancelled
title: Monoco Daemon Orchestrator
owner: IndenScale
parent: EPIC-0025
priority: high
created_at: '2026-02-01'
domains:
- AgentEmpowerment
tags:
- '#EPIC-0025'
- '#FEAT-0140'
- daemon
- orchestrator
- scheduler
---

## FEAT-0140: Monoco Daemon Orchestrator

> Implement the core Daemon Orchestration Layer as defined in EPIC-0025.

## 背景说明

本功能旨在实现 Monoco 守护进程编排层，负责管理代理生命周期和任务调度。守护进程需要从被动服务演进为主动编排器，监控输入源（如收件箱）、调度工作线程（工程师、架构师），并处理故障情况（验尸分析）。该编排层是 Monoco 作为"智能体操作系统发行版"的核心组件，确保代理会话的高效管理和资源分配。

## Context
The Monoco Daemon needs to evolve from a passive service to an active orchestrator that manages the lifecycle of Agents ("Kernel Workers"). This involves monitoring inputs (Inbox), scheduling workers (Engineers, Architects), and handling failures (Autopsy).

## Goals
- **Inbox Watcher**: Monitor `Memos/inbox.md` and trigger Architect when content accumulates.
- **Agent Scheduler**: Manage lifecycle of Agent Sessions (spawn, monitor, kill).
- **Autopsy Protocol**: Automatically analyze failed sessions.
- **Feedback Loop**: Chain execution (Engineer -> Reviewer).

## Implementation Plan
1.  **Enhance Scheduler**: Update `monoco/daemon/scheduler.py` to support more robust polling and state management.
2.  **Implement Policies**: Refine `MemoAccumulationPolicy` and add triggers for other states.
3.  **Refine Apoptosis**: Update `monoco/features/agent/apoptosis.py` to pass context to the Coroner agent.
4.  **Integration**: Ensure `monoco/daemon/app.py` correctly starts and exposes the orchestrator.

## Technical Tasks
- [x] Refactor `SchedulerService` for better extensibility. (已整合到 EPIC-0025)
- [x] Implement `check_inbox_trigger` in Scheduler. (已整合到 EPIC-0025)
- [x] Implement `check_handover_trigger` in Scheduler. (已整合到 EPIC-0025)
- [x] Enhance `ApoptosisManager` to provide context. (已整合到 EPIC-0025)
- [x] Add unit tests for Scheduler logic. (已整合到 EPIC-0025)

## Review Comments

### 2026-02-02 整合结论

**决定**: 此 Feature 内容已整合到 EPIC-0025，标记为 cancelled 并关闭。

**理由**:
- FEAT-0140 是 EPIC-0025 "Monoco Daemon Orchestrator" 的具体实现
- 内容已合并到 EPIC-0025 Phase 3 (Daemon Core) 的技术任务中
- 避免 Epic 与 Feature 之间的重复跟踪

**整合内容**:
- Inbox Watcher: 监控 Memos/inbox.md 并触发 Architect
- Agent Scheduler: 管理 Agent Sessions 生命周期 (spawn, monitor, kill)
- Autopsy Protocol: 自动分析失败会话
- Feedback Loop: 链式执行 (Engineer -> Reviewer)
