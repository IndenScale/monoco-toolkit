# 本地主权 (Local Sovereignty)

## 1. 为什么要把 Issue 从云端迁移下来？

Monoco 做出了一个反直觉的决定：**放弃 Jira/Linear/Trello 等成熟的 SaaS 工具，将 Issue 管理回归到本地文件系统。**

这并非复古，而是为了在 AI 时代重夺**数据主权**与**工程一致性**。

## 2. 核心理由

### 2.1 Git 原子性 (Atomic Commits)

在传统模式下，需求（Jira Ticket）与代码（Git Commit）是割裂的两个平行宇宙。
- 你在代码里改了逻辑，却忘了更新 Jira 状态。
- 你在 Jira 里改了需求，代码分支却还在跑旧逻辑。

在 Monoco 模式下，**Issue 就是文件**。
- 当你提交代码时，你可以同时修改 `Issue.md` 的状态。
- `git commit` 将“需求的变更”与“代码的变更”打包在同一个原子操作中。
- **历史回溯**：当你 `git checkout` 到一年前的版本，你不仅看到了那时的代码，也看到了那时的需求状态。这是 SaaS 工具永远无法做到的。

### 2.2 消除 SaaS 黑盒

Agent 需要读取 Issue 来理解任务。
- **SaaS 模式**: Agent 需要 API Token，需要处理 Rate Limit，需要适配复杂的 JSON Schema。
- **本地模式**: Agent 只需要 `read_file("Issues/FEAT-001.md")`。

本地文件系统是 Agent 最熟悉、最快速、最可靠的接口。Monoco 将 Issue 降维为文本文件，使得任何文本处理工具（grep, sed, llm）都能直接参与项目管理。

### 2.3 作为治理对象的 Issue (Issue as a Governable Object)

在云端工具中，Issue 只是数据库里的一行记录，其内容的质量（字段是否合理、引用是否破碎、占位符是否清除）完全依赖于人的自觉。

在 Monoco 模式下，**Issue 是可被编译器治理的对象**：
- **静态检查 (Linting)**: 我们可以像检查代码语法一样检查 Issue。字段是否缺失？引用的 Epic 是否破碎？是否还残留着 "TBD" 等占位符文本？
- **不变量约束**: 只有当 Issue 的元数据达到特定的“质量标准”时，才允许进入下一个 Stage。
- **结构化关联**: 本地化使得我们可以扫描整个代码库，建立 Issue 与代码、测试、文档之间的强链接。

### 2.4 动态鲜活性 (Dynamic Vitality)

传统的 Issue 往往在创建后就陷入“陈腐”。开发者忙于写代码，很少去更新 Ticket 里的文件列表或详细描述。

本地化实现了**自动化的生命力同步**：
- **Touched Files 自动同步**: 借助 Git 接口，Monoco 可以实时追踪当前任务修改了哪些文件，并自动更新 Issue 的 `files` 列表。
- **进度真实性**: 勾选 Checkbox 不再只是手动操作。通过关联特定的测试用例或代码提交，系统可以自动验证进度，确保 Issue 描述与工程事实始终保持 1:1 的同步。

## 3. 分布式协作

本地化并不意味着放弃协作。依靠 Git 的分布式特性，Monoco 实现了比 SaaS 更强大的协作模式：

- **离线可用**: 飞机上、高铁上，随时查看和编辑任务。
- **分支隔离**: 在 Feature Branch 中修改 Issue，不会污染 Main Branch 的任务状态，直到 PR 合并。
- **Conflict Resolution**: 当两个人同时修改任务状态时，Git 的合并冲突机制提供了最精细的解决方案。

## 4. 结论

Monoco 的 **Local Sovereignty** 理念，旨在消除软件工程中的“中间商”。
我们不需要一个云端数据库来告诉我们要做什么。**代码库本身包含了它所需的一切：从需求到实现，从测试到文档。**
