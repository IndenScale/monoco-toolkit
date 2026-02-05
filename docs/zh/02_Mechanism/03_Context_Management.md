# 上下文管理 (Context Management)

在 Agent 开发中，**Context Window (上下文窗口)** 是最昂贵的资源。如何向 Agent 提供精准、够用且不超限的上下文，是工程成败的关键。

Monoco 通过 Issue 中的 `files` 字段，实现了**声明式的上下文管理**。

## 1. Files 字段的定义

在 Issue 的 Front Matter 中：

```yaml
files:
  - monoco/core/agent.py
  - monoco/core/scheduler.py
  - docs/zh/02_Mechanism/01_Issue_Lifecycle.md
```

这个列表不仅是文件的路径，它定义了 Agent 的**认知边界 (Cognitive Boundary)**。

### 1.1 显式白名单
Agent **只能**看到列表里的文件。
- 防止 Hallucination (幻觉): Agent 不会引用不存在的代码。
- 防止 Distraction (干扰): Agent 不会被无关的 legacy code 误导。
- 安全性: 限制 Agent 对敏感配置文件的读取权限。

## 2. 动态上下文注入 (Dynamic Injection)

Monoco Runtime 在启动 Agent 时，会执行以下步骤：

1.  **Resolve**: 解析 `files` 列表中的路径（支持 Glob 模式）。
2.  **Read**: 读取文件内容。
3.  **Pack**: 将文件路径与内容打包成特定的 XML/Markdown 格式。
4.  **Inject**: 将打包后的内容插入到 System Prompt 的 `<context>` 区块中。

### 2.1 智能截断与摘要
如果文件过大，Monoco 支持通过策略进行优化：
- **Outline Mode**: 仅注入类和函数签名，隐藏实现细节。
- **Snippet Mode**: 仅注入与光标位置相关的代码片段。

## 3. 自动化的上下文维护

依靠人肉维护 `files` 列表是痛苦的。Monoco 提供了自动化机制：

### 3.1 基于 Git 的自动推断
当你运行 `monoco issue sync-files` 时，系统会查询 Git：
> "当前分支相对于 Main 分支修改了哪些文件？"

这些被修改的文件（Touched Files）会被自动加入 `files` 列表。
这意味着：**你修改过的文件，自动成为你（和 Reviewer）的上下文。**

### 3.2 基于引用的自动发现 (Coming Soon)
未来 Monoco 将支持静态分析：
如果 `monoco/core/agent.py` import 了 `monoco/core/llm.py`，后者可能会被自动建议加入上下文。

## 4. 最佳实践

1.  **Start Small**: 创建 Issue 时，只列出你确定需要修改的核心文件。
2.  **Let Git Drive**: 开发过程中，让 `sync-files` 自动扩充列表。
3.  **Prune Regularly**: 如果发现列表里包含了无关文件（误触），手动删除它们，通过 Linter 保持上下文的纯净。
