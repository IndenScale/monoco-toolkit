# AgentGuardrail

## 定义
智能体护栏 - 负责确保 AI Agent 的行为符合规范、输出达到质量标准、流程遵守约束。它是人机协作的"免疫系统"。

## 与 AgentEmpowerment 的关系
- **AgentEmpowerment**: 让 Agent "能做"（能力、知识、调度）
- **AgentGuardrail**: 让 Agent "做好"（验证、约束、合规）

## 职责
- **状态门禁 (State Gating)**: 拦截 Issue 的状态流转（如：若测试失败则拒绝 `submit`）。
- **预言机调用 (Oracle Invocation)**: 通过 Hooks 触发外部验证器（Linter, Tests, i18n Scanners）。
- **反馈循环 (Feedback Loop)**: 当违反约束时，提供清晰、可执行的反馈信息。
- **合规性 (Compliance)**: 确保所有交付物均符合既定的质量标准（如 Schema 校验）。

## 边界
- **负责**: Agent 行为的约束与验证
- **不负责**: Agent 如何工作（AgentEmpowerment）、工作项管理（IssueSystem）

## 原则
- **Fail Fast**: 尽早发现问题，降低修复成本
- **Actionable Feedback**: 错误信息必须包含可执行的修复建议
- **Non-Blocking by Default**: 默认不阻塞，关键路径才启用门禁
