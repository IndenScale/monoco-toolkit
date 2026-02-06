# Monoco Daemon 目前架构深度调研报告 (2026-02-06)

## 0. 核心定位

`monoco daemon` 是 Monoco 系统的 **中枢神经系统**。它将传统的静态代码仓库转换为一个具备 **自主意识 (Agency)** 的协作环境。其核心职责是从单纯的 "API 服务" 转向 "事件驱动的自动化引擎"。

---

## 1. 架构概览

目前的 `monoco daemon` 采用了 **三层架构设计**：

### 1.1 通讯层 (FastAPI + SSE)

- **REST API**: 提供对 Issue、Project、Config、Mailroom 的基础 CRUD 操作，主要服务于 IDE 插件和 Kanban 面板。
- **SSE (Server-Sent Events)**: 通过 `Broadcaster` 同步文件系统变更（Git HEAD 更新、Issue 文件变更）到前端，实现 "UI 是仓库的镜像"。

### 1.2 调度层 (SchedulerService + EventBus)

这是系统的 "脑干"，实现了 `FEAT-0164` 定义的统一事件驱动架构：

- **EventBus**: 进程内纵贯线，汇聚所有 Watcher 产生的事件。
- **Watchers**: 细粒度的文件系统监听器（IssueWatcher, MemoWatcher, TaskWatcher），将物理变更转化为语义事件（如 `ISSUE_STAGE_CHANGED`）。
- **AgentScheduler**: 管理 Agent 进程的生命周期，负责并发控制和资源隔离。

### 1.3 逻辑层 (Independent Handlers)

遵循 `FEAT-0162` 的 **无工作流设计 (Workflow-less Design)**：

- 每个 Handler 是一个独立的微服务（如 `TaskFileHandler`, `MemoThresholdHandler`）。
- **涌现式协作**: 复杂的工程工作流（如 想法 -> Issue -> 开发 -> PR -> 评审）并不是由预定义的逻辑图驱动，而是由各个 Handler 对仓库状态变更的独立响应相互协作产生的。

---

## 2. 关键设计原则分析

### 2.1 信号队列模型 (Signal Queue Model)

针对 `Memos` 的处理采用了 `FEAT-0165` 协议：

- **Memo 即信号**: 它是 fleeting 的，不是资产。
- **原子消费**: `MemoThresholdHandler` 在触发 Principal 之前会原子化地清空 inbox，确保信号不被重复处理且不依赖内存状态。
- **Git 为存档**: 应用层不保留 Memo 状态，历史追溯完全依赖 Git。

### 2.2 状态不变性与防御性设计

- **PIDManager**: 实现了基于工作区的单例保证，防止多个 Daemon 冲突。
- **Integrity Validation**: 在 API 层面（特别是 `update_issue_content`）强制执行格式校验，确保文件系统始终处于合法状态。

### 2.3 邮件收发室 (Mailroom)

- 实现了异步的产物处理机制，负责将 PDF、Office 等非结构化文档自动转换为 WebP 透明产物（Artifacts），供 Agent 进行多模态分析。

---

## 3. 架构评价与潜在改进点

### 优势 (Strengths)

1. **极致解耦**: Handler 的独立性使得系统非常容易扩展新功能，只需添加监听新事件的订阅者即可。
2. **仓库即状态 (SSOT)**: 严格遵循 "Single Source of Truth is Git"，Daemon 几乎是无状态的（除了内存中的 EventBus 和 Job Queue）。
3. **响应式设计**: 亚秒级的反馈回路使得 Agent 的协作感非常强。

### 挑战与改进方向 (Opportunities)

1. **分布式限制**: 目前的 `PIDManager` 和 `LocalProcessScheduler` 绑定在单机环境。对于大型企业（如 `Cortex IEE` 愿景），未来可能需要转向分布式 Job Queue。
2. **事件冲突管理**: 当多个 Handler 响应同一个事件时，目前缺乏优先级或冲突消解机制。
3. **可观测性**: 虽然有日志，但缺乏一个可视化的 "事件链路追踪 (Event Trace)"，帮助用户理解为什么某个 Agent 被启动了。

---

## 4. 结论

Monoco Daemon 已经成功从一个简单的后端包装器进化到了 **工程操作系统 (Engineering OS)** 的原型阶段。其架构设计的核心魅力在于 **"让流程在规则中涌现"**，而非通过硬编码的 Pipeline 约束 Agent。

## 5. 专项评估：Agent Session 职责边界与质量门禁

### 5.1 问题背景

目前 Agent 在一个 Session 中理论上可以端到端完成从 `create` 到 `close (merge)` 的所有操作。用户担忧这会导致质量控制失效，建议将 `plan-build` 与 `review-merge` 强制分离到不同的 Session 中。

### 5.2 评估结论：强制分离是必要的

基于 Monoco 的 **Trunk-Based Development (TBD)** 和 **质量左移** 原则，我们认为这种分离不仅必要，而且是系统安全性的核心屏障。

#### 必要性理由：

1. **防御偏见 (Developer Bias)**: 同一个 Agent (Engineer) 难以客观发现自己逻辑中的瑕疵。引入第二个 Agent (Reviewer) 能够提供“第二双眼睛”。
2. **Trunk 完整性保护**: `merge (close)` 是将变更引入干线的终极动作。将其与开发过程分离，可以确保每次合拢都经过了独立的逻辑校验。
3. **职责分离 (SoD)**: 开发权限（Feature Branch）与合并权限（Trunk）在治理模式上应当是不对等的。

### 5.3 实现现状与建议

目前系统在 **逻辑层 (Handlers)** 已经实现了初步分离：

- `IssueStageHandler` 负责唤起 `Engineer`。
- `PRCreatedHandler` 负责唤起 `Reviewer`。

但 **执行层 (CLI Tooling)** 缺乏硬性约束：

### 5.3 技术实现路径优化

基于用户反馈，确认 CLI 是无状态的，因此建议将校验逻辑下沉到 **Daemon (Scheduler)** 或 **Agent 框架层 (Hooks)**。

#### 方案 1：基于 Daemon 的主动生命周期管理 (强制停止)

Daemon 监听 `ISSUE_STAGE_CHANGED` 事件。一旦识别到 Stage 变更为 `review` (代表 `submit` 已成功执行)：

- **动作**: Daemon 遍历 `AgentScheduler` 中的所有活跃 Session。
- **匹配**: 找到 `issue_id` 相同且角色为 `Engineer` (Builder) 的 Session。
- **执行**: 强制执行 `scheduler.terminate(session_id)`。
- **优势**: **物理隔离**。Agent 彻底失去执行环境，无法在提交后继续执行 `merge`。这是最推荐的“干净分界”。

#### 方案 2：基于 Daemon 状态的 Pre-Tool Hook 拦截

在 Agent 框架的 `PreToolUse` 钩子中（由 `AgentToolAdapter` 处理）：

- **检查**: 钩子向 Daemon 查询当前 `session_id` 的 `role_name`。
- **策略**:
  - 如果 `role == Engineer` 且试图执行 `monoco issue close`。
  - **拦截**: 钩子返回 `DENY`，拒绝工具执行。
- **优势**: **细粒度控制**。可以在不关闭 Session 的情况下精细化管控高危指令。

### 5.4 协作模型总结

推荐采用 **“Session 级原子化协作”** 模式：

1. **Session A (Engineer)**: 工作至 `submit` 成功后，由 Daemon 强制回收，确保其动作集在此终结。
2. **Session B (Reviewer)**: 由 `PR_CREATED` 事件唤起，负责 `review` 和最后的 `close (merge)`。

这种设计将质量门禁从“道德约束”提升到了“架构约束”。

## 6. 角色模型评估：三角色模型与 Principal Engineer

### 6.1 核心主张：坚定采用“三角色模型” (Principal, Engineer, Reviewer)

针对从需求模糊性到代码实现，再到最终合并的完整生命周期，我们确立 **Principal Engineer (首席工程师)** 为系统的决策中枢，与 **Engineer (执行者)** 和 **Reviewer (防御者)** 形成三足鼎立的制衡架构。我们将原本的 Manager (需求管理) 与 Planner (架构设计) 职责合并，因为在 Agentic System 中，需求建模与架构定义是不可分割的对称操作。

### 6.2 为什么合并为 Principal Engineer？

#### 1. 工程化管理 (Engineering as Management)

在 Monoco 语境下，管理项目本质上是一个高阶的软件工程问题。Principal Engineer 整合了“外部价值解释”与“内部架构设计”，确保每一项需求都建立在对系统现状和演进方向的深度认知之上。

#### 2. 语义契约的严肃性 (Symbolic Contract)

- **Principal 的输出是 Issue (意图)**，**Engineer 的输出是 Code (现实)**。
- 只有当这两个角色分离时，Issue 才能作为一个**不可篡改的契约**存在。角色分离确保了意图定义的独立性，防止执行者为了逃避复杂实现而擅自降级需求标准。

#### 3. 上下文卫生的差异 (Context Hygiene)

- **Principal 视角**: 广度优先。跨越多个 Issue、Memos 和全局架构文档，负责全局一致性和决策。
- **Engineer 视角**: 深度优先。聚焦于特定的代码块、测试用例和本地环境，负责实现的鲁棒性。
- 分离角色可以防止 Principal 的决策过程被底层的编译堆栈或 Linter 琐事所干扰，保持对全局架构的清醒判断。

### 6.3 角色职责边界划分

| 角色          | 核心职责                                                | 输入场景                                 | 关键动作                                          |
| :------------ | :------------------------------------------------------ | :--------------------------------------- | :------------------------------------------------ |
| **Principal** | 需求建模、需求过滤、定义“完成标准”、维护系统不变性      | Memos, Slack/IM, Tasks.md, Spikes (研究) | `issue create/update`, `memo delete`, `ADR write` |
| **Engineer**  | 翻译意图为高质量代码，撰写单元测试，确保自测覆盖        | Issue (ready/doing stage)                | `issue start`, `issue sync-files`, `issue submit` |
| **Reviewer**  | 挑战实现逻辑，验证现实与意图的一致性，守护 Trunk 完整性 | PR (review stage)                        | `issue close`, `issue reject`, `challenge test`   |

### 6.4 结论

通过引入 **Principal Engineer** 角色，我们将 Monoco 的组织力从行政式的任务分配转向了逻辑式的系统演进。三角色模型通过物理上的 Session 隔离与 Hook 拦截，构建了一个具备“抗性”的自我修正循环，这是实现 L4 级及以上自适应系统的基石。

---

_Generated by Antigravity Kernel Worker_
