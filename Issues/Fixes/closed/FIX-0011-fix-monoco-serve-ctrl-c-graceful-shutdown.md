---
id: FIX-0011
uid: bc590c
type: fix
status: closed
stage: done
title: Fix monoco serve Ctrl+C graceful shutdown
created_at: '2026-02-03T21:09:15'
updated_at: '2026-02-03T21:09:15'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0011'
files:
- monoco/daemon/commands.py
criticality: high
solution: implemented
opened_at: '2026-02-03T21:09:15'
---

## FIX-0011: Fix monoco serve Ctrl+C graceful shutdown

## Objective

修复 `monoco serve` 在 Ctrl+C 后无法 graceful shutdown 的问题。原代码在 signal handler 中直接调用 `sys.exit(0)`，导致 uvicorn 的 lifespan shutdown 代码无法执行，daemon、watcher 等服务无法被正确清理。

## Acceptance Criteria
- [x] Ctrl+C 后 signal handler 不直接退出进程
- [x] uvicorn lifespan shutdown 能正常执行
- [x] daemon 模式下也能正确处理 SIGTERM

## Technical Tasks

- [x] 修改 `_setup_signal_handlers` 函数
  - [x] 移除 `sys.exit(0)` 调用
  - [x] 只保留 PID 文件清理
  - [x] 添加详细注释说明设计意图
- [x] 为 daemon 模式也启用 signal handler
  - [x] 确保 `serve stop` 发送的 SIGTERM 能被正确处理

## Changes Made

### 1. 修改 signal handler (`monoco/daemon/commands.py`)

**Before:**
```python
def signal_handler(signum, frame):
    console.print(f"\n[yellow]Received signal {signum}, shutting down...[/yellow]")
    pid_manager.remove_pid_file()
    sys.exit(0)  # ← 阻止 graceful shutdown
```

**After:**
```python
def signal_handler(signum, frame):
    console.print(f"\n[yellow]Received signal {signum}, shutting down gracefully...[/yellow]")
    # Only remove PID file here; let uvicorn handle the rest
    # The lifespan shutdown in app.py will stop all services
    pid_manager.remove_pid_file()
    # Don't call sys.exit() - let uvicorn's signal handler continue
    # to execute the shutdown sequence properly
```

### 2. 为 daemon 模式启用 signal handler

**Before:**
```python
# Setup signal handlers for foreground mode
if not daemon:
    _setup_signal_handlers(pid_manager)
```

**After:**
```python
# Setup signal handlers for graceful shutdown in both modes
# - Foreground: Ctrl+C (SIGINT) or SIGTERM
# - Daemon: SIGTERM from `serve stop` command
_setup_signal_handlers(pid_manager)
```

## Review Comments

修复已完成。修改后：
1. Signal handler 不再直接终止进程
2. Uvicorn 的 graceful shutdown 机制能够正常执行
3. FastAPI lifespan 的 shutdown 代码会被调用，正确停止所有服务（watcher、scheduler、event_bus 等）
4. Daemon 模式下也能正确处理 SIGTERM 信号
