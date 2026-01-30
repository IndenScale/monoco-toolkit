# Guardrail

## 定义
负责通过门禁 (Gates)、策略 (Policies) 与预言机 (Oracles) 维护系统完整性的领域。它是项目的“免疫系统”。

## 职责
- **状态门禁 (State Gating)**: 拦截 Issue 的状态流转（如：若测试失败则拒绝 `submit`）。
- **预言机调用 (Oracle Invocation)**: 通过 Hooks 触发外部验证器（Linter, Tests, i18n Scanners）。
- **反馈循环 (Feedback Loop)**: 当违反约束时，提供清晰、可执行的反馈信息。
- **合规性 (Compliance)**: 确保所有交付物均符合既定的质量标准（如 Schema 校验）。
