# Monoco Issue System

**Monoco Issue System** 是面向智能体工程 (Agentic Engineering) 的核心任务编排层。

与传统的 Jira 或 Linear 不同，它不是为人机隔离设计的，而是为**人机协作**设计的。它提供了一套确定性的、可验证的协议，让 AI Agent 能够安全地参与到软件工程的生命周期中。

---

## 📚 核心文档 (Core Documentation)

请按顺序阅读以下文档以建立完整认知：

### [00. 总览: 为什么是 Issue?](./00_overview.md)

> 探讨软件工程的熵增问题以及 Agent 在协作中面临的挑战（幻觉、失忆、发散）。解释 Monoco 如何通过 "Issue as Code" 解决这些问题。

### [01. 构造: 通用原子](./01_structure.md)

> 详解 Issue 的静态结构。包括作为机器接口的 YAML Front Matter（含文件追踪）和作为人类接口的 Markdown Body。介绍静态校验机制。

### [02. 循环: 生命周期](./02_lifecycle.md)

> 描述一个任务从 `Draft` 到 `Merged` 的宏观闭环。重点介绍 **Strict Git Workflow**、环境隔离策略以及主分支保护机制。

### [03. 实战: 工作流工具](./03_workflow.md)

> CLI 命令参考手册。涵盖从创建、启动分支、同步上下文 (`sync-files`) 到提交验收的全流程操作。

### [04. 协议: 智能体集成](./04_agent_protocol.md)

> 揭示 Monoco 如何通过 Skill 注入和环境约束（Linter）来塑造 Agent 的行为，使其成为可靠的数字员工。

---

## 📖 参考资料 (References)

- **[05. 配置指南](./05_configuration.md)**: 自定义 Issue 类型、状态映射和目录结构。
- **[06. 查询语法](./06_query_syntax.md)**: 使用类似 SQL 的逻辑查询和过滤 Issue。
- **[07. 治理成熟度](./07_governance.md)**: 渐进式治理策略与成熟度等级。
