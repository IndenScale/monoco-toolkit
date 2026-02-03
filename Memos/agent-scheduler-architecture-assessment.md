# Agent Scheduler 架构评估报告

> **Context**: Architecture Assessment  
> **Date**: 2026-02-03  
> **Author**: Agent (Kimi CLI)  

---

## 执行摘要

本次评估针对用户提出的"三步走"策略，对现有 Epic/Issue 划分和架构清晰度进行了深入调研。核心结论是：**现有架构已具备良好的基础，但 Feature 粒度确实偏大，需要按三步走策略重新划分**。

---

## 一、现有架构盘点

### 1.1 已存在的核心组件

| 组件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| **EngineAdapter (抽象层)** | `monoco/features/agent/engines.py` | ✅ 已实现 | 已定义 `EngineAdapter` ABC，支持 Gemini/Claude/Qwen/Kimi |
| **EventBus (事件总线)** | `monoco/daemon/events.py` | ✅ 已实现 | FEAT-0155 已实现，支持异步发布/订阅 |
| **Event Handlers** | `monoco/daemon/handlers.py` | ✅ 已实现 | Architect/Engineer/Reviewer/Coroner 处理器 |
| **SchedulerService** | `monoco/daemon/scheduler.py` | ✅ 已实现 | 事件驱动的调度器，已替换轮询架构 |
| **SessionManager** | `monoco/features/agent/manager.py` | ✅ 已实现 | Session 生命周期管理 |
| **Dropzone Watcher** | `monoco/core/ingestion/watcher.py` | ✅ 已实现 | 文件系统监听（Mailroom 使用） |

### 1.2 现有 Epic 归属关系

```
EPIC-0000 (Root)
├── EPIC-0025: Monoco Daemon Orchestrator (AgentScheduling)
│   ├── FEAT-0155 (Closed): 重构为事件驱动架构
│   ├── FEAT-0160 (Open): IM Message Loop
│   └── FEAT-0149 (Backlog/Frozen): Native Hook System
├── EPIC-0032: Collaboration Bus
│   └── EPIC-0033: IM Integration (钉钉/飞书)
└── ...
```

### 1.3 关键发现：抽象层已存在

**用户第一步要求的 "AgentScheduler 抽象类" 实际上已经存在**：

```python
# monoco/features/agent/engines.py
class EngineAdapter(ABC):
    """Abstract base class for agent engine adapters."""
    
    @abstractmethod
    def build_command(self, prompt: str) -> List[str]: ...
    
    @property
    @abstractmethod
    def name(self) -> str: ...

class EngineFactory:
    _adapters = {
        "gemini": GeminiAdapter,
        "claude": ClaudeAdapter,
        "qwen": QwenAdapter,
        "kimi": KimiAdapter,
    }
```

**但存在架构层级问题**：
- `EngineAdapter` 位于 `features/agent/` 层，属于具体功能实现
- 缺少一个更高层的 `AgentScheduler` 抽象来统一调度策略
- 调度逻辑分散在 `daemon/scheduler.py` 和 `daemon/handlers.py`

---

## 二、三步走策略评估

### 2.1 第一步：AgentScheduler 抽象类

**现状评估**: ⚠️ **部分实现，需要重构**

| 需求 | 现状 | 差距 |
|------|------|------|
| 屏蔽 Provider 细节 | `EngineAdapter` 已实现 | ✅ 满足 |
| 统一调度接口 | 分散在多个 Handler 中 | ❌ 需要抽象 |
| 调度策略可插拔 | 硬编码在 handlers.py | ❌ 需要重构 |

**建议实现**:
```python
# 新增: monoco/core/scheduler/base.py
class AgentScheduler(ABC):
    """高层调度抽象，屏蔽具体 Agent Provider 细节"""
    
    @abstractmethod
    async def schedule(self, task: AgentTask) -> str: ...
    
    @abstractmethod
    async def terminate(self, session_id: str) -> bool: ...
    
    @abstractmethod
    def get_status(self, session_id: str) -> AgentStatus: ...

# 具体实现
class LocalProcessScheduler(AgentScheduler): ...
class DockerScheduler(AgentScheduler): ...  # 未来扩展
class RemoteScheduler(AgentScheduler): ...  # 未来扩展
```

**对应 Feature**: 
- 建议新建 `FEAT-0165: AgentScheduler 抽象层与 Provider 解耦`
- 将现有 `EngineAdapter` 提升为 `AgentScheduler` 的子组件

---

### 2.2 第二步：事件驱动的自动化框架

**现状评估**: ✅ **已基本实现，需要完善**

FEAT-0155 已完成核心重构：

```python
# monoco/daemon/events.py - 已存在
class AgentEventType(Enum):
    MEMO_CREATED = "memo.created"
    MEMO_THRESHOLD = "memo.threshold"
    ISSUE_STAGE_CHANGED = "issue.stage_changed"
    SESSION_COMPLETED = "session.completed"
    ...

class EventBus:
    async def publish(self, event_type: AgentEventType, payload: Dict): ...
    def subscribe(self, event_type: AgentEventType, handler: EventHandler): ...
```

**但缺少文件系统事件到业务事件的映射层**：

| 需求 | 现状 | 差距 |
|------|------|------|
| 监听特定目录 | `DropzoneWatcher` 已实现 | ✅ 满足 |
| 监听特定文件变化 | 未抽象为通用机制 | ⚠️ 需要封装 |
| 字段变化识别 | 未实现 | ❌ 需要开发 |
| 触发器注册机制 | Handler Registry 已存在 | ✅ 满足 |

**建议实现**:
```python
# 新增: monoco/core/automation/triggers.py
class FileTrigger:
    """文件变化触发器"""
    path: Path
    field_extractor: Callable  # 提取关键字段
    condition: Callable        # 触发条件
    action: str               # 对应事件类型

class AutomationFramework:
    """自动化框架，管理所有触发器"""
    def register_trigger(self, trigger: FileTrigger): ...
    def watch(self): ...
```

**对应 Feature**:
- 建议新建 `FEAT-0166: 文件系统事件到业务事件的自动化映射框架`
- 与现有 `DropzoneWatcher` 整合

---

### 2.3 第三步：Agent 联调工作流

**现状评估**: ⚠️ **概念清晰，实现分散**

用户描述的 workflow 是：
```
User writes memo/tasks 
    ↓ (triggers)
Architect analyzes 
    ↓ (creates)
Issue Ticket 
    ↓ (triggers when stage=doing)
Engineer implements 
    ↓ (triggers when PR created)
Reviewer reviews
```

**现有实现状态**：

| 环节 | 实现状态 | 触发机制 |
|------|----------|----------|
| Memo → Architect | ✅ 已实现 | `MEMO_THRESHOLD` 事件 |
| Issue doing → Engineer | ✅ 已实现 | `ISSUE_STAGE_CHANGED` 事件 |
| Engineer → Reviewer | ❌ **已移除链式触发** | 现为 `PR_CREATED` 事件 |
| 文件变化 → 事件 | ⚠️ 部分实现 | 需完善 |

**关键问题**：
1. **Agent 之间确实没有直接调度关系** - 这是 FEAT-0155 的设计决策（去链式化）
2. **但缺少对 memo/tasks.md 的监听** - 目前只监听 `Memos/inbox.md`
3. **Issue ticket 状态变化监听已存在** - `ISSUE_STAGE_CHANGED`

**建议实现**:
```python
# 扩展: monoco/daemon/handlers.py
class TaskFileHandler(AgentEventHandler):
    """监听 tasks.md 或特定 Issue 文件变化"""
    # 当用户修改特定字段时触发对应 Agent

class MemoFileHandler(AgentEventHandler):
    """监听 Memos/ 目录变化"""
    # 已部分实现，需要扩展
```

**对应 Feature**:
- 建议新建 `FEAT-0167: Agent 联调工作流 - 端到端自动化`
- 整合现有 handlers，添加 TaskFileHandler

---

## 三、架构清晰度评估

### 3.1 当前架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Collaboration Bus                        │
│  (IM, Kanban, Memo, IDE Extension)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │ Filesystem as API
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   Ingestion Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Dropzone     │  │ Memo Watcher │  │ Issue Watcher│      │
│  │ (Mailroom)   │  │ (inbox.md)   │  │ (status)     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    EventBus                                 │
│  (Central async event system)                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ↓             ↓             ↓
┌──────────────┐ ┌──────────┐ ┌──────────┐
│   Architect  │ │ Engineer │ │ Reviewer │
│   Handler    │ │ Handler  │ │ Handler  │
└──────┬───────┘ └────┬─────┘ └────┬─────┘
       │              │            │
       ↓              ↓            ↓
┌─────────────────────────────────────────┐
│        AgentScheduler (抽象层)          │
│  ┌─────────────────────────────────┐   │
│  │  EngineAdapter (Gemini/Claude/...)│  │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 3.2 架构清晰度评分

| 维度 | 评分 | 说明 |
|------|------|------|
| **分层清晰** | 7/10 | 各层职责基本明确，但调度抽象层位置偏低 |
| **事件驱动** | 8/10 | EventBus 已实现，但文件→事件映射不够通用 |
| **扩展性** | 6/10 | 新增 Agent Provider 需要修改 engines.py |
| **可测试性** | 6/10 | Handler 与 SessionManager 耦合较紧 |
| **文档化** | 7/10 | Domain 定义清晰，但实现细节文档不足 |

---

## 四、建议的 Issue 重构方案

### 4.1 关闭/归档现有过大 Feature

| 现有 Feature | 建议操作 | 理由 |
|--------------|----------|------|
| FEAT-0160 (IM Message Loop) | 拆分为 3 个子 Feature | 粒度太大，包含网关、Adapter、Watcher、Agent 集成 |

### 4.2 新建三步走 Feature

```
EPIC-0025: Monoco Daemon Orchestrator
├── Phase 1: 抽象层
│   └── FEAT-0165: AgentScheduler 抽象层与 Provider 解耦
│       - [ ] 定义 AgentScheduler ABC
│       - [ ] 重构 EngineAdapter 为子组件
│       - [ ] 实现 LocalProcessScheduler
│       - [ ] 编写 Provider 接入文档
│
├── Phase 2: 事件框架
│   └── FEAT-0166: 文件系统事件到业务事件的自动化映射框架
│       - [ ] 抽象 FileTrigger 机制
│       - [ ] 实现字段变化检测 (YAML Front Matter)
│       - [ ] 统一 Dropzone/Memo/Issue 监听
│       - [ ] 触发器配置化 (YAML/JSON)
│
└── Phase 3: 联调工作流
    └── FEAT-0167: Agent 联调工作流 - 端到端自动化
        - [ ] 实现 TaskFileHandler (监听 tasks.md)
        - [ ] 实现 IssueStageHandler (监听 Issue 状态)
        - [ ] 实现 Proposal 确认机制
        - [ ] 完整 workflow 测试
```

### 4.3 与现有 Feature 的关系

```
FEAT-0165 ──┬──> 依赖: FEAT-0155 (EventBus)
            └──> 被依赖: FEAT-0166, FEAT-0167

FEAT-0166 ──┬──> 依赖: FEAT-0165, FEAT-0155
            ├──> 依赖: FEAT-0153 (Mailroom - DropzoneWatcher)
            └──> 被依赖: FEAT-0167, FEAT-0160

FEAT-0167 ──┬──> 依赖: FEAT-0165, FEAT-0166
            └──> 依赖: FEAT-0160 (IM 集成)
```

---

## 五、关键架构决策建议

### 5.1 决策 1: AgentScheduler 的位置

**选项 A**: 保留在 `features/agent/` (现状)
- 优点：与现有 EngineAdapter 同层
- 缺点：功能层包含核心抽象，违反分层原则

**选项 B**: 迁移到 `core/scheduler/` (推荐)
- 优点：核心抽象位于 core 层，features 层依赖 core 层
- 缺点：需要重构 import 路径

**建议**: 选项 B，建立 `monoco/core/scheduler/` 模块

### 5.2 决策 2: 文件监听统一

**现状**: 
- `DropzoneWatcher` 监听 Mailroom
- `SchedulerService._memo_watcher_loop` 监听 Memos
- `SchedulerService._issue_watcher_loop` 监听 Issues

**建议**: 统一为 `FilesystemEventBridge`
```python
# monoco/core/automation/fs_bridge.py
class FilesystemEventBridge:
    """统一文件系统事件桥接"""
    watchers: List[BaseWatcher]
    event_bus: EventBus
```

### 5.3 决策 3: Agent 触发策略

**用户要求**: "Agent 之间没有调度关系，而是通过检测文件状态触发"

**现状**: 已实现去链式化（FEAT-0155）
- Engineer 完成后**不**自动触发 Reviewer
- Reviewer 仅由 `PR_CREATED` 事件触发

**建议**: 保持此设计，并在文档中明确为"事件驱动、去链式化架构"

---

## 六、结论与行动项

### 6.1 总体结论

| 问题 | 结论 |
|------|------|
| 现有 Feature 是否脚踏实地？ | **否**，粒度偏大，需要按三步走拆分 |
| 架构是否清晰？ | **基本清晰**，但存在分层问题和抽象层级问题 |
| 三步走策略是否合理？ | **合理**，且与现有实现方向一致 |

### 6.2 立即行动项

1. **创建 FEAT-0165**: AgentScheduler 抽象层
   - 负责人: Agent
   - 优先级: High
   - 阻塞: FEAT-0166, FEAT-0167

2. **重构 EngineAdapter**: 迁移到 core/scheduler/
   - 作为 FEAT-0165 的子任务

3. **拆分 FEAT-0160**: IM Message Loop 拆分为更小粒度
   - FEAT-0160-a: IM Gateway (钉钉/飞书 Adapter)
   - FEAT-0160-b: IM Filesystem Bridge
   - FEAT-0160-c: IMArchitect Agent 集成

4. **创建 FEAT-0166**: 文件系统事件自动化框架
   - 负责人: Agent
   - 优先级: High
   - 依赖: FEAT-0165

5. **创建 FEAT-0167**: Agent 联调工作流
   - 负责人: Agent
   - 优先级: Medium
   - 依赖: FEAT-0165, FEAT-0166

---

## 附录：相关代码引用

### A.1 现有 EngineAdapter
```python
# monoco/features/agent/engines.py:12-34
class EngineAdapter(ABC):
    """Abstract base class for agent engine adapters."""
    @abstractmethod
    def build_command(self, prompt: str) -> List[str]: ...
```

### A.2 现有 EventBus
```python
# monoco/daemon/events.py:58-66
class EventBus:
    """Central async event bus for Agent scheduling."""
    def subscribe(self, event_type: AgentEventType, handler: EventHandler): ...
    async def publish(self, event_type: AgentEventType, payload: Dict): ...
```

### A.3 现有 Handler 架构
```python
# monoco/daemon/handlers.py:23-53
class AgentEventHandler(ABC):
    """Base class for agent event handlers."""
    async def should_handle(self, event: AgentEvent) -> bool: ...
    async def handle(self, event: AgentEvent): ...
```

---

*Report Generated: 2026-02-03*  
*Based on codebase state at commit: HEAD*
