---
id: FEAT-0138
uid: 5d2c5f
type: feature
status: closed
stage: done
title: 实现代理会话持久化
created_at: '2026-02-01T20:44:08'
updated_at: '2026-02-02T11:27:50'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0138'
files:
- tests/features/test_session_manager_persistence.py
- tests/daemon/test_session_api.py
criticality: medium
solution: implemented
opened_at: '2026-02-01T20:44:08'
closed_at: '2026-02-02T11:27:50'
isolation:
  type: branch
  ref: feat/feat-0138-实现代理会话持久化
  created_at: '2026-02-02T11:21:25'
---

## FEAT-0138: 实现代理会话持久化

## 背景与目标

实现代理会话持久化功能，确保会话状态在系统重启后不会丢失。当前会话信息仅保存在内存中，当守护进程或系统重启时，所有进行中的会话状态都会丢失。本功能需要扩展 Session 模型，添加进程 ID 字段，实现 SessionManager 的持久化存储（加载/保存到 `.monoco/sessions/*.json`），并支持本地（所有者）与远程（观察者）两种模式，确保 Daemon 能够列出由 CLI 子任务创建的会话。

## 目标

确保代理会话状态在系统重启后不会丢失，支持 CLI 和 Daemon 之间的会话共享。

## 验收标准

- [x] Session 模型包含 `pid` 字段
- [x] SessionManager 将会话持久化到 `.monoco/sessions/*.json`
- [x] RuntimeSession 支持本地（所有者）与远程（观察者）两种模式
- [x] Worker 在 Session 模型中正确更新 `pid`
- [x] Daemon 可以列出由 CLI 子任务创建的会话
- [x] 所有单元测试通过
- [x] `monoco issue lint` 检查通过

## 技术任务

- [x] 更新 `Session` 模型，添加 `pid` 字段
- [x] 实现 `SessionManager` 持久化（加载/保存到 `.monoco/sessions/*.json`）
- [x] 更新 `RuntimeSession` 以支持本地（所有者）与远程（观察者）两种模式
- [x] 确保 `Worker` 在 Session 模型中更新 `pid`
- [x] 验证 Daemon 可以列出由 CLI 子任务创建的会话
- [x] 编写单元测试验证持久化功能
- [x] 编写单元测试验证跨进程会话可见性

## Review Comments

### 实现总结

本功能已实现代理会话的持久化存储，主要特性包括：

1. **Session 模型扩展**: `Session` 模型已包含 `pid` 字段，用于跟踪关联的进程 ID。

2. **SessionManager 持久化**: 
   - 会话自动保存到 `.monoco/sessions/{session_id}.json`
   - 支持从磁盘加载现有会话
   - 自动处理损坏的会话文件

3. **RuntimeSession 双模式支持**:
   - **所有者模式**: 带有 `Worker` 实例，可以启动/暂停/恢复会话
   - **观察者模式**: 无 `Worker` 实例，通过 `pid` 检查进程状态
   - 加载的会话自动进入观察者模式

4. **Worker PID 更新**: `Worker` 在启动时自动将进程 ID 更新到 `Session` 模型。

5. **Daemon 会话列表**: Daemon 通过 `SessionManager.list_sessions()` 可以列出所有会话，包括 CLI 创建的会话。

### 测试覆盖

新增测试文件：
- `tests/features/test_session_manager_persistence.py`: 15 个测试用例，覆盖会话持久化的各个方面
- `tests/daemon/test_session_api.py`: 9 个测试用例，验证 Daemon 与会话的交互

测试涵盖：
- 会话创建和保存
- 会话加载和观察者模式
- 跨 Manager 会话可见性
- PID 字段持久化
- 进程状态检测
- 损坏文件处理
- Daemon 列出 CLI 创建的会话
