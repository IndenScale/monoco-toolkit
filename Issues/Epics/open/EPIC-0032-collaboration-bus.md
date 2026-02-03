---
id: EPIC-0032
uid: 6a27eb
type: epic
status: open
stage: doing
title: 协作总线：文件系统作为总线，事件驱动架构
created_at: '2026-02-01T20:24:49'
updated_at: '2026-02-03T09:55:00'
parent: EPIC-0000
dependencies:
- EPIC-0025
related: []
domains:
- CollaborationBus
files:
- Memos/architecture-layer-analysis.md
tags:
- '#EPIC-0000'
- '#EPIC-0032'
- '#EPIC-0025'
- narrative
- collaboration
- filesystem-as-bus
- event-driven
criticality: high
opened_at: '2026-02-01T20:24:49'
progress: 0/1
files_count: 1
---

## EPIC-0032: 协作总线：文件系统作为总线，事件驱动架构

> **核心架构原则**: Filesystem as Bus / Event-Driven Architecture
> 
> 协作总线不是传统意义上的消息队列，而是**文件系统 + 事件驱动**的轻量级架构。

## Objective

构建统一的人机协作总线，以文件系统为媒介，事件驱动为机制，承载信息传递、反馈收集与演化信号。

使人类开发者与 Agent 能够高效协作，并将协作过程中的洞察转化为系统改进。

## 核心架构原则

### 1. Filesystem as Bus (文件系统作为总线)

```
┌─────────────┐    Filesystem     ┌─────────────┐
│   Human     │◄───(Markdown)────►│    Agent    │
│  (IDE/CLI)  │    (JSON/YAML)    │  (Architect/│
│             │                   │  Engineer/  │
│             │◄─────────────────►│  Reviewer)  │
└─────────────┘                   └─────────────┘
       │                                 │
       └─────────── Issues/ ─────────────┘
       └─────────── Memos/ ──────────────┘
       └─────────── tasks.md ────────────┘
```

- **Issues/**: 工作单元的状态流转 (draft → doing → review → done)
- **Memos/**: 快速笔记与上下文传递
- **tasks.md**: 任务清单，触发 Architect 分析
- **Kanban/**: 工作流可视化 (只读视图)

### 2. Event-Driven Architecture (事件驱动架构)

```
文件变化 → Watcher → EventBus → ActionRouter → Action → 文件写入
                                              │
                                              ├── SpawnAgentAction
                                              ├── SendNotificationAction (future)
                                              └── GitPushAction (future)
```

- **Watcher**: 监听文件系统变化 (Layer 1)
- **EventBus**: 异步事件总线
- **ActionRouter**: 事件路由到 Action (Layer 2)
- **Action**: 具体执行逻辑 (Layer 3)

### 3. 去链式化 (Decoupled Agents)

**反模式** (避免):
```
Architect → Engineer → Reviewer  (直接调用，强耦合)
```

**正模式** (采用):
```
Architect ──► Issues/FEAT-001.md (stage=draft)
                      │
                      ▼ (人工改 stage=doing)
              IssueStageHandler ──► 调度 Engineer
                                          │
                                          ▼
                                    Engineer ──► PR
                                                      │
                                                      ▼
                                              PRCreatedHandler ──► 调度 Reviewer
```

## Acceptance Criteria

- [ ] **Filesystem as Bus**: 所有协作通过文件读写完成，无直接进程间调用
- [ ] **Event-Driven**: 文件变化触发事件，事件驱动 Action 执行
- [ ] **Decoupled Agents**: Agent 间无直接调度关系，通过文件状态解耦
- [ ] **Human-in-the-Loop**: 关键节点 (stage 变更) 由人工确认
- [ ] **Observable**: 所有状态可通过 `cat`/`ls`/`grep` 观察

## Technical Tasks

### Phase 1: Core Infrastructure (依赖 EPIC-0025)
> 由 EPIC-0025 FEAT-0160/0161/0162 实现

- [ ] **FEAT-0160**: AgentScheduler 抽象层 (Layer 3)
- [ ] **FEAT-0161**: 文件系统事件自动化框架 (Layer 1+2)
- [ ] **FEAT-0162**: Agent 联调工作流 (Integration)

### Phase 2: Interface Layer (只读/写入视图)
> 界面是文件系统的视图，不直接参与调度

- [ ] **FEAT-Kanban-View**: Kanban 看板作为工作流可视化
  - 只读展示 Issues/ 目录状态
  - 支持拖拽变更 stage (实际修改文件)
- [ ] **FEAT-IDE-Integration**: IDE Extension 作为协作界面
  - Issue 可视化 (读取 Issues/)
  - Agent 状态展示 (读取 sessions/)
  - 快捷操作 (修改文件 front matter)

### Phase 3: Feedback Collection (文件形式)
> 反馈以文件形式收集，非数据库

- [ ] **FEAT-Agent-Feedback**: Agent 报告写入 Memos/
- [ ] **FEAT-Human-Feedback**: 人类反馈写入 Memos/
- [ ] **FEAT-Friction-Capture**: 摩擦点自动记录到 Memos/

### Phase 4: Future Extensions (未来工作)
> 以下特性在核心架构稳定后考虑

- [ ] **Notification System**: 通知机制 (邮件/IM)
- [ ] **Evolution Signaling**: 改进建议流转机制

## 协作流程示例

### 流程 1: Task → Issue → Engineer → PR → Reviewer

```
1. Human 写入 tasks.md
   └── "需要实现用户认证功能"

2. TaskWatcher 检测到变化
   └── 发布 TASK_FILE_CHANGED 事件

3. ActionRouter 路由到 SpawnAgentAction(Architect)
   └── Architect 读取 tasks.md
   └── Architect 创建 Issues/Features/open/FEAT-XXX.md
   └── (stage=draft, 等待人工确认)

4. Human 修改 FEAT-XXX.md (stage=doing)
   └── IssueWatcher 检测到变化
   └── 发布 ISSUE_STAGE_CHANGED 事件

5. ActionRouter 路由到 SpawnAgentAction(Engineer)
   └── Engineer 读取 Issue 内容
   └── Engineer 编码实现
   └── Engineer 提交 PR

6. PRCreatedHandler 检测到 PR
   └── 发布 PR_CREATED 事件
   └── ActionRouter 路由到 SpawnAgentAction(Reviewer)
   └── Reviewer 审查代码
   └── Reviewer 写入审查报告到 Memos/

7. Human 根据审查报告决定合并
   └── 人工执行合并操作
   └── Human 修改 Issue (stage=done)
```

### 流程 2: Memo 累积 → Architect 批量处理

```
1. Human 多次写入 Memos/inbox.md
   └── 累积 pending memos >= 阈值

2. MemoWatcher 检测到阈值触发
   └── 发布 MEMO_THRESHOLD_REACHED 事件

3. ActionRouter 路由到 SpawnAgentAction(Architect)
   └── Architect 读取累积的 memos
   └── Architect 分析后创建 Issues/
   └── Architect 清空或归档已处理的 memos
```

## 与 EPIC-0025 的关系

```
EPIC-0025: Monoco Daemon Orchestrator
├── 提供: AgentScheduler (Layer 3)
├── 提供: Watcher + ActionRouter (Layer 1+2)
└── 提供: Agent Collaboration Workflow

EPIC-0032: Collaboration Bus (本 Epic)
├── 使用: EPIC-0025 提供的基础设施
├── 定义: 协作流程与规范
├── 实现: 界面层 (Kanban/IDE)
└── 实现: 反馈收集机制
```

## Review Comments

### 2026-02-03 架构更新

**重大变更**:
1. **强调 Filesystem as Bus**: 明确文件系统是协作核心媒介
2. **强调 Event-Driven**: 明确事件驱动是核心机制
3. **删除 IM Integration**: 集成为未来工作，非当前核心
4. **去链式化**: Agent 间不直接调用，通过文件状态解耦
5. **Human-in-the-Loop**: 关键节点由人工确认 (stage 变更)

**架构决策**:
- 协作总线 = 文件系统 + 事件驱动
- 界面 = 文件系统的视图
- Agent = 文件的生产者和消费者
- 调度 = 文件状态变化触发
