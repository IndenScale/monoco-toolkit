# AgentEmpowerment

## 定义
智能体赋能 - 负责赋予 AI Agent 所需的能力、知识与协作机制，使其能够自主完成复杂任务。它是人机协作的"引擎"。

## 与 AgentGuardrail 的关系
- **AgentEmpowerment**: 让 Agent "能做"（能力、知识、调度）
- **AgentGuardrail**: 让 Agent "做好"（验证、约束、合规）

## 职责
- **Onboarding & Knowledge**: Agent 冷启动引导、知识库管理、SOP 与最佳实践传递
- **Role Management**: Agent 角色定义（Manager/Engineer/Reviewer/Planner）、能力模型
- **Task Scheduling**: 任务分发、工作流编排（Plan -> Code -> Review）、事件驱动执行
- **Execution Monitoring**: Agent 任务执行状态追踪、超时处理、结果收集
- **Human-in-the-Loop**: 人机交互界面、审批节点、反馈收集

## 边界
- **负责**: 所有与"Agent 如何工作"相关的内容
- **不负责**: 工作项本身（IssueSystem）、开发工具（DevEx）、基础层（Foundation）

## 原则
- **Goal-Oriented**: Agent 以目标为导向，而非命令为导向
- **Observable**: 所有 Agent 行为可观察、可审计
- **Interruptible**: 支持人工介入、任务暂停与恢复
- **Context-Aware**: Agent 充分理解当前上下文（Issue、Code、History）
