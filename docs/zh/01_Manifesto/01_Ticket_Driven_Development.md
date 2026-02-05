# 票据驱动开发 (Ticket Driven Development)

## 1. 为什么 Agent 需要 Issue Ticket？

在传统的敏捷开发中，Issue Ticket (Jira/Linear) 是人与人沟通的载体。但在 Agent 驱动的开发中，Issue Ticket 的角色发生了根本性的转变：**它从“沟通备忘录”变成了“可执行的规格说明书 (Executable Spec)”**。

### 1.1 自然语言的模糊性 vs 工程的确定性

Agent (LLM) 拥有无限的发散思维，这既是优势也是缺陷。如果直接让 Agent "帮我写个登录功能"，它可能会产生一千种不同的实现。

Monoco 认为，**Issue Ticket 是约束 Agent 发散性的边界**。

一个合格的 Monoco Issue 必须包含：
- **明确的上下文 (Files)**: 规定 Agent 只能看哪里，只能改哪里。
- **结构化的检查点 (Checkboxes)**: 规定 Agent 必须按什么步骤执行。
- **可验证的验收标准 (Criteria)**: 规定 Agent 什么时候才算做完。

### 1.2 Issue 即 Prompt

在 Monoco 的架构中，`monoco issue start` 的本质是 **Prompt Engineering 的自动化**。

当 Agent 启动时，系统会自动将 Issue 的内容编译为 System Prompt 的一部分：
> "你是一个正在处理 Issue FEAT-123 的工程师。你的目标是完成 Ticket 中的 Checkbox。你的修改范围被限制在 `files` 列表内。"

Issue Ticket 成为了 Agent 的**长期记忆**和**短期目标**的载体。

## 2. 规格说明书的结构化

为了让 Agent 能够“读懂”需求，Monoco 将 Issue 标准化为**结构化 Markdown**。

### 2.1 标题即身份 (Identity)
`## {ID}: {Title}`
这不仅是标题，更是全局唯一的锚点。Agent 通过 ID 在 Git 历史、代码注释和提交信息中追踪任务。

### 2.2 任务列表即进度条 (Progress)
Monoco 强制要求 Issue Body 中包含 Checkbox (`- [ ]`)。
- **原子性**: 每个 Checkbox 代表一个可独立验证的步骤。
- **状态同步**: Agent 完成一步后，会自动勾选 Checkbox，系统据此计算任务进度。

### 2.3 上下文即知识 (Context)
通过 `files` 字段，我们将“知识”显式注入给 Agent。
- **Before**: Agent 需要自己去 codebase 漫游寻找相关文件（容易迷路）。
- **After**: 人类 Architect 预先在 Issue 中指定了 `files`，Agent 启动即拥有上帝视角。

## 3. 结论

**Ticket Driven Development (TDD)** 是 Monoco 的核心工作流。我们不相信“一句话需求”，我们相信**高质量的输入决定高质量的输出**。

在 Monoco 中，写好一个 Issue，不仅是管理的需要，更是编程的一部分。
