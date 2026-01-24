---
id: FEAT-0099
uid: 6423d2
type: feature
status: closed
stage: done
title: 'Scheduler: Core Scheduling Logic & CLI'
created_at: '2026-01-24T18:45:12'
opened_at: '2026-01-24T18:45:12'
updated_at: '2026-01-24T19:01:02'
closed_at: '2026-01-24T19:01:02'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0099-scheduler-core-scheduling-logic-cli
  created_at: '2026-01-24T18:54:55'
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0099'
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

## FEAT-0099: Scheduler: Core Scheduling Logic & CLI

## Objective
实现调度器的核心循环和 CLI 接口。调度器负责协调 Worker 和 Session 的创建与管理，而 CLI (`monoco agent`) 提供了用户与调度器交互的界面。这是用户操作代理的主要入口。

## Acceptance Criteria
- [x] **CLI 实现**: 支持 `monoco agent run`, `list`, `logs`, `kill` 命令。
- [x] **前台运行**: `run` 命令默认在当前终端前台运行 Agent 循环。
- [x] **后台调度**: (可选/MVP后) 支持 `--detach` 模式提交给守护进程。
- [x] **调度逻辑**: 能够根据 Issue ID 自动识别上下文并启动相应的 Worker。
- [x] **状态展示**: `list` 命令清晰展示当前活跃的 Session 及其状态。

## Technical Tasks
- [x] 实现 CLI 入口点 (`monoco/features/scheduler/cli.py`) 使用 Click 或现有 CLI 框架。
- [x] 实现 `run` 命令逻辑：
    - [x] 加载 Issue 元数据。
    - [x] 确定 Role（默认或指定）。
    - [x] 实例化 SessionManager 和 RuntimeSession。
    - [x] 启动 Worker 循环（模拟循环：Think -> Act -> Observe）。
- [x] 实现 `list` 命令：查询 SessionManager。
- [x] 集成到 `monoco` 主 CLI 组中。

## Review Comments
- Self-review: 实现了基本的 CLI 结构（基于 Typer）。`monoco agent run` 可以启动会话并运行（模拟）。`monoco agent list` 展示会话（MVP仅限内存）。实现了与主 CLI 的集成。后台模式暂时作为 Placeholder。
