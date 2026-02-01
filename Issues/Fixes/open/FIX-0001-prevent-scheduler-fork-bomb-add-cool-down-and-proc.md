---
id: FIX-0001
uid: 982d61
type: fix
status: open
stage: review
title: 'Prevent Scheduler Fork Bomb: Add Cool-down and Process Limit to Handover Policy'
created_at: '2026-02-01T21:21:20'
updated_at: '2026-02-01T21:31:52'
parent: EPIC-0025
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0025'
- '#FIX-0001'
files:
- monoco/core/config.py
- monoco/daemon/services.py
- monoco/daemon/commands.py
- monoco/daemon/scheduler.py
- tests/daemon/test_semaphore_manager.py
criticality: high
opened_at: '2026-02-01T21:21:20'
---

## FIX-0001: Prevent Scheduler Fork Bomb: Add Cool-down and Process Limit to Handover Policy

## Objective
修复 `Daemon Scheduler` 中存在的严重逻辑缺陷，该缺陷会在 Agent 启动失败或异常退出时，因缺乏冷却（Cool-down）和回退（Backoff）机制，导致无限重复创建进程，最终引发宿主机资源耗尽（Fork Bomb）。

## Analysis
- **Root Cause**: `HandoverPolicy` 仅检查当前是否存在 `Running/Pending` 的 Session。若 Agent 进程因 OOM 死亡（变为 `Terminated/Failed`），Issue 状态依然是 `Doing`，导致下一轮 Tick（5秒后）再次触发启动。
- **Arch Defect**: 当前 `SessionManager` 缺乏并发控制逻辑，只要触发器通过就无限 fork 进程。
- **Impact**: 宿主机内存溢出，系统崩溃。

## Acceptance Criteria
- [x] **Role-based Concurrency Control**: 实现基于角色的信号量机制（Semaphores）。
    - **默认策略 (Conservative Defaults)**:
        - Global Max: **3** (防止宿主机卡死)
        - Engineer: **1**
        - Architect: **1**
        - Reviewer: **1**
    - 支持配置不同角色的最大并发数。
- [x] **Configurable**: 
    - 支持在 `workspace.yaml` 中定义 `agent.concurrency` 策略。
    - 支持 `monoco serve` 启动参数覆盖（如 `--max-agents 3`）。
- [x] **Failure Backoff**: 对于最近 N 秒内有失败记录的 Issue，Scheduler 应跳过触发。
- [x] **Graceful Rejection**: 当达到并发上限时，记录 Warning 日志并跳过启动，而不是报错。

## Technical Tasks
- [x] Config: Update `Config` model to support `AgentConcurrencyConfig`.
- [x] Core: Implement `SemaphoreManager` in `monoco/daemon/services.py` or inside `SchedulerService`.
- [x] CLI: Add `--max-agents` arg to `monoco serve` command.
- [x] Logic: Update `SchedulerService` to verify `can_acquire(role)` before spawning.
- [x] Logic: Maintain `failure_registry` for Cool-down implementation.
- [x] Test: Unit test for Semaphore limits (e.g. try spanning 6 Engineers when limit is 5).


## Review Comments

### Implementation Summary

#### 1. AgentConcurrencyConfig (monoco/core/config.py)
- 新增 `AgentConcurrencyConfig` 模型，支持配置：
  - `global_max`: 全局最大并发数（默认 3）
  - `engineer`, `architect`, `reviewer`, `planner`: 各角色最大并发数（默认均为 1）
  - `failure_cooldown_seconds`: 失败后冷却时间（默认 60 秒）
- 集成到 `AgentConfig` 中作为 `concurrency` 字段

#### 2. SemaphoreManager (monoco/daemon/services.py)
- 实现基于角色的信号量管理器：
  - `can_acquire(role_name, issue_id)`: 检查是否可以获取槽位（包含全局限制、角色限制、冷却检查）
  - `acquire(session_id, role_name)`: 获取槽位
  - `release(session_id)`: 释放槽位
  - `record_failure(issue_id, session_id)`: 记录失败并启动冷却
  - `clear_failure(issue_id)`: 清除失败记录（成功完成时调用）
  - `get_status()`: 获取当前状态用于监控
- 线程安全：使用 `threading.Lock` 保护共享状态

#### 3. CLI 参数支持 (monoco/daemon/commands.py)
- `monoco serve` 新增 `--max-agents` 参数
- 通过环境变量 `MONOCO_MAX_AGENTS` 传递给 Scheduler

#### 4. SchedulerService 集成 (monoco/daemon/scheduler.py)
- 初始化时加载并发配置
- 所有 spawn 操作前调用 `can_acquire()` 检查
- 成功启动后调用 `acquire()` 获取槽位
- 启动失败时调用 `release()` 释放槽位
- 检测到失败状态时调用 `record_failure()` 记录冷却
- 成功完成时调用 `clear_failure()` 清除冷却

#### 5. 测试覆盖 (tests/daemon/test_semaphore_manager.py)
- 14 个单元测试覆盖：
  - 默认限制验证
  - 自定义配置
  - 获取/释放槽位
  - 角色限制执行
  - 全局限制执行
  - 失败冷却机制
  - 冷却过期
  - 清除失败记录
  - 边界情况处理
  - Fork Bomb 场景模拟
  - 多角色并发场景
  - 优雅降级
