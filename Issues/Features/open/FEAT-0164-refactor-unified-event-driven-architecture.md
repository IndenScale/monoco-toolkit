---
id: FEAT-0164
uid: d4e5f6
type: feature
status: open
stage: draft
title: 重构：清除旧 Handler 架构，统一事件驱动架构
created_at: '2026-02-03T12:00:00'
updated_at: '2026-02-03T12:00:00'
dependencies:
- FEAT-0160
- FEAT-0161
- FEAT-0162
related:
- FEAT-0155
domains:
- AgentEmpowerment
tags:
- '#FEAT-0164'
- '#refactor'
- '#architecture'
- '#event-driven'
- '#cleanup'
files: []
criticality: high
---

## FEAT-0164: 重构：清除旧 Handler 架构，统一事件驱动架构

## 背景与目标

当前 Daemon 中存在两套 Handler 架构：
1. **旧架构** (`monoco/daemon/handlers.py`): 基于 `SessionManager` + `SemaphoreManager` + Polling Loop
2. **新架构** (`monoco/core/automation/handlers.py`): 基于 `AgentScheduler` + EventBus + Watcher 框架

新架构 (FEAT-0160/0161/0162) 的代码已合并，但**未被 Daemon 使用**。本任务旨在：
- **彻底删除**旧架构代码和测试
- **激活**新架构并集成到 Daemon
- **统一**为单一的事件驱动架构

## 目标

1. 删除旧 Handler 架构的所有代码
2. 删除旧架构相关的测试文件
3. 重构 `SchedulerService` 使用新架构
4. 集成 `Watcher` 框架到 Daemon
5. 集成 `ActionRouter` 到 Daemon
6. 确保所有测试通过

## 验收标准

- [ ] 旧 Handler 代码已删除 (`monoco/daemon/handlers.py` 中的旧类)
- [ ] 旧架构相关测试已删除
- [ ] `SchedulerService` 使用 `AgentScheduler` + 新 Handler
- [ ] `Watcher` 框架集成到 Daemon 生命周期
- [ ] `ActionRouter` 集成到事件处理流程
- [ ] 所有 623 个测试通过
- [ ] Daemon 启动时正确初始化新架构

## 技术任务

### Phase 1: 删除旧架构代码

#### 1.1 删除旧 Handler 类
- [ ] 删除 `monoco/daemon/handlers.py` 中的:
  - `AgentEventHandler` (ABC)
  - `ArchitectHandler`
  - `EngineerHandler`
  - `CoronerHandler`
  - `ReviewerHandler`
  - `EventHandlerRegistry`
- [ ] 保留文件用于新的 Handler 注册逻辑（或合并到 `core/automation`）

#### 1.2 删除旧架构支持代码
- [ ] 删除 `monoco/daemon/services.py` 中的:
  - `SemaphoreManager`（如果仅被旧架构使用）
- [ ] 删除 `monoco/features/agent/` 中的旧组件:
  - `manager.py` - `SessionManager` 类
  - `session.py` - `RuntimeSession` 类
  - `apoptosis.py` - `ApoptosisManager` 类
  - `adapter.py` - 如果与旧架构耦合
- [ ] 更新 `monoco/features/agent/__init__.py` 导出

#### 1.3 删除旧架构测试
- [ ] 删除 `tests/daemon/test_semaphore_manager.py`
- [ ] 删除 `tests/daemon/test_session_api.py`
- [ ] 删除 `tests/features/test_reliability.py`（如果仅测试旧架构）
- [ ] 删除 `tests/features/test_session.py`
- [ ] 删除 `tests/features/test_session_manager_persistence.py`
- [ ] 删除 `tests/features/test_session_persistence.py`
- [ ] 删除 `tests/daemon/test_scheduler_logic.py`（如果仅测试旧逻辑）

### Phase 2: 重构 SchedulerService

#### 2.1 简化 SchedulerService
- [ ] 重写 `monoco/daemon/scheduler.py`:
  ```python
  class SchedulerService:
      """Unified event-driven scheduler service."""
      
      def __init__(self, project_manager: ProjectManager):
          self.project_manager = project_manager
          
          # AgentScheduler (FEAT-0160)
          self.agent_scheduler = LocalProcessScheduler(...)
          
          # ActionRouter (FEAT-0161)
          self.action_router = ActionRouter(event_bus)
          
          # Watchers (FEAT-0161)
          self.watchers: List[FilesystemWatcher] = []
          
          # Handlers (FEAT-0162)
          self.handlers: List[Any] = []
      
      async def start(self):
          # 1. Start AgentScheduler
          await self.agent_scheduler.start()
          
          # 2. Setup and start Watchers
          self._setup_watchers()
          for watcher in self.watchers:
              await watcher.start()
          
          # 3. Register Actions to Router
          self._register_actions()
          
          # 4. Start ActionRouter
          await self.action_router.start()
          
          # 5. Start Handlers
          self.handlers = start_all_handlers(self.agent_scheduler)
      
      def _setup_watchers(self):
          """Initialize all filesystem watchers."""
          for project_ctx in self.project_manager.projects.values():
              # IssueWatcher
              self.watchers.append(IssueWatcher(
                  watch_path=project_ctx.issues_root,
                  event_bus=event_bus,
              ))
              
              # MemoWatcher
              memo_path = project_ctx.path / "Memos" / "inbox.md"
              if memo_path.exists():
                  self.watchers.append(MemoWatcher(
                      watch_path=memo_path,
                      event_bus=event_bus,
                  ))
              
              # TaskWatcher (if tasks.md exists)
              task_path = project_ctx.path / "tasks.md"
              if task_path.exists():
                  self.watchers.append(TaskWatcher(
                      watch_path=task_path,
                      event_bus=event_bus,
                  ))
      
      def _register_actions(self):
          """Register all actions to the router."""
          # SpawnAgentAction for different roles
          self.action_router.register(
              AgentEventType.MEMO_THRESHOLD,
              SpawnAgentAction(self.agent_scheduler, role="Architect")
          )
          self.action_router.register(
              AgentEventType.ISSUE_STAGE_CHANGED,
              ConditionalAction(
                  condition=lambda p: p.get("new_stage") == "doing",
                  action=SpawnAgentAction(self.agent_scheduler, role="Engineer")
              )
          )
          self.action_router.register(
              AgentEventType.PR_CREATED,
              SpawnAgentAction(self.agent_scheduler, role="Reviewer")
          )
      ```

#### 2.2 移除旧组件依赖
- [ ] 移除 `session_managers` 字典
- [ ] 移除 `apoptosis_managers` 字典
- [ ] 移除 `_memo_watcher_loop()` 方法
- [ ] 移除 `_issue_watcher_loop()` 方法
- [ ] 移除 `_session_monitor_loop()` 方法
- [ ] 移除 `_register_handlers()` 方法
- [ ] 移除 `semaphore_manager`（如果已集成到 AgentScheduler）

### Phase 3: 集成 Watcher 框架

#### 3.1 确保 Watcher 正确实现
- [ ] 检查 `monoco/core/watcher/issue.py` - `IssueWatcher`
- [ ] 检查 `monoco/core/watcher/memo.py` - `MemoWatcher`
- [ ] 检查 `monoco/core/watcher/task.py` - `TaskWatcher`
- [ ] 确保所有 Watcher 使用 `watchdog` 或 `PollingWatcher` 实现

#### 3.2 Watcher 生命周期管理
- [ ] Watcher 在 `start()` 中启动
- [ ] Watcher 在 `stop()` 中停止
- [ ] 处理 Watcher 异常（重启或记录）

### Phase 4: 集成 ActionRouter

#### 4.1 Action 注册
- [ ] 在 `SchedulerService` 中创建 `ActionRouter` 实例
- [ ] 注册 `SpawnAgentAction` 到 Router
- [ ] 注册条件路由（如 Issue stage=doing 才触发 Engineer）

#### 4.2 Action 执行
- [ ] 确保 Action 通过 `AgentScheduler.schedule()` 调度 Agent
- [ ] 处理 Action 执行结果

### Phase 5: 更新导入和导出

#### 5.1 更新 Daemon 导入
- [ ] `monoco/daemon/scheduler.py`:
  - 移除: `SessionManager`, `ApoptosisManager`, `SemaphoreManager`
  - 添加: `ActionRouter`, `SpawnAgentAction`, `ConditionalAction`
  - 添加: `IssueWatcher`, `MemoWatcher`, `TaskWatcher`
  - 添加: `start_all_handlers` (from `core.automation.handlers`)

#### 5.2 更新 features/agent 模块
- [ ] 决定 `monoco/features/agent/` 模块的命运:
  - 选项 A: 完全删除，功能迁移到 `core/scheduler/` 和 `core/executor/`
  - 选项 B: 保留 CLI 命令，但底层使用新架构
- [ ] 更新 `monoco/features/agent/cli.py` 使用 `AgentScheduler`

### Phase 6: 测试和验证

#### 6.1 更新现有测试
- [ ] 更新 `tests/test_scheduler_base.py`（如果需要）
- [ ] 更新 `tests/test_scheduler_local.py`（如果需要）
- [ ] 更新 `tests/test_scheduler_engines.py`（如果需要）

#### 6.2 新架构测试
- [ ] 确保 `tests/core/watcher/` 测试通过
- [ ] 确保 `tests/core/router/` 测试通过
- [ ] 确保 `tests/core/automation/` 测试通过
- [ ] 确保 `tests/core/executor/` 测试通过

#### 6.3 集成测试
- [ ] Daemon 启动/停止测试
- [ ] Watcher 事件触发测试
- [ ] Action 路由测试
- [ ] 端到端 Workflow 测试

## 文件变更预估

### 删除的文件
| 文件 | 说明 |
|------|------|
| `monoco/daemon/handlers.py` | 旧 Handler 类（完全删除或重写） |
| `monoco/features/agent/manager.py` | `SessionManager` |
| `monoco/features/agent/session.py` | `RuntimeSession` |
| `monoco/features/agent/apoptosis.py` | `ApoptosisManager` |
| `monoco/features/agent/adapter.py` | 如果与旧架构耦合 |
| `tests/daemon/test_semaphore_manager.py` | Semaphore 测试 |
| `tests/daemon/test_session_api.py` | Session API 测试 |
| `tests/features/test_session*.py` | Session 相关测试 |
| `tests/features/test_reliability.py` | Reliability 测试 |
| `tests/daemon/test_scheduler_logic.py` | 旧 Scheduler 逻辑测试 |

### 修改的文件
| 文件 | 变更 |
|------|------|
| `monoco/daemon/scheduler.py` | 完全重写，使用新架构 |
| `monoco/daemon/services.py` | 移除 `SemaphoreManager` |
| `monoco/daemon/app.py` | 更新 `SchedulerService` 使用方式 |
| `monoco/features/agent/__init__.py` | 更新导出 |
| `monoco/features/agent/cli.py` | 使用新架构 |
| `monoco/main.py` | 更新导入（如果需要） |

### 保留的文件（新架构）
| 文件 | 说明 |
|------|------|
| `monoco/core/scheduler/` | AgentScheduler 抽象层 (FEAT-0160) |
| `monoco/core/watcher/` | Watcher 框架 (FEAT-0161) |
| `monoco/core/router/` | ActionRouter (FEAT-0161) |
| `monoco/core/executor/` | Action 执行层 (FEAT-0161) |
| `monoco/core/automation/` | Handler 和配置 (FEAT-0162) |

## 架构对比

### 旧架构（删除）
```
SchedulerService
├── SessionManager (每个项目一个)
│   └── RuntimeSession
├── ApoptosisManager
├── SemaphoreManager
├── EventHandlerRegistry
│   ├── ArchitectHandler
│   ├── EngineerHandler
│   ├── CoronerHandler
│   └── ReviewerHandler
└── Polling Loops
    ├── _memo_watcher_loop()
    ├── _issue_watcher_loop()
    └── _session_monitor_loop()
```

### 新架构（统一）
```
SchedulerService
├── AgentScheduler (LocalProcessScheduler)
│   └── 管理 Agent 进程生命周期
├── ActionRouter
│   └── 路由事件到 Actions
├── Actions
│   ├── SpawnAgentAction (Architect)
│   ├── SpawnAgentAction (Engineer)
│   └── SpawnAgentAction (Reviewer)
├── Watchers
│   ├── IssueWatcher -> EventBus
│   ├── MemoWatcher -> EventBus
│   └── TaskWatcher -> EventBus
└── Handlers (FEAT-0162)
    ├── TaskFileHandler
    ├── IssueStageHandler
    ├── MemoThresholdHandler
    └── PRCreatedHandler
```

## 依赖

- FEAT-0160: AgentScheduler 抽象层（已完成）
- FEAT-0161: 文件系统事件自动化框架（已完成）
- FEAT-0162: Agent 联调工作流（已完成）

## 风险与注意事项

1. **破坏性变更**: 这是破坏性重构，旧代码将被物理删除
2. **功能验证**: 需要确保新架构完全覆盖旧架构功能
3. **CLI 兼容性**: `monoco agent` 命令需要保持兼容或明确废弃
4. **配置迁移**: 如果有旧架构配置，需要迁移或清理

## Review Comments

*待实现后填写*
