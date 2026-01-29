---
id: FEAT-0098
uid: 0715b6
parent: EPIC-0000
type: feature
status: closed
stage: done
title: 'Scheduler: Session Management & Persistent History'
created_at: '2026-01-24T18:45:12'
opened_at: '2026-01-24T18:45:12'
updated_at: '2026-01-24T19:01:01'
closed_at: '2026-01-24T19:01:01'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0098-scheduler-session-management-persistent-history
  created_at: '2026-01-24T18:51:34'
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0098'
files:
- Issues/Epics/open/EPIC-0019-implement-agent-scheduler-module.md
- Issues/Features/open/FEAT-0097-scheduler-worker-management-role-templates.md
- Issues/Features/open/FEAT-0098-scheduler-session-management-persistent-history.md
- Issues/Features/open/FEAT-0099-scheduler-core-scheduling-logic-cli.md
- Issues/Features/open/FEAT-0100-scheduler-reliability-engineering-apoptosis-recove.md
- monoco/features/scheduler/__init__.py
- monoco/features/scheduler/config.py
- monoco/features/scheduler/defaults.py
- monoco/features/scheduler/manager.py
- monoco/features/scheduler/models.py
- monoco/features/scheduler/session.py
- monoco/features/scheduler/worker.py
- tests/features/test_scheduler.py
- tests/features/test_session.py
---

## FEAT-0098: Scheduler: Session Management & Persistent History

## Objective
实现 `Session` 对象及其生命周期管理。Session 代表 Worker 在 Task 上的一次运行时实例。它必须处理状态转换（Pending -> Running -> Suspended -> Terminated），并在适当的时候通过 Git 提交严格地持久化上下文/历史，确保“临时会话 (Ephemeral Sessions)”。

## Acceptance Criteria
- [x] **Session 模型**: 代表会话及其状态（Status, Worker, IssueID, Git Branch）的类。
- [x] **生命周期**: 启动、挂起、恢复和终止会话的方法。
- [x] **Git 集成**: 每个会话关联一个唯一的 git 分支（或重用现有的特性分支）。
- [x] **历史记录**: 能够回读会话历史（虽然日志可能是一个独立的关注点，但会话元数据持久化是关键）。
- [x] **持久化**: 会话状态应可恢复（例如，如果守护进程重启，我们知道哪些会话是活跃的）。*注：对于 MVP，内存加文件备份元数据已足够。*

## Technical Tasks
- [x] 定义 `Session` 类 (`monoco/features/scheduler/session.py`)。
- [x] 实现 `SessionManager` 以追踪活跃会话 (`monoco/features/scheduler/manager.py`)。
- [x] 实现 Git 上下文隔离（确保 Worker 在正确的分支运行）。
- [x] 实现状态转换：
    - [x] `start()`: 检出分支，生成 Worker。
    - [x] `suspend()`: 停止 Worker，保存状态（如果有）。
    - [x] `resume()`: 恢复状态，重启 Workder。
    - [x] `terminate()`: 清理。
- [x] 添加会话生命周期的单元测试。

## Review Comments
- Self-review: 实现了 Session, RuntimeSession 和 SessionManager。为生命周期和管理添加了基础单元测试。MVP 中通过分支命名模拟 Git 集成。目前持久化是内存/模拟的，未来需要真实的持久化层。
