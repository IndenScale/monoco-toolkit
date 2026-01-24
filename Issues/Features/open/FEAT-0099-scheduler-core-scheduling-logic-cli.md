---
id: FEAT-0099
uid: 6423d2
type: feature
status: open
stage: doing
title: 'Scheduler: Core Scheduling Logic & CLI'
created_at: '2026-01-24T18:45:12'
opened_at: '2026-01-24T18:45:12'
updated_at: 2026-01-24 18:54:55
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0099'
files: []
isolation:
  type: branch
  ref: feat/feat-0099-scheduler-core-scheduling-logic-cli
  path: null
  created_at: '2026-01-24T18:54:55'
---

## FEAT-0099: Scheduler: Core Scheduling Logic & CLI

## Objective
实现调度器的核心循环和 CLI 接口。调度器负责协调 Worker 和 Session 的创建与管理，而 CLI (`monoco agent`) 提供了用户与调度器交互的界面。这是用户操作代理的主要入口。

## Acceptance Criteria
- [ ] **CLI 实现**: 支持 `monoco agent run`, `list`, `logs`, `kill` 命令。
- [ ] **前台运行**: `run` 命令默认在当前终端前台运行 Agent 循环。
- [ ] **后台调度**: (可选/MVP后) 支持 `--detach` 模式提交给守护进程。
- [ ] **调度逻辑**: 能够根据 Issue ID 自动识别上下文并启动相应的 Worker。
- [ ] **状态展示**: `list` 命令清晰展示当前活跃的 Session 及其状态。

## Technical Tasks
- [ ] 实现 CLI 入口点 (`monoco/features/scheduler/cli.py`) 使用 Click 或现有 CLI 框架。
- [ ] 实现 `run` 命令逻辑：
    - 加载 Issue 元数据。
    - 确定 Role（默认或指定）。
    - 实例化 SessionManager 和 RuntimeSession。
    - 启动 Worker 循环（模拟循环：Think -> Act -> Observe）。
- [ ] 实现 `list` 命令：查询 SessionManager。
- [ ] 集成到 `monoco` 主 CLI 组中。

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
