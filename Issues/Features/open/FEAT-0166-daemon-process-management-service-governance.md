---
id: FEAT-0166
uid: c520bf
type: feature
status: open
stage: doing
title: Daemon Process Management & Service Governance
created_at: '2026-02-03T20:24:05'
updated_at: '2026-02-03T20:32:12'
parent: EPIC-0025
dependencies: []
related: []
domains:
- Foundation
tags:
- '#EPIC-0025'
- '#FEAT-0166'
- daemon
- process-management
- service-governance
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T20:24:05'
---

## FEAT-0166: Daemon Process Management & Service Governance

## Objective

实现 Monoco Daemon 的进程管理与服务治理层，解决以下核心问题：

1. **端口冲突**：当前 `monoco serve` 直接启动 uvicorn，无端口占用检测，导致多次启动时报错
2. **孤儿进程**：终端关闭后，前台运行的 uvicorn 进程未被清理，变成孤儿进程继续占用资源
3. **缺乏生命周期管理**：没有 `start/stop/status` 等标准服务管理命令

本 Feature 将引入 **Workspace-scoped 的守护进程模型**，每个工作区独立管理自己的 Daemon 实例，支持前台/后台两种运行模式，并提供完整的进程生命周期管理。

## Acceptance Criteria

- [ ] **PID 文件机制**：Workspace 级别的 PID 文件管理（`<workspace>/.monoco/run/monoco.pid`）
- [ ] **端口管理**：启动前检测端口占用，支持自动递增或明确报错
- [ ] **后台守护模式**：`--daemon` 参数支持后台运行，脱离控制终端
- [ ] **生命周期命令**：提供 `monoco serve start|stop|status|restart` 子命令
- [ ] **孤儿进程清理**：终端关闭时正确捕获信号，清理 uvicorn 及相关子进程
- [ ] **幂等性**：多次调用 `start` 不会重复启动，返回当前运行状态

## Technical Tasks

### Phase 1: PID 与端口管理基础设施
- [ ] 设计 PID 文件格式与存储结构（JSON 元数据）
- [ ] 实现 `PIDManager` 类（`monoco/core/daemon/pid.py`）
  - [ ] `create_pid_file(workspace_root, host, port)`
  - [ ] `read_pid_file(workspace_root)`
  - [ ] `remove_pid_file(workspace_root)`
  - [ ] `is_process_alive(pid)` 检查
- [ ] 实现端口检测与分配逻辑
  - [ ] `is_port_in_use(port, host)`
  - [ ] `find_available_port(start_port, host, max_retry=100)`

### Phase 2: 进程生命周期管理
- [ ] 扩展 `monoco/daemon/commands.py`
  - [ ] 添加 `start()` 命令（支持 `--daemon`, `--port`, `--host`）
  - [ ] 添加 `stop()` 命令（通过 PID 文件查找并终止进程）
  - [ ] 添加 `status()` 命令（显示运行状态、PID、端口、启动时间）
  - [ ] 添加 `restart()` 命令（stop + start 组合）
- [ ] 修改 `serve()` 函数，集成 PID 管理逻辑
  - [ ] 启动前检查现有 PID 文件
  - [ ] 启动成功后写入 PID 文件
  - [ ] 关闭时删除 PID 文件

### Phase 3: 信号处理与守护进程化
- [ ] 实现信号处理器（`SIGTERM`, `SIGINT`, `SIGHUP`）
  - [ ] 确保终端关闭时优雅关闭 uvicorn
  - [ ] 清理 PID 文件和临时资源
- [ ] 实现 Unix Daemon 化（`--daemon` 模式）
  - [ ] 使用 `os.fork()` 或 `subprocess` 实现后台运行
  - [ ] 重定向 stdout/stderr 到日志文件（`<workspace>/.monoco/log/daemon.log`）
  - [ ] 脱离控制终端（setsid）

### Phase 4: 孤儿进程清理工具
- [ ] 实现遗留进程检测与清理
  - [ ] `monoco serve cleanup` 命令：扫描并终止孤儿 uvicorn 进程
  - [ ] 自动检测端口 8642 及常用端口的占用情况
  - [ ] 通过进程名匹配（`uvicorn.*monoco.daemon.app`）识别孤儿进程

### Phase 5: 集成与测试
- [ ] 更新 CLI 入口，注册新的子命令
- [ ] 编写单元测试
  - [ ] PID 文件操作测试
  - [ ] 端口分配测试
  - [ ] 进程生命周期测试
- [ ] 手动测试场景
  - [ ] 正常启动/停止流程
  - [ ] 端口被占用时的错误处理
  - [ ] 终端关闭后进程清理
  - [ ] 后台模式日志输出

## Design Decisions

### Workspace-Scoped vs Global-Scoped
**决策**：采用 Workspace-scoped 模型
- PID 文件存储在 `<workspace>/.monoco/run/monoco.pid`
- 每个工作区独立管理自己的 Daemon
- 避免全局单点故障，支持多项目并行开发

### 端口分配策略
**决策**：固定端口优先，自动递增兜底
- 默认端口：8642
- 端口被占用时：尝试 8643-8741 范围
- 超出范围：明确报错，提示用户指定端口

### 后台运行实现
**决策**：双模式支持
- **前台模式**（默认）：开发调试，日志直接输出到终端
- **后台模式**（`--daemon`）：生产运行，日志写入文件

## Review Comments

<!-- Required for Review/Done stage. Record review feedback here. -->
