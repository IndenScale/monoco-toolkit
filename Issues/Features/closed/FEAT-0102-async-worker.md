---
id: FEAT-0102
uid: a1b2c3
type: feature
status: closed
stage: done
title: 重构 Worker 为异步执行模式
created_at: '2026-01-25T14:30:00'
updated_at: '2026-01-25T22:53:01'
closed_at: '2026-01-25T22:53:01'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0008'
- '#FEAT-0102'
files:
- monoco/features/scheduler/worker.py
- monoco/features/scheduler/session.py
- monoco/features/scheduler/manager.py
- tests/features/test_scheduler.py
- tests/features/test_session.py
priority: high
---

## FEAT-0102: 重构 Worker 为异步执行模式

### 目标
将 `Worker.start` 从同步阻塞执行更改为异步非阻塞执行。只有显式调用 `wait()` 时才应阻塞，同时提供基于轮询的状态检查机制。

### 背景
当前 `Worker.start()` 直接调用 `subprocess.Popen().wait()`，导致主线程阻塞。这阻碍了：
1. 多个 Agent 的并发执行。
2. Scheduler 进行有效的监控和控制循环。
3. "细胞凋亡" (Apoptosis) 机制生效（无法杀死卡死的 Agent）。

我们需要实现 "Fire-and-Forget + Monitor" 模式。

### 任务
- [x] 修改 `Worker` 类
    - [x] `start()`: 移除 `wait()` 调用，`Popen` 后立即返回。
    - [x] 新增 `poll()`: 非阻塞地检查进程状态。
    - [x] 新增 `wait()`: 可选的阻塞等待方法（如果需要）。
- [x] 修改 `RuntimeSession`
    - [x] `start()`: 适配异步模式，假设调用即运行。
    - [x] 新增 `refresh_status()`: 供循环/轮询调用以更新 Model 状态。
- [x] 更新测试
    - [x] `test_worker_lifecycle`: 验证 `start()` 返回 'running' 状态且进程存活。
    - [x] `test_session_lifecycle`: 验证异步状态流转。

## Review Comments

- **2026-01-25 Agent**: 已完成代码重构，所有测试通过。解决了 CI 环境中因依赖外部 `gemini` 导致的失败问题（通过 Mock 隔离），并实现了非阻塞的调度逻辑。
