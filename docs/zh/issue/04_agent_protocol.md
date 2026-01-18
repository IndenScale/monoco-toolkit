# 智能体集成 (Agent Integration)

Monoco 不仅仅是一个 CLI 工具，它是一个 **Agent 行为协议**。本章节揭示 Monoco 如何通过机制设计来约束和引导 Agent。

## 1. 技能注入 (Skill Injection)

当你运行 `monoco init` 时，系统会自动在 `.agent/skills/monoco_issue/` 下生成一套标准的文档：

- `SKILL.md`: 定义了本体论、工作流和验证规则。
- `AGENTS.md`: 一份极简的、Token 友好的作弊条 (Cheatsheet)。

**任何接入 Monoco 的 Agent (如 VS Code Extension 中的 Agent) 都必须在系统提示词(System Prompt) 中加载这些技能。**

## 2. 行为塑造 (Behavior Shaping)

Monoco 并不依赖 Agent 的“自觉”，而是依靠**环境约束**。

### 约束 1: 必须通过 Linter

Agent 无法提交一个格式错误的 Issue，因为 `submit` 命令会强制运行 `lint`。如果失败，流程会被阻断，Agent 必须根据错误信息自我修正。

### 约束 2: 必须在分支工作

如果 Agent 试图偷懒直接修改主分支，Linter 的 **Environment Policy** 会直接抛出 Error，迫使 Agent 学习并执行切换分支的操作。

### 约束 3: 必须追踪上下文

通过 `sync-files`，我们强制将隐式的代码修改显式化。下一次 Agent 接手这个任务时，不需要重新搞清楚“上次改了哪”，直接读取 `files` 列表即可。

## 3. 为什么选择 Git 原生？

许多 Agent 框架试图构建自己的“沙箱”或“数据库”。Monoco 选择 Git 是因为：

1.  **Git 是事实标准**: 任何 Agent 最终都要交付代码到 Git。
2.  **Diff 是最佳上下文**: `git diff` 是表达“做了什么”的最精确、最节省 Token 的方式。
3.  **零迁移成本**: 你的项目本身就在 Git 里，Monoco 不需要你迁移数据。

Monoco 只是在 Git 之上，为 Agent 铺设了一层“语义轨道”。

---

[上一章: 03. 实战](./03_workflow.md) | [返回目录](./00_overview.md)
