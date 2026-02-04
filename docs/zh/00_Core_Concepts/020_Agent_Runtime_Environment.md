# Agent 运行时环境与钩子机制

## 1. 运行时架构 (Runtime Architecture)

Monoco Agent 运行时环境旨在构建一个受控、可观测且具备自我纠错能力的沙盒系统。

### 1.1 上下文注入 (Context Injection)
Agent 并非在真空中运行。系统通过 `monoco sync` 机制，将以下上下文动态注入 Agent 的 System Prompt：
*   **环境法则**: 定义在 `AGENTS.md` 中的行为准则（如“禁止直接修改 main 分支”）。
*   **工程规范**: 项目特定的代码风格、命名约定。
*   **工具能力**: 当前可用的 Skills 列表及其使用范式。

### 1.2 文件系统优先 (FS-First)
Monoco 遵循 FS-First 原则。Agent 的所有感知与操作均直接作用于本地文件系统：
*   **读取**: 通过 `read_file`, `glob`, `grep` 感知项目状态。
*   **写入**: 通过 `write_file`, `replace` 修改项目状态。
*   **局域性**: 这种设计确保了操作的物理局域性 (Locality)，避免了对远程服务的依赖，并利用 Git 提供了原生的操作审计日志。

## 2. 钩子系统 (Hooks System Integration)

Hooks 是 Monoco 运行时的核心组件，充当操作系统内核的角色，拦截并规范 Agent 的 I/O 行为。

### 2.1 通用拦截器 (Universal Interceptor)
Monoco 在 Agent 与底层系统之间部署了一层通用拦截器。无论 Agent 试图执行 Git 命令还是调用工具，拦截器都会预先评估该操作的合法性。

### 2.2 即时反馈循环 (JIT Feedback Loop)
Hooks 将传统的“事后审查”前移为“运行时反馈”。当 Agent 违反约束时，Hooks 会返回结构化的 JSON 错误对象，触发 Agent 的自我修正机制。

#### 场景示例：越界写操作拦截
1.  **意图**: Agent 试图修改 `monoco/main.py`。
2.  **检查**: Hook 读取当前 Issue 的 `files` 字段，发现该文件未被声明。
3.  **拦截**: 拦截器返回 `decision: deny`。
4.  **反馈**:
    ```json
    {
      "error": "ScopeViolation",
      "message": "File 'monoco/main.py' is not in the allowed 'files' list for this Issue.",
      "suggestion": "Please run 'monoco issue sync-files' if you intend to modify this file."
    }
    ```
5.  **纠正**: Agent 接收反馈，执行 `monoco issue sync-files` 更新元数据，随后重试写操作。

## 3. 安全与合规策略 (Security & Compliance)

### 3.1 分支隔离策略
运行时环境强制执行严格的分支策略：
*   **主干保护**: 直接在 `main` 或 `master` 分支上的写操作会被 Hook 无条件拦截。
*   **Feature 分支**: 所有开发工作必须在以 `feat/`, `fix/` 等标准前缀命名的分支上进行。

### 3.2 最终一致性 (Eventual Consistency)
系统通过自动化 Hooks 确保文档与代码的最终一致性：
*   **Pre-Commit Hook**: 在代码提交前，强制运行 `sync-files`。系统对比 Git Staged 文件与 Issue `files` 列表，自动补全遗漏的文件记录，确保 Issue 文档永远真实反映代码变更。
