# Daemon 架构提议评估报告

> **Context**: Architecture Proposals Review  
> **Date**: 2026-02-03  
> **Author**: Agent (Kimi CLI)  

---

## 执行摘要

对用户提出的三个架构提议进行评估：

| 提议 | 评估结论 | 优先级 |
|------|----------|--------|
| 1. AgentScheduler 提取到 core 目录 | **强烈推荐** | High |
| 2. Daemon 成为独立 feature | **有条件支持** | Medium |
| 3. Daemon 引入 SQLite | **谨慎反对** | Low |

---

## 提议 1: AgentScheduler 提取到 core 目录

### 1.1 当前架构问题

```
当前依赖关系（问题）：
┌─────────────────────────────────────────┐
│  monoco/daemon/scheduler.py             │
│  - SchedulerService                     │
│  - 依赖: features/agent/manager.py      │
└─────────────┬───────────────────────────┘
              │ 反向依赖（坏味道）
              ▼
┌─────────────────────────────────────────┐
│  monoco/features/agent/                 │
│  - manager.py (SessionManager)          │
│  - engines.py (EngineAdapter) ← 抽象层  │
│  - worker.py (Worker)                   │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  monoco/daemon/handlers.py              │
│  - AgentEventHandler                    │
│  - 依赖: features/agent/manager.py      │
└─────────────────────────────────────────┘
```

**问题识别**:
1. **循环依赖风险**: `daemon/` 依赖 `features/agent/`，而 `features/agent/` 理论上不应依赖 `daemon/`
2. **抽象层位置错误**: `EngineAdapter` ABC 位于 `features/` 层，违反分层原则
3. **调度逻辑分散**: `SchedulerService` 在 `daemon/`，但调度策略在 `handlers.py`

### 1.2 提议架构

```
提议依赖关系（清晰）：
┌─────────────────────────────────────────┐
│  monoco/core/scheduler/                 │
│  - base.py (AgentScheduler ABC)         │
│  - engines.py (EngineAdapter ABC)       │
│  - local.py (LocalProcessScheduler)     │
│  - events.py (EventBus) ← 从 daemon 迁移 │
└─────────────┬───────────────────────────┘
              │ 被依赖（正确）
              ▼
┌─────────────────────────────────────────┐
│  monoco/features/agent/                 │
│  - manager.py (SessionManager)          │
│  - worker.py (Worker)                   │
│  - 使用: core/scheduler/engines         │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  monoco/daemon/                         │
│  - app.py (FastAPI 服务)                │
│  - handlers.py (使用 core/scheduler)    │
│  - scheduler_service.py (调度服务)      │
└─────────────────────────────────────────┘
```

### 1.3 具体重构方案

```python
# 新增: monoco/core/scheduler/__init__.py
from .base import AgentScheduler, AgentTask, AgentStatus
from .engines import EngineAdapter, EngineFactory
from .events import EventBus, AgentEventType

__all__ = [
    "AgentScheduler",
    "AgentTask", 
    "AgentStatus",
    "EngineAdapter",
    "EngineFactory",
    "EventBus",
    "AgentEventType",
]
```

```python
# 新增: monoco/core/scheduler/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AgentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"

@dataclass
class AgentTask:
    """调度任务定义"""
    task_id: str
    role_name: str
    issue_id: str
    prompt: str
    engine: str = "gemini"
    timeout: Optional[int] = None
    metadata: Dict[str, Any] = None

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

```python
# 迁移: monoco/features/agent/engines.py → monoco/core/scheduler/engines.py
# 保持 EngineAdapter ABC 不变

class EngineAdapter(ABC):
    """Agent Provider 适配器抽象"""
    
    @abstractmethod
    def build_command(self, prompt: str) -> List[str]: ...
    
    @property
    @abstractmethod
    def name(self) -> str: ...
```

```python
# 迁移: monoco/daemon/events.py → monoco/core/scheduler/events.py
# EventBus 是调度基础设施，不应与 FastAPI daemon 耦合
```

### 1.4 评估结论

| 维度 | 评分 | 说明 |
|------|------|------|
| **架构清晰度** | ⭐⭐⭐⭐⭐ | 明确分层，消除反向依赖 |
| **可测试性** | ⭐⭐⭐⭐⭐ | 核心抽象可独立测试 |
| **扩展性** | ⭐⭐⭐⭐⭐ | 易于添加新 Scheduler 实现 |
| **迁移成本** | ⭐⭐⭐ | 中等，需要修改 import 路径 |

**建议**: **立即执行**
- 创建 `monoco/core/scheduler/` 模块
- 迁移 `EngineAdapter`, `EventBus` 到 core 层
- 重构 `SchedulerService` 依赖关系

---

## 提议 2: Daemon 成为独立 Feature

### 2.1 当前 Daemon 职责分析

```
monoco/daemon/ 当前内容：
├── app.py              # FastAPI HTTP/SSE 服务
├── commands.py         # CLI 命令 (monoco daemon start/stop)
├── events.py           # EventBus (应迁移到 core)
├── handlers.py         # Agent 事件处理器
├── mailroom_service.py # Mailroom 服务集成
├── models.py           # Pydantic 请求/响应模型
├── scheduler.py        # SchedulerService
├── services.py         # ProjectManager, SemaphoreManager, Broadcaster
├── stats.py            # 统计计算
├── triggers.py         # 触发策略
└── reproduce_stats.py  # 复现统计
```

### 2.2 职责边界分析

| 组件 | 当前位置 | 建议位置 | 理由 |
|------|----------|----------|------|
| EventBus | `daemon/events.py` | `core/scheduler/events.py` | 核心基础设施 |
| EngineAdapter | `features/agent/engines.py` | `core/scheduler/engines.py` | 核心抽象 |
| AgentScheduler | 分散 | `core/scheduler/base.py` | 核心抽象 |
| SchedulerService | `daemon/scheduler.py` | `features/orchestrator/` | 业务逻辑 |
| Handlers | `daemon/handlers.py` | `features/orchestrator/` | 业务逻辑 |
| FastAPI App | `daemon/app.py` | `features/api/` 或保持 | HTTP 接口层 |
| MailroomService | `daemon/mailroom_service.py` | `features/mailroom/` | 独立 feature |

### 2.3 提议架构

```
方案 A: 完全独立为 feature/orchestrator
┌─────────────────────────────────────────┐
│  monoco/features/orchestrator/          │
│  - __init__.py                          │
│  - service.py (SchedulerService)        │
│  - handlers.py (Agent handlers)         │
│  - triggers.py                          │
│  - semaphore.py (SemaphoreManager)      │
│  - cli.py (orchestrator 命令)           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  monoco/features/api/                   │
│  - __init__.py                          │
│  - server.py (FastAPI app)              │
│  - routes/                              │
│  - middleware/                          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  monoco/core/scheduler/                 │
│  - 核心抽象层                           │
└─────────────────────────────────────────┘
```

```
方案 B: 保持 daemon 目录，但重新定位
monoco/
├── core/
│   └── scheduler/          # 核心调度抽象
├── features/
│   ├── agent/              # Agent 生命周期
│   ├── mailroom/           # 文档摄取
│   └── ...
└── daemon/                 # 运行时进程
    ├── __main__.py         # 入口
    ├── app.py              # FastAPI (仅 HTTP 层)
    ├── commands.py         # CLI
    └── plugins/            # 插件目录
        ├── orchestrator.py # 加载 orchestrator
        ├── mailroom.py     # 加载 mailroom
        └── api.py          # 加载 API routes
```

### 2.4 关键决策点

**问题**: Daemon 的"文件监听、生产事件、触发 action"职责是否应该独立？

**分析**:

| 方面 | 独立为 Feature | 保持 Daemon 目录 |
|------|----------------|------------------|
| **概念清晰** | ✅ Orchestrator 职责明确 | ⚠️ Daemon 概念较模糊 |
| **启动复杂度** | ⚠️ 需要决定启动哪些 feature | ✅ 统一 daemon 启动 |
| **资源占用** | ✅ 可按需启动 | ⚠️ 可能启动不必要服务 |
| **代码耦合** | ✅ 降低耦合 | ⚠️ daemon/ 内部耦合较高 |
| **迁移成本** | ⚠️ 高 | ✅ 低 |

### 2.5 评估结论

**建议**: **渐进式重构，而非完全独立**

理由：
1. **当前 Daemon 不仅是编排器**: 还包含 API Server、Mailroom、Git Monitor 等
2. **启动时序复杂**: Orchestrator 依赖 Agent、Issue、Memo 等多个 features
3. **配置分散问题**: 独立 feature 会增加配置复杂度

**具体建议**:
```
阶段 1 (立即):
- 将 EventBus, EngineAdapter 迁移到 core/scheduler/
- 保持 daemon/ 目录结构

阶段 2 (未来):
- 如果 orchestrator 逻辑继续膨胀，再考虑独立为 feature
- 当前 567 行的 app.py + 350 行的 services.py 尚可控
```

---

## 提议 3: Daemon 引入 SQLite

### 3.1 当前状态存储方式

```
当前存储（文件系统为主）：
.monoco/
├── state.json              # WorkspaceState (JSON)
├── workspace.yaml          # 工作区配置
├── project.yaml            # 项目配置
├── sessions/               # Session 持久化
│   ├── <uuid-1>.json
│   ├── <uuid-2>.json
│   └── ...
└── artifacts/
    └── manifest.jsonl      # Artifact 清单 (JSONL)
```

```python
# monoco/core/state.py - 当前实现
class WorkspaceState(BaseModel):
    last_active_project_id: Optional[str] = None
    
    def save(self, workspace_root: Path):
        state_file = workspace_root / ".monoco" / "state.json"
        # JSON 序列化
```

### 3.2 SQLite 适用场景分析

| 数据类型 | 当前格式 | 是否适合 SQLite | 理由 |
|----------|----------|-----------------|------|
| Session 状态 | JSON 文件 | ⚠️ 中性 | 读写频繁，但结构简单 |
| Event Log | 内存 | ✅ 适合 | 时序数据，量大，无需 Git |
| Issue 数据 | Markdown | ❌ 不适合 | 需要 Git 追踪 |
| Memo 数据 | Markdown | ❌ 不适合 | 需要 Git 追踪 |
| Workspace State | JSON | ❌ 不适合 | 结构简单，JSON 足够 |
| Artifact Manifest | JSONL | ⚠️ 中性 | 只追加，JSONL 更高效 |

### 3.3 用户担忧分析

> "event 这种轻量级的消息似乎不太适合被 git 追踪，更适合作为 log"

**正确理解**:
- Event 确实**不应该**被 Git 追踪
- 但 Event 也**不应该**被长期存储
- Event 是**瞬时状态**，用于触发动作，而非持久化数据

```python
# 当前 EventBus 实现 (内存队列)
class EventBus:
    def __init__(self):
        self._event_queue: asyncio.Queue = asyncio.Queue()
    
    async def publish(self, event_type: AgentEventType, payload: Dict):
        event = AgentEvent(type=event_type, payload=payload)
        await self._event_queue.put(event)  # 仅内存，不持久化
```

### 3.4 SQLite 引入的复杂性

```
引入 SQLite 后的架构变化：

Before:
┌─────────────┐     ┌─────────────┐
│   Daemon    │────▶│  JSON Files │
│             │     │  (Git 追踪) │
└─────────────┘     └─────────────┘

After (with SQLite):
┌─────────────┐     ┌─────────────┐
│   Daemon    │────▶│  JSON Files │◀── Git 追踪
│             │     │  (Issues等) │
│             │     ├─────────────┤
│             │────▶│   SQLite    │◀── .gitignore
│             │     │  (Events等) │
└─────────────┘     └─────────────┘
              
新问题：
1. 双数据源一致性
2. 备份策略（SQLite 需要单独备份）
3. 并发访问（SQLite 文件锁）
4. 迁移复杂度
```

### 3.5 替代方案：结构化日志

如果目标是"Event 不适合 Git，适合作为 log"，更轻量的方案是**结构化日志**:

```python
# 方案: 使用结构化日志而非 SQLite
import structlog

logger = structlog.get_logger("monoco.events")

# Event 作为日志，不存储在 Git
async def publish(self, event_type: AgentEventType, payload: Dict):
    event = AgentEvent(type=event_type, payload=payload)
    
    # 1. 内存队列（立即消费）
    await self._event_queue.put(event)
    
    # 2. 结构化日志（可选，用于审计）
    logger.info(
        "event_published",
        event_type=event_type.value,
        payload=payload,
        timestamp=event.timestamp.isoformat(),
    )
```

日志输出到 `.monoco/logs/events.log`，并在 `.gitignore` 中排除。

### 3.6 评估结论

| 维度 | SQLite | 结构化日志 | 当前方案 (内存) |
|------|--------|------------|-----------------|
| 复杂度 | 高 | 低 | 最低 |
| 查询能力 | 强 | 弱 (需 grep) | 无 |
| 持久化 | 是 | 是 | 否 |
| 适合 Event | 过度设计 | ✅ 合适 | ⚠️ 重启丢失 |
| 运维成本 | 中 | 低 | 最低 |

**建议**: **暂不引入 SQLite**

理由：
1. **当前 Event 是瞬时数据**: 不需要长期存储
2. **如果需要审计日志**: 使用结构化日志 (JSON Lines) 足够
3. **如果未来需要复杂查询**: 再考虑 SQLite 或专用时序数据库

**具体建议**:
```python
# 如果需要 Event 持久化，使用 JSON Lines
# .monoco/logs/events.jsonl (gitignored)

{"timestamp": "2026-02-03T08:30:00Z", "type": "ISSUE_STAGE_CHANGED", "payload": {...}}
{"timestamp": "2026-02-03T08:30:05Z", "type": "SESSION_STARTED", "payload": {...}}
```

---

## 综合建议与行动项

### 立即执行 (High Priority)

1. **创建 `monoco/core/scheduler/` 模块**
   ```
   monoco/core/scheduler/
   ├── __init__.py
   ├── base.py          # AgentScheduler ABC
   ├── engines.py       # EngineAdapter (迁移)
   ├── events.py        # EventBus (迁移)
   └── local.py         # LocalProcessScheduler
   ```

2. **迁移 EngineAdapter**
   - 从 `features/agent/engines.py` → `core/scheduler/engines.py`
   - 更新所有 import 路径

### 短期执行 (Medium Priority)

3. **迁移 EventBus**
   - 从 `daemon/events.py` → `core/scheduler/events.py`
   - `daemon/handlers.py` 从 core 导入

4. **重构 SchedulerService**
   - 实现 `AgentScheduler` ABC
   - `SchedulerService` 改为使用 `AgentScheduler` 接口

### 暂不执行 (Low Priority / 待定)

5. **Daemon 独立为 Feature**: 当前复杂度可控，暂不迁移
6. **引入 SQLite**: 使用结构化日志作为过渡方案，待有明确需求再评估

---

## 附录：重构后的目录结构

```
monoco/
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── git.py
│   ├── state.py
│   └── scheduler/              # 新增
│       ├── __init__.py
│       ├── base.py             # AgentScheduler ABC
│       ├── engines.py          # EngineAdapter
│       ├── events.py           # EventBus
│       └── local.py            # LocalProcessScheduler
│
├── features/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── manager.py          # SessionManager (使用 core/scheduler)
│   │   ├── worker.py           # Worker
│   │   └── models.py           # RoleTemplate
│   ├── issue/
│   ├── memo/
│   └── mailroom/               # 未来可能独立
│
└── daemon/                     # 保持，但职责更清晰
    ├── __init__.py
    ├── __main__.py
    ├── app.py                  # FastAPI (仅 HTTP 层)
    ├── commands.py             # CLI
    ├── handlers.py             # Agent handlers (使用 core/scheduler)
    ├── scheduler_service.py    # 调度服务 (使用 core/scheduler)
    ├── services.py             # ProjectManager, SemaphoreManager
    └── models.py               # Pydantic models
```

---

*Report Generated: 2026-02-03*
