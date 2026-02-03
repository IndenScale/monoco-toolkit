---
id: FEAT-0161
uid: b2c3d4
type: feature
status: open
stage: doing
title: 文件系统事件到业务事件的自动化映射框架
created_at: '2026-02-03T09:25:00'
updated_at: '2026-02-03T10:26:12'
parent: EPIC-0025
dependencies:
- FEAT-0160
- FEAT-0153
related:
- FEAT-0162
- FEAT-0160
domains:
- AgentEmpowerment
tags:
- '#EPIC-0025'
- '#FEAT-0161'
- architecture
- watcher
- event-driven
- three-layer
files:
- Issues/Features/open/FEAT-0161-filesystem-event-automation-framework.md
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T09:25:00'
isolation:
  type: branch
  ref: feat/feat-0161-文件系统事件到业务事件的自动化映射框架
  created_at: '2026-02-03T10:03:44'
---

## FEAT-0161: 文件系统事件到业务事件的自动化映射框架

## 背景与目标

当前架构存在分层问题：`SchedulerService` 既负责调度又负责文件监听，Handler 直接 spawn agent 而缺少 Action 抽象。这导致：
1. 文件监听逻辑无法独立复用
2. 新增 Action 类型需要修改 Handler 代码
3. 无法支持非 Agent Action（如 pytest、git push、IM 通知）

本任务旨在建立**三层架构**：
- **Layer 1**: 文件监听层 (Watcher) - 监听文件系统变化
- **Layer 2**: 事件路由层 (ActionRouter) - 将事件路由到 Action
- **Layer 3**: 执行层 (Action) - 具体执行逻辑

**架构决策**: 参见 Memos/architecture-layer-analysis.md

## 目标

1. 提取文件监听到独立的 `core/watcher/` 模块 (Layer 1)
2. 设计 `ActionRouter` 与 `Action` 抽象层 (Layer 2 & 3)
3. 实现字段变化检测 (YAML Front Matter 监听)
4. 统一 Dropzone/Memo/Issue/Task 监听逻辑
5. 支持触发器配置化 (YAML/JSON)

## 验收标准

- [x] **Layer 1 - 文件监听层**: `core/watcher/` 模块独立运行
- [x] **Layer 2 - 事件路由层**: `ActionRouter` 实现事件到 Action 的映射
- [x] **Layer 3 - 执行层**: `Action` ABC 支持多种执行类型
- [x] **字段检测**: YAML Front Matter 字段级变化监听
- [x] **统一监听**: Dropzone/Memo/Issue/Task 使用统一框架
- [x] **配置化**: 触发器支持 YAML/JSON 配置

## 技术任务

### Phase 1: Layer 1 - 文件监听层 (Watcher)

- [x] 创建 `monoco/core/watcher/__init__.py`
  - 导出 `FilesystemWatcher`, `FileEvent`, `WatchConfig`
- [x] 创建 `monoco/core/watcher/base.py`
  - 定义 `FilesystemWatcher` ABC
    - `start()` / `stop()` - 生命周期管理
    - `emit(event_type, payload)` - 发送事件到 EventBus
  - 定义 `FileEvent` dataclass (path, change_type, old_content, new_content)
  - 定义 `WatchConfig` (path, pattern, field_extractors)
- [x] 实现 `IssueWatcher`
  - 监听 `Issues/` 目录变化
  - 检测 Issue 文件创建/修改/删除
  - 提取 YAML Front Matter 字段变化
- [x] 实现 `MemoWatcher`
  - 监听 `Memos/inbox.md` 变化
  - 检测 Memo 累积阈值
  - 提取 pending memo 数量
- [x] 实现 `TaskWatcher`
  - 监听 `tasks.md` 或特定任务文件
  - 检测任务状态变化
- [x] 迁移 `DropzoneWatcher`
  - 从 `core/ingestion/watcher.py` 迁移
  - 适配新的 `FilesystemWatcher` 接口

### Phase 2: Layer 2 - 事件路由层 (ActionRouter)

- [x] 创建 `monoco/core/router/__init__.py`
  - 导出 `ActionRouter`, `Action`, `ActionResult`
- [x] 创建 `monoco/core/router/action.py`
  - 定义 `Action` ABC
    - `name` - Action 名称
    - `can_execute(payload) -> bool` - 条件判断
    - `execute(payload) -> ActionResult` - 执行逻辑
  - 定义 `ActionResult` dataclass (success, output, error, metadata)
- [x] 创建 `monoco/core/router/router.py`
  - 实现 `ActionRouter`
    - `register(event_type, action)` - 注册 Action
    - `route(event)` - 路由事件到对应 Actions
    - `start()` / `stop()` - 生命周期管理
  - 支持条件路由 (Conditional Routing)
  - 支持 Action 链 (Action Chain)

### Phase 3: Layer 3 - 执行层 (Actions)

- [x] 创建 `monoco/core/executor/__init__.py`
- [x] 创建 `monoco/core/executor/agent_action.py`
  - 实现 `SpawnAgentAction(Action)`
  - 使用 `AgentScheduler` 调度 Agent
  - 支持不同 Role (Architect, Engineer, Reviewer)
- [x] 创建 `monoco/core/executor/pytest_action.py` (预留)
  - 实现 `RunPytestAction(Action)`
  - 支持运行测试并解析结果
- [x] 创建 `monoco/core/executor/git_action.py` (预留)
  - 实现 `GitPushAction(Action)`
  - 实现 `GitCommitAction(Action)`
- [x] 创建 `monoco/core/executor/im_action.py` (预留)
  - 实现 `SendIMAction(Action)`
  - 支持发送通知消息

### Phase 4: 字段变化检测

- [x] 实现 `YAMLFrontMatterExtractor`
  - 解析 Markdown 文件的 YAML Front Matter
  - 检测特定字段变化 (status, stage, assignee 等)
  - 生成字段级事件 (e.g., `issue.status_changed`)
- [x] 实现 `FieldWatcher`
  - 配置化字段监听
  - 支持条件触发 (e.g., `status == "doing"`)

### Phase 5: 触发器配置化

- [x] 创建 `monoco/core/automation/config.py`
  - 定义触发器配置 Schema
- [x] 实现 YAML/JSON 配置解析
  ```yaml
  triggers:
    - name: "memo_threshold"
      watcher: "MemoWatcher"
      condition: "pending_count >= 5"
      actions:
        - type: "SpawnAgentAction"
          role: "Architect"
    
    - name: "issue_doing"
      watcher: "IssueWatcher"
      field: "stage"
      condition: "value == 'doing'"
      actions:
        - type: "SpawnAgentAction"
          role: "Engineer"
  ```
- [ ] 实现配置热加载

### Phase 6: 重构现有代码

- [ ] 重构 `SchedulerService`
  - 移除文件监听逻辑
  - 改为组装 Watcher + Router
- [ ] 重构 `daemon/handlers.py`
  - 将 Handler 改为 Action 实现
  - 使用 ActionRouter 注册

### Phase 7: 测试与文档

- [x] 单元测试 (112 个测试通过)
  - Watcher 基础功能测试 (37 个测试)
  - ActionRouter 路由测试 (31 个测试)
  - Action 执行测试
  - Field Watcher 测试 (44 个测试)
- [ ] 集成测试
  - 文件变化 → 事件 → Action 完整流程
- [ ] 文档
  - 三层架构设计文档
  - 如何添加新的 Watcher
  - 如何添加新的 Action
  - 触发器配置指南

## 架构设计

### 三层架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           LAYER 1: 文件监听层                            │
│                          (File Watcher / Producer)                       │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ IssueWatcher│  │ MemoWatcher │  │ TaskWatcher │  │ DropzoneWatcher │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
│         │                │                │                  │          │
│         └────────────────┴────────────────┴──────────────────┘          │
│                                   │                                     │
│                                   ▼                                     │
│                         ┌─────────────────┐                             │
│                         │   EventBus      │                             │
│                         │  (publish)      │                             │
│                         └─────────────────┘                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           LAYER 2: 事件调度层                            │
│                     (Event Consumer / Action Router)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                         ┌─────────────────┐                             │
│                         │  ActionRouter   │                             │
│                         │                 │                             │
│                         │  - 监听事件      │                             │
│                         │  - 路由到 Action │                             │
│                         │  - 条件判断      │                             │
│                         └────────┬────────┘                             │
│                                  │                                      │
│         ┌────────────────────────┼────────────────────────┐             │
│         │                        │                        │             │
│         ▼                        ▼                        ▼             │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────────┐     │
│  │SpawnAgent   │        │RunPytest    │        │SendNotification │     │
│  │  Action     │        │  Action     │        │    Action       │     │
│  └──────┬──────┘        └──────┬──────┘        └────────┬────────┘     │
└─────────┼──────────────────────┼────────────────────────┼──────────────┘
          │                      │                        │
          ▼                      ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           LAYER 3: 执行层                                │
│                        (Action Executor)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  AgentScheduler │  │  TestRunner     │  │  NotificationService    │  │
│  │                 │  │                 │  │                         │  │
│  │  - spawn agent  │  │  - pytest       │  │  - send IM message      │  │
│  │  - monitor      │  │  - git push     │  │  - send email           │  │
│  │  - terminate    │  │  - deploy       │  │  - webhook              │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 核心接口

```python
# Layer 1: FilesystemWatcher
class FilesystemWatcher(ABC):
    """文件监听抽象"""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    @abstractmethod
    async def start(self): ...
    
    @abstractmethod
    async def stop(self): ...
    
    async def emit(self, event_type: str, payload: Dict):
        await self.event_bus.publish(event_type, payload)

# Layer 2 & 3: Action
class Action(ABC):
    """Action 抽象"""
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @abstractmethod
    async def can_execute(self, payload: Dict) -> bool: ...
    
    @abstractmethod
    async def execute(self, payload: Dict) -> ActionResult: ...

# Layer 2: ActionRouter
class ActionRouter:
    """事件路由中心"""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._actions: Dict[str, List[Action]] = defaultdict(list)
    
    def register(self, event_type: str, action: Action):
        self._actions[event_type].append(action)
    
    async def start(self):
        while self._running:
            event = await self.event_bus.consume()
            await self._route(event)
    
    async def _route(self, event: AgentEvent):
        actions = self._actions.get(event.type, [])
        for action in actions:
            if await action.can_execute(event.payload):
                result = await action.execute(event.payload)
```

## 依赖

- FEAT-0165: AgentScheduler 抽象层
  - `SpawnAgentAction` 依赖 `AgentScheduler`
- FEAT-0153: Mailroom Automation
  - `DropzoneWatcher` 迁移依赖

## 被依赖

- FEAT-0167: Agent 联调工作流
  - 依赖本任务的 Watcher 和 Action 框架
- (IM 适配为未来工作，非核心)
  - 依赖本任务的文件监听框架

## 文件变更预估

| 文件 | 操作 | 说明 |
|------|------|------|
| `monoco/core/watcher/__init__.py` | 新增 | Watcher 模块 |
| `monoco/core/watcher/base.py` | 新增 | FilesystemWatcher ABC |
| `monoco/core/watcher/issue.py` | 新增 | IssueWatcher |
| `monoco/core/watcher/memo.py` | 新增 | MemoWatcher |
| `monoco/core/watcher/task.py` | 新增 | TaskWatcher |
| `monoco/core/router/__init__.py` | 新增 | Router 模块 |
| `monoco/core/router/action.py` | 新增 | Action ABC |
| `monoco/core/router/router.py` | 新增 | ActionRouter |
| `monoco/core/executor/__init__.py` | 新增 | Executor 模块 |
| `monoco/core/executor/agent_action.py` | 新增 | SpawnAgentAction |
| `monoco/daemon/scheduler.py` | 修改 | 重构为组装层 |
| `monoco/daemon/handlers.py` | 修改 | 改为 Action 实现 |

## Review Comments

*架构设计评审待补充*
