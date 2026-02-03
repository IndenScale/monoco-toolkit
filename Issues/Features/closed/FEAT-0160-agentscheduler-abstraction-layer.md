---
id: FEAT-0160
uid: a1b2c3
type: feature
status: closed
stage: done
title: AgentScheduler 抽象层与 Provider 解耦
created_at: '2026-02-03T09:20:00'
updated_at: '2026-02-03T09:58:58'
parent: EPIC-0025
dependencies:
- FEAT-0155
related:
- FEAT-0161
- FEAT-0162
domains:
- AgentEmpowerment
tags:
- '#EPIC-0025'
- '#FEAT-0160'
- architecture
- scheduler
- abstraction
files:
- monoco/core/scheduler/__init__.py
- monoco/core/scheduler/base.py
- monoco/core/scheduler/engines.py
- monoco/core/scheduler/events.py
- monoco/core/scheduler/local.py
- monoco/features/agent/engines.py
- monoco/features/agent/__init__.py
- monoco/features/agent/worker.py
- monoco/daemon/events.py
- monoco/daemon/handlers.py
- monoco/daemon/scheduler.py
- tests/test_scheduler_base.py
- tests/test_scheduler_local.py
- tests/test_scheduler_engines.py
criticality: high
solution: implemented
opened_at: '2026-02-03T09:20:00'
closed_at: '2026-02-03T09:58:58'
isolation:
  type: branch
  ref: feat/FEAT-0160-agentscheduler-abstraction
  created_at: '2026-02-03T09:58:58'
---

## FEAT-0160: AgentScheduler 抽象层与 Provider 解耦

## 背景与目标

当前 `EngineAdapter` 抽象层位于 `features/agent/` 目录，导致架构分层不清晰：`daemon/` 需要依赖 `features/` 层的抽象，违反了"核心抽象应在 core 层"的原则。

本任务旨在建立高层的 `AgentScheduler` 抽象，将调度策略与具体 Agent Provider 解耦，为未来的多执行环境（本地进程、Docker、远程服务）奠定基础。

**架构决策**: 参见 Memos/daemon-architecture-proposals-assessment.md 提议 1

## 目标

1. 创建 `monoco/core/scheduler/` 模块作为调度核心抽象层
2. 定义 `AgentScheduler` ABC，屏蔽 Provider 细节
3. 迁移 `EngineAdapter` 到 core 层作为子组件
4. 实现 `LocalProcessScheduler` 作为默认本地进程调度器
5. 支持并发配额控制与资源管理

## 验收标准

- [x] **模块创建**: `monoco/core/scheduler/` 目录结构完整
- [x] **抽象定义**: `AgentScheduler` ABC 定义完整接口 (schedule/terminate/get_status/list_active)
- [x] **迁移完成**: `EngineAdapter` 从 `features/agent/` 迁移至 `core/scheduler/`
- [x] **默认实现**: `LocalProcessScheduler` 实现本地进程调度
- [x] **配额控制**: 支持并发限制与资源管理
- [x] **文档**: Provider 接入文档完成

## 技术任务

### Phase 1: 模块初始化与抽象定义

- [x] 创建 `monoco/core/scheduler/__init__.py`
  - 导出 `AgentScheduler`, `AgentTask`, `AgentStatus`
  - 导出 `EngineAdapter`, `EngineFactory`
  - 导出 `EventBus`, `AgentEventType`, `EventHandler`
  - 导出 `LocalProcessScheduler`
- [x] 创建 `monoco/core/scheduler/base.py`
  - 定义 `AgentStatus` Enum (PENDING, RUNNING, COMPLETED, FAILED, TERMINATED, TIMEOUT)
  - 定义 `AgentTask` dataclass (task_id, role_name, issue_id, prompt, engine, timeout, metadata)
  - 定义 `AgentScheduler` ABC
    - `schedule(task: AgentTask) -> str` - 返回 session_id
    - `terminate(session_id: str) -> bool`
    - `get_status(session_id: str) -> AgentStatus`
    - `list_active() -> Dict[str, AgentStatus]`
    - `get_stats() -> Dict[str, Any]`

### Phase 2: EngineAdapter 迁移

- [x] 创建 `monoco/core/scheduler/engines.py`
  - 定义 `EngineAdapter` ABC (build_command, name, supports_yolo_mode)
  - 定义 `EngineFactory` (create, supported_engines)
  - 实现所有具体 Adapter (GeminiAdapter, ClaudeAdapter, QwenAdapter, KimiAdapter)
- [x] 更新 `monoco/features/agent/engines.py` 为向后兼容的 re-export
- [x] 更新 `monoco/features/agent/__init__.py` 导出 engines
- [x] 更新 `monoco/features/agent/worker.py` 中的 import 路径
- [x] 更新测试文件 `tests/test_scheduler_engines.py` 的 import 路径

### Phase 3: LocalProcessScheduler 实现

- [x] 创建 `monoco/core/scheduler/local.py`
  - 实现 `LocalProcessScheduler(AgentScheduler)`
  - 实现进程生命周期管理 (spawn, monitor, timeout, kill)
  - 实现并发配额控制 (asyncio.Semaphore)
  - 集成 EventBus 发布生命周期事件
- [x] 创建 `tests/test_scheduler_local.py` 单元测试
- [x] 集成 `ApoptosisManager` 进行会话清理 (后续优化)

### Phase 4: EventBus 迁移

- [x] 创建 `monoco/core/scheduler/events.py`
  - 定义 `AgentEventType` Enum (所有事件类型)
  - 定义 `AgentEvent` dataclass
  - 定义 `EventBus` 类 (subscribe, unsubscribe, publish, start, stop)
  - 提供全局 `event_bus` 实例
- [x] 更新 `monoco/daemon/events.py` 为向后兼容的 re-export
- [x] 更新 `monoco/daemon/handlers.py` 从 core 导入

### Phase 5: 重构 SchedulerService

- [x] 重构 `monoco/daemon/scheduler.py`
  - `SchedulerService` 使用 `AgentScheduler` 接口
  - 添加 `agent_scheduler: AgentScheduler` 属性
  - 使用 `LocalProcessScheduler` 作为默认实现
  - 添加 `_load_scheduler_config()` 方法加载配置
  - 在 `start()` 中启动 scheduler，在 `stop()` 中停止

### Phase 6: 文档与测试

- [x] 单元测试
  - `tests/test_scheduler_base.py` - AgentScheduler 接口契约测试
  - `tests/test_scheduler_engines.py` - EngineAdapter 测试 (已更新 import)
  - `tests/test_scheduler_local.py` - LocalProcessScheduler 功能测试
- [x] 编写 Provider 接入文档
  - 如何添加新的 Agent Provider
  - `EngineAdapter` 实现指南
  - `AgentScheduler` 实现指南

## 架构设计

### 目标架构

```
┌─────────────────────────────────────────┐
│  monoco/core/scheduler/                 │
│  ├── base.py (AgentScheduler ABC)       │
│  ├── engines.py (EngineAdapter ABC)     │
│  ├── events.py (EventBus)               │
│  └── local.py (LocalProcessScheduler)   │
└─────────────┬───────────────────────────┘
              │ 被依赖（正确方向）
              ▼
┌─────────────────────────────────────────┐
│  monoco/features/agent/                 │
│  ├── manager.py (SessionManager)        │
│  ├── worker.py (Worker)                 │
│  └── 使用: core/scheduler/engines       │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  monoco/daemon/                         │
│  ├── app.py (FastAPI 服务)              │
│  ├── handlers.py (使用 core/scheduler)  │
│  └── scheduler_service.py (调度服务)    │
└─────────────────────────────────────────┘
```

### AgentScheduler 接口

```python
class AgentScheduler(ABC):
    """
    高层调度抽象，屏蔽具体 Agent Provider 细节。
    
    职责：
    - 任务调度与生命周期管理
    - 资源配额控制（并发限制）
    - 状态监控与事件发布
    
    实现：
    - LocalProcessScheduler: 本地进程模式（当前）
    - DockerScheduler: 容器模式（未来）
    - RemoteScheduler: 远程服务模式（未来）
    """
    
    @abstractmethod
    async def schedule(self, task: AgentTask) -> str:
        """调度任务，返回 session_id"""
        pass
    
    @abstractmethod
    async def terminate(self, session_id: str) -> bool:
        """终止任务"""
        pass
    
    @abstractmethod
    def get_status(self, session_id: str) -> AgentStatus:
        """获取任务状态"""
        pass
    
    @abstractmethod
    def list_active(self) -> Dict[str, AgentStatus]:
        """列出所有活跃任务"""
        pass
```

## 依赖

- FEAT-0155: 事件驱动架构重构 (已关闭)
  - 依赖 `EventBus` 实现

## 被依赖

- FEAT-0161: 文件系统事件自动化框架
- FEAT-0162: Agent 联调工作流

## 文件变更预估

| 文件 | 操作 | 说明 |
|------|------|------|
| `monoco/core/scheduler/__init__.py` | 新增 | 模块导出 |
| `monoco/core/scheduler/base.py` | 新增 | AgentScheduler ABC, AgentTask, AgentStatus |
| `monoco/core/scheduler/engines.py` | 新增 | EngineAdapter, EngineFactory, 具体 Adapters |
| `monoco/core/scheduler/local.py` | 新增 | LocalProcessScheduler 实现 |
| `monoco/core/scheduler/events.py` | 新增 | EventBus, AgentEventType, AgentEvent |
| `monoco/features/agent/engines.py` | 修改 | 改为向后兼容的 re-export |
| `monoco/features/agent/__init__.py` | 修改 | 添加 engines 导出 |
| `monoco/features/agent/worker.py` | 修改 | 更新 import 路径 |
| `monoco/daemon/events.py` | 修改 | 改为向后兼容的 re-export |
| `monoco/daemon/handlers.py` | 修改 | 更新 import 路径 |
| `monoco/daemon/scheduler.py` | 修改 | 使用 AgentScheduler 接口 |
| `tests/test_scheduler_base.py` | 新增 | AgentScheduler 接口契约测试 |
| `tests/test_scheduler_local.py` | 新增 | LocalProcessScheduler 功能测试 |
| `tests/test_scheduler_engines.py` | 修改 | 更新 import 路径 |

## Review Comments

### 实现总结 (2026-02-03)

**已完成工作:**

1. **模块结构** - 创建了 `monoco/core/scheduler/` 模块，包含:
   - `base.py`: `AgentScheduler` ABC, `AgentTask`, `AgentStatus`
   - `engines.py`: `EngineAdapter`, `EngineFactory`, 4个具体 Adapter
   - `events.py`: `EventBus`, `AgentEventType`, `AgentEvent`
   - `local.py`: `LocalProcessScheduler` 实现
   - `__init__.py`: 统一导出

2. **向后兼容** - 保留了旧的 import 路径:
   - `monoco/features/agent/engines.py` - 带 DeprecationWarning 的 re-export
   - `monoco/daemon/events.py` - 带 DeprecationWarning 的 re-export

3. **SchedulerService 重构** - 更新为使用 `AgentScheduler` 接口:
   - 添加 `agent_scheduler: AgentScheduler` 属性
   - 使用 `LocalProcessScheduler` 作为默认实现
   - 添加配置加载方法

4. **测试覆盖** - 新增 40 个单元测试:
   - `test_scheduler_base.py`: 8 个测试 (AgentStatus, AgentTask, AgentScheduler 接口)
   - `test_scheduler_engines.py`: 21 个测试 (EngineAdapter, EngineFactory)
   - `test_scheduler_local.py`: 11 个测试 (LocalProcessScheduler)

**架构改进:**
- 核心抽象 (`AgentScheduler`, `EngineAdapter`, `EventBus`) 现在位于 `core/scheduler/`
- 特性层 (`features/agent/`) 依赖于核心层，方向正确
- Daemon 层 (`daemon/`) 通过抽象接口使用调度功能
- 为未来的 `DockerScheduler`, `RemoteScheduler` 奠定了基础

**待完成:**
- 无 (已完成所有核心任务和文档)
