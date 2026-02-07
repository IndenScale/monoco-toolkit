---
id: FIX-0022
uid: 29d30c
type: fix
status: open
stage: review
title: Fix Courier Service Multi-Instance and Port Conflict Issues
created_at: '2026-02-07T12:03:27'
updated_at: '2026-02-07T12:16:47'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0022'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Fixes/closed/FIX-0021-enhance-courier-status-with-port-persistence-and-h.md
- Issues/Fixes/open/FIX-0021-enhance-courier-status-with-port-persistence-and-h.md
- src/monoco/features/courier/commands.py
- src/monoco/features/courier/constants.py
- src/monoco/features/courier/service.py
- tests/features/courier/test_service_integration.py
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-07T12:03:27'
isolation:
  type: branch
  ref: FIX-0022-fix-courier-service-multi-instance-and-port-confli
  created_at: '2026-02-07T12:03:34'
---

## FIX-0022: Fix Courier Service Multi-Instance and Port Conflict Issues

## Objective

修复 Courier Service 的多实例启动和端口冲突问题，实现健壮的进程管理和资源隔离。

**核心问题**：

1. **多实例阻断失效**：不同端口可以同时启动多个 Courier 实例，共享同一个 PID/State 文件导致状态混乱。
2. **端口冲突检测缺失**：启动前不检查端口可用性，导致进程启动后立即因端口冲突崩溃。
3. **野生进程清理缺失**：`stop` 命令只能停止有 PID 文件的进程，无法清理孤儿进程。
4. **竞态条件漏洞**：快速连续启动时，PID 文件写入存在竞态条件。
5. **默认端口冲突**：8080 太常用，容易与其他开发服务冲突。

## Acceptance Criteria

- [x] 使用文件锁（flock）确保同一时刻只有一个 Courier 实例可以启动。
- [x] 启动前检查端口可用性，如果端口被占用则立即失败并提示。
- [x] `stop` 命令支持 `--all` 参数，可以清理所有 Courier 相关进程（通过进程名匹配）。
- [x] PID 文件写入使用原子操作（O_EXCL 标志）。
- [x] 默认端口从 8080 改为 8644。
- [x] 添加集成测试验证多实例阻断和端口冲突检测。

## Technical Tasks

- [x] **Phase 0: 修改默认端口**
  - [x] 修改 `constants.py` 中的 `COURIER_DEFAULT_PORT` 从 8080 改为 8644
  - [x] 更新相关文档和注释
- [x] **Phase 1: 文件锁机制**
  - [x] 在 `service.py` 中添加 `_acquire_lock()` 和 `_release_lock()` 方法
  - [x] 使用 `fcntl.flock()` 在启动时获取排他锁
  - [x] 确保锁在进程退出时自动释放
- [x] **Phase 2: 端口可用性检查**
  - [x] 添加 `_check_port_available(port)` 方法
  - [x] 在 `start()` 方法中调用端口检查
  - [x] 如果端口被占用，抛出 `ServiceStartError` 并提示占用进程信息
- [x] **Phase 3: 进程发现和清理**
  - [x] 添加 `_find_courier_processes()` 方法（通过 `pgrep` 查找）
  - [x] 在 `stop()` 中添加 `--all` 参数支持
  - [x] 实现基于进程名的批量清理逻辑
- [x] **Phase 4: 原子性 PID 写入**
  - [x] 修改 `_write_pid()` 使用 `os.open()` 的 `O_EXCL` 标志
  - [x] 处理文件已存在的异常情况
- [x] **Phase 5: 测试**
  - [x] 添加多实例启动测试
  - [x] 添加端口冲突测试
  - [x] 添加野生进程清理测试

## Review Comments

所有验收标准已实现并通过测试。

## Solution

### 实现总结

1. **文件锁机制** (`service.py`):
   - 添加 `_acquire_lock()` 和 `_release_lock()` 方法
   - 使用 `fcntl.flock()` 获取排他锁（非阻塞模式）
   - 锁文件路径: `.monoco/run/courier.lock`
   - 启动失败时自动释放锁，启动成功时保持锁定

2. **端口可用性检查** (`service.py`):
   - 添加 `_check_port_available(port)` 方法
   - 尝试绑定到指定端口进行验证
   - 如果端口被占用，使用 `lsof` 获取占用进程的 PID
   - 在 `start()` 方法最早期进行端口检查

3. **进程发现和清理** (`service.py`, `commands.py`):
   - 添加 `_find_courier_processes()` 方法，使用 `pgrep -f` 查找所有 Courier 进程
   - 修改 `stop()` 方法支持 `all_processes` 参数
   - CLI 添加 `--all` / `-a` 选项支持

4. **原子性 PID 写入** (`service.py`):
   - 修改 `_write_pid()` 使用 `os.O_CREAT | os.O_EXCL` 标志
   - 如果 PID 文件已存在，抛出 `ServiceAlreadyRunningError`

5. **默认端口更改** (`constants.py`):
   - `COURIER_DEFAULT_PORT` 从 8080 改为 8644

6. **集成测试** (`tests/features/courier/test_service_integration.py`):
   - 18 个测试用例覆盖所有功能
   - 文件锁多实例阻断测试
   - 端口冲突检测测试
   - 原子 PID 写入测试
   - 进程发现和清理测试

## 架构讨论记录

在实现过程中发现了更深层的架构问题：**Courier 应该是用户级别的全局服务，而非项目级别**。这个问题超出了本 Fix 的范围，应该在后续的 EPIC 中解决。当前 Fix 仅解决进程管理的技术问题。
