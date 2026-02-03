---
id: EPIC-0025
uid: d7a8f9
type: epic
status: open
stage: doing
title: Monoco Daemon Orchestrator
created_at: '2026-02-01T00:18:00'
updated_at: '2026-02-03T10:02:42'
priority: high
parent: EPIC-0000
dependencies: []
related: []
domains:
- AgentEmpowerment
tags:
- '#EPIC-0000'
- '#EPIC-0025'
- '#orchestrator'
- '#daemon'
- narrative
- three-layer-architecture
files:
- Memos/agent-scheduler-architecture-assessment.md
- Memos/architecture-layer-analysis.md
- Memos/daemon-architecture-proposals-assessment.md
criticality: high
solution: null
opened_at: '2026-02-01T00:18:00'
owner: IndenScale
progress: 11/12
files_count: 0
---

## EPIC-0025: Monoco Daemon Orchestrator

> **Narrative Epic**: Agent 调度与编排的长期叙事
> 
> **架构更新 2026-02-03**: 基于三份架构评估报告，本 Epic 已更新为**三层架构**实现路径：
> - Layer 1: 文件监听层 (Watcher) → FEAT-0161
> - Layer 2: 事件调度层 (ActionRouter) → FEAT-0161  
> - Layer 3: 执行层 (AgentScheduler) → FEAT-0160

## 目标 (Objective)

构建 Monoco 的守护进程（Daemon）与编排层（Orchestration Layer），使其从被动工具集进化为主动运行的 Agent 操作系统内核。

本 Epic 将实现 "Mailroom -> Daemon Loop -> HITP" 的完整自动化闭环，支持非阻塞的轻量级二进制解析、基于生命周期的 Agent 调度、以及明确的人机协作（HITP）关卡。

**架构核心原则** (2026-02-03 更新):
1. **三层架构分离**: 文件监听 → 事件路由 → Action 执行
2. **Agent 间无直接调度**: 通过文件状态变化触发，而非直接调用
3. **核心抽象上提**: `AgentScheduler` 与 `EngineAdapter` 迁移至 `core/scheduler/`
4. **IM 为未来工作**: 当前聚焦核心文件驱动架构

## 验收标准 (Acceptance Criteria)

- [x] **Mailroom Pipeline**: 能够通过环境感知的适配器处理二进制文件（Office/PDF），利用"截图 + 多模态 API"将其转换为标准格式并投递给 Agent。
- [ ] **Three-Layer Architecture**: 实现文件监听层、事件调度层、执行层的清晰分离。
- [ ] **AgentScheduler Abstraction**: `core/scheduler/` 模块提供 Provider 无关的调度接口。
- [ ] **Event-Driven Workflow**: Memo/Issue/Task 文件变化自动触发对应 Agent，无需链式调用。
- [ ] **Notification Connectors**: 集成 CI/CD (GitHub Actions) 实现非阻塞的外部通知（Email/IM）。
- [ ] **HITP Gateways**: 在通过 IDE/WebUI 提供明确的三段式人工确认（Confirm Plan -> Merge Code -> Push Remote）。

## 技术任务 (Technical Tasks)

### Phase 1: The Artifact Ecosystem & Mailroom (Ingestion Layer) ✅
> 建立产物管理基础设施与轻量化文档接入。
> Mindset: Infrastructure First -> Skill Empowerment -> Automated Implementation.

- [x] **FEAT-0151**: Monoco Artifact Core - 实现全局 CAS 存储与项目元数据注册表 (`manifest.jsonl`).
- [x] **FEAT-0152**: Monoco Artifact Skills - 定义多模态文档处理的 Agent SOP 与环境自适应指南。
- [x] **FEAT-0153**: Monoco Mailroom Automation - 实现自动化工具链探测与非阻塞式 Binary Ingestion。
- [x] **FEAT-VLM-Protocol**: 标准化 Mailroom 输出与 Kimi/Gemini CLI 多模态协议的对接。

### Phase 2: Core Scheduler Abstraction (Layer 3 - 执行层)
> 建立核心调度抽象层，解耦 Provider 细节与调度策略
> 参见: Memos/agent-scheduler-architecture-assessment.md, Memos/daemon-architecture-proposals-assessment.md

- [ ] **FEAT-0160**: AgentScheduler 抽象层与 Provider 解耦
  - [ ] 创建 `monoco/core/scheduler/` 模块
  - [ ] 定义 `AgentScheduler` ABC (schedule/terminate/get_status/list_active)
  - [ ] 迁移 `EngineAdapter` 从 `features/agent/` → `core/scheduler/`
  - [ ] 实现 `LocalProcessScheduler` 作为默认实现
  - [ ] 支持并发配额控制与资源管理
  - [ ] 编写 Provider 接入文档

### Phase 3: Event-Driven Automation Framework (Layer 1+2 - 监听与路由层)
> 建立文件监听 → 事件 → Action 的三层架构
> 参见: Memos/architecture-layer-analysis.md

- [ ] **FEAT-0161**: 文件系统事件到业务事件的自动化映射框架
  - [ ] **Layer 1 - 文件监听层**: 提取文件监听到独立 `core/watcher/` 模块
    - [ ] 抽象 `FilesystemWatcher` ABC
    - [ ] 实现 `IssueWatcher` (监听 Issue 状态变化)
    - [ ] 实现 `MemoWatcher` (监听 Memo 累积)
    - [ ] 实现 `TaskWatcher` (监听 tasks.md 变化)
    - [ ] 实现 `DropzoneWatcher` (已存在，迁移至此)
  - [ ] **Layer 2 - 事件路由层**: 设计 `ActionRouter` 与 `Action` 抽象
    - [ ] 定义 `Action` ABC (can_execute/execute)
    - [ ] 实现 `ActionRouter` (事件 → Action 映射)
    - [ ] 实现条件判断机制 (Conditional Routing)
    - [ ] 支持触发器配置化 (YAML/JSON)
  - [ ] **字段变化检测**: 实现 YAML Front Matter 字段级监听
  - [ ] **统一事件总线**: 迁移 `EventBus` 到 `core/scheduler/events.py`

### Phase 4: Agent Collaboration Workflow (端到端自动化)
> 实现 Agent 联调工作流，文件状态驱动而非直接调度
> 参见: Memos/agent-scheduler-architecture-assessment.md

- [ ] **FEAT-0162**: Agent 联调工作流 - 端到端自动化
  - [ ] 实现 `TaskFileHandler` (监听 tasks.md，触发 Architect)
  - [ ] 实现 `IssueStageHandler` (监听 Issue stage=doing，触发 Engineer)
  - [ ] 实现 `MemoThresholdHandler` (监听 Memo 累积，触发 Architect)
  - [ ] 实现 `PRCreatedHandler` (监听 PR 创建，触发 Reviewer)
  - [ ] 完整 workflow 集成测试:
    - [ ] Workflow A: tasks.md → Architect → Issue (draft)
    - [ ] Workflow B: Issue doing → Engineer → PR
    - [ ] Workflow C: PR → Reviewer → 审查报告

### Phase 5: Notification Connectors (Output Layer)
> 解决 "运行结束后对通知的集成"

- [ ] **FEAT-Notification-Actions**: 封装 GitHub Actions / CI Steps 用于发送通知。
- [ ] **FEAT-Event-Emitters**: 在 Monoco Daemon 中实现事件发射器，触发 CI Pipelines。

### Phase 6: HITP Protocols (Interaction Layer)
> 解决 "HITP: Issue 确认/微调 -> 合并修改 -> 推送远程"

- [ ] **FEAT-HITP-Interface**: 标准化 "Plan Review" 和 "Code Review" 的交互协议。
- [ ] **FEAT-Gateway-Confirm**: 实现 Issue/Plan 阶段的人工确认关卡 (Approve to Implement)。
- [ ] **FEAT-Gateway-Merge**: 实现 Code/PR 阶段的人工确认关卡 (Approve to Merge)。
- [ ] **FEAT-Gateway-Push**: 实现 Deployment 阶段的人工确认关卡 (Approve to Push)。
- [ ] **FEAT-UI-Integration**: 适配 VSCode Client 和 Web Console 支持上述 HITP 操作。

### 已冻结/归档

- **FEAT-0149** (Native Hook System): ⏸️ 已冻结
  - 状态: 等待行业标准成熟 (ACP 未标准化)
  - 原因: Kimi/Claude/Gemini Hook 架构差异巨大
  - 替代: Git Hooks 集成 (FEAT-0145) 已实现

### 未来工作 (非当前 Epic 范围)

- **IM 集成** (钉钉/飞书): 作为额外的文件输入源，未来视需求评估实现。
- **Proposal 机制**: 如需预创建确认，未来再评估
- **SQLite 存储**: 当前使用 JSON Lines，未来按需评估

## 架构依赖关系

```
FEAT-0160 (Core Scheduler)
    │
    ├── 依赖: FEAT-0155 (EventBus - 已关闭)
    │
    ▼
FEAT-0161 (Automation Framework)
    │
    ├── 依赖: FEAT-0160
    ├── 依赖: FEAT-0153 (Mailroom - DropzoneWatcher)
    │
    ▼
FEAT-0162 (Collaboration Workflow)
    │
    └── 依赖: FEAT-0160, FEAT-0161
```

## Review Comments

### 2026-02-03 架构重构更新

**背景**: 基于三份架构评估报告，对 Epic 进行了彻底重构。

**重大变更**:
1. **移除 IM 依赖**: 删除 FEAT-0161/0163/0164/0168，IM 为未来工作
2. **移除 Proposal**: 删除 FEAT-0162 (原)，简化工作流
3. **重新编号**: 完成了从旧编号到 0160/0161/0162 的映射。
4. **聚焦核心**: 三层架构 + 文件驱动工作流

**架构决策记录 (ADR)**:
- **ADR-1**: `AgentScheduler` 抽象层必须位于 `core/scheduler/`
- **ADR-2**: 文件监听逻辑独立为 `core/watcher/` 模块
- **ADR-3**: Agent 间不直接调度，通过文件状态变化解耦
- **ADR-4**: 暂不引入 SQLite，使用结构化日志
- **ADR-5**: IM 集成为未来工作，非当前核心

**Hook System 状态说明**:
- Git Hooks 层: 由 FEAT-0145 (归属 EPIC-0030) 实现
- Monoco Native Hooks: 冻结，参见 FEAT-0149
- Agent SDK Hooks: 不实现（平台差异过大）
