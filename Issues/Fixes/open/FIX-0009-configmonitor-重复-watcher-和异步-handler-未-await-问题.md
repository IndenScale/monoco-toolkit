---
id: FIX-0009
uid: 11b407
type: fix
status: open
stage: review
title: ConfigMonitor 重复 watcher 和异步 handler 未 await 问题
created_at: '2026-02-03T13:16:34'
updated_at: '2026-02-03T13:40:37'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0009'
files:
- '"Issues/Fixes/open/FIX-0009-configmonitor-\351\207\215\345\244\215-watcher-\345\222\214\345\274\202\346\255\245-handler-\346\234\252-await-\351\227\256\351\242\230.md"'
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- monoco/core/config.py
- monoco/core/scheduler/events.py
- monoco/core/watcher/base.py
- monoco/daemon/app.py
- monoco/daemon/services.py
- uv.lock
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T13:16:34'
isolation:
  type: branch
  ref: feat/fix-0009-configmonitor-重复-watcher-和异步-handler-未-await-问题
  created_at: '2026-02-03T13:18:52'
---

## FIX-0009: ConfigMonitor 重复 watcher 和异步 handler 未 await 问题

## Objective
修复 `monoco serve` 启动时的两个严重错误：
1. **ConfigMonitor 重复 watcher 错误** - 同一目录被多次 schedule 导致 RuntimeError
2. **异步 handler 未 await 警告** - MemoThresholdHandler 协程未被正确执行

## Problem Analysis

### 问题 1: ConfigMonitor 重复 watcher

**报错信息：**
```
RuntimeError: Cannot add watch <ObservedWatch: path='.../.monoco', is_recursive=False> - it is already scheduled
```

**根本原因：**
- `daemon/app.py` 启动时创建了两个 `ConfigMonitor`：
  - 监视 `project.yaml`
  - 监视 `workspace.yaml`
- 两个文件都在 `.monoco/` 目录下
- `ConfigMonitor` 使用 `observer.schedule(watch_dir)` 监视**父目录**
- macOS FSEvents 不允许对同一路径重复添加 watcher

**设计缺陷：**
根据项目设计原则，**不存在纯粹的 workspace 容器**，根目录本身就是一个 project。因此不应有独立的 workspace-level config monitor，而应该：
1. 根目录作为第一个 project 被注册
2. 每个 project 自行管理其配置监视
3. 移除 `daemon/app.py` 中的独立 `config_monitors`

### 问题 2: 异步 handler 未 await

**报错信息：**
```
RuntimeWarning: coroutine 'MemoThresholdHandler.__call__' was never awaited
```

**根本原因：**
- `MemoThresholdHandler.__call__` 是 `async def` 方法
- 它被注册为 `PollingWatcher` 的本地回调（`_callbacks`）
- `PollingWatcher.emit()` 中的检测逻辑对**绑定方法**失效
- 协程被调用但未 await，导致 handler 永远不会执行

**调用链：**
```
MemoWatcher._handle_count_change()
  └── await self.emit(event)           # base.py:138
        └── for callback in self._callbacks:
              └── callback(event)        # handler(event) 返回协程但未 await
```

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [x] `monoco serve` 启动时不再出现 `RuntimeError: Cannot add watch` 错误
- [x] `monoco serve` 启动时不再出现 `RuntimeWarning: coroutine ... was never awaited` 警告
- [x] 配置变更热更新功能正常工作
- [x] MemoThresholdHandler 能正确响应 threshold 事件

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

- [x] **Task 1: 重构 ConfigMonitor 架构**
  - [x] 移除 `daemon/app.py` 中的独立 `config_monitors` 列表
  - [x] 在 `ProjectContext` 中添加配置监视能力
  - [x] 修改 `ConfigMonitor` 直接监视文件而非目录（避免重复 schedule）
  
- [x] **Task 2: 修复异步 handler 调用**
  - [x] 修改 `PollingWatcher.emit()` 正确处理绑定方法
  - [x] 或使用 EventBus 订阅替代本地回调

- [x] **Task 3: 验证修复**
  - [x] 启动 `monoco serve` 确认无报错
  - [x] 修改 project.yaml 确认热更新生效
  - [x] 添加 memo 超过 threshold 确认 handler 被触发

## Files to Modify

| 文件 | 修改内容 |
|------|----------|
| `monoco/daemon/app.py` | 移除 `config_monitors` 相关代码 |
| `monoco/daemon/services.py` | `ProjectContext` 添加 `ConfigMonitor` |
| `monoco/core/config.py` | `ConfigMonitor` 改为文件级监视 |
| `monoco/core/watcher/base.py` | 修复异步回调检测 |

## Design Notes

### 架构调整

**当前（有问题）：**
```
daemon/app.py
├── config_monitors[0]: ConfigMonitor(project.yaml)  # watch .monoco/
├── config_monitors[1]: ConfigMonitor(workspace.yaml) # watch .monoco/ ← 冲突！
└── project_manager
    └── projects (无配置监视)
```

**修复后：**
```
daemon/app.py
└── project_manager
    └── projects[0] (root)
        └── ProjectContext
            └── config_monitor: ConfigMonitor(project.yaml)  # 只监视文件
```

### 关于 workspace.yaml

根据配置加载逻辑：
- `workspace.yaml`：core, paths, i18n, ui, telemetry, agent（环境配置）
- `project.yaml`：name, key, members（身份配置）

由于根目录是 project，workspace.yaml 变更可以通过重启 daemon 生效，暂不要求热更新。

## Review Comments

### 代码变更摘要

1. **monoco/daemon/app.py**: 移除了独立的 `config_monitors` 列表和相关生命周期管理代码，将配置监视职责下放到 `ProjectContext`。

2. **monoco/daemon/services.py**: 
   - 在 `ProjectContext.__init__` 中添加了 `ConfigMonitor` 初始化
   - 在 `start()` 中启动 `config_monitor`
   - 在 `stop()` 中停止 `config_monitor`
   - 使用 broadcaster 广播配置变更事件（`CONFIG_UPDATED`）

3. **monoco/core/config.py**: 
   - 添加了 `_started` 标志防止重复启动
   - 添加了异常处理，避免启动失败时崩溃
   - 改进了日志记录

4. **monoco/core/watcher/base.py**: 
   - 添加了 `_is_async_callable()` 方法，正确检测实现了 `__call__` 的异步可调用对象
   - 修复了 `MemoThresholdHandler` 等 handler 未被正确 await 的问题
