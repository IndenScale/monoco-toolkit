---
id: FEAT-0078
type: feature
status: closed
stage: done
title: Agent 执行层与 CLI 集成
created_at: "2026-01-15T22:56:10"
updated_at: "2026-01-15T23:01:43"
closed_at: "2026-01-15T23:01:43"
parent: EPIC-0014
solution: implemented
dependencies: []
related: []
tags: []
priority: High
author: Monoco
---

## Feature: Agent 执行层与 CLI 集成

## 目标 (Objective)

实现一个统一的 **执行层 (Execution Layer)**，允许 Monoco 将提示词分发给已配置的 Agent CLI (Gemini, Claude, Qwen) 以完成复杂的自动化任务。这使得 "智能体执行 (Agentic Executions)"（如 Issue 起草、精炼、代码审查）能够直接在 Monoco Toolkit 中通过命令行触发。

## 背景 (Context)

用户调研表明，开发者希望利用本地已安装的强大 Agent CLI 工具 (`claude`, `gemini`, `qwen`) 来处理项目上下文。Monoco 不需要重新构建一个 LLM 客户端，而应该作为一个 **编排者 (Orchestrator)**，负责组装上下文和指令，并将其分发给这些现有的工具。

## 策略 (Strategy) - 委托模式 (The "Delegation Pattern")

Monoco 将实际的智能任务 **委托** 给用户配置的 CLI 工具执行。

### 1. 统一 Agent 接口 (Unified Agent Interface)

通过标准 Python 协议抽象 CLI 工具之间的差异。

```python
class AgentClient(Protocol):
    async def available(self) -> bool: ...
    async def execute(self, prompt: str, context_files: List[Path] = []) -> str: ...
```

**适配器 (Adapters):**

- **Gemini**: `gemini -i "prompt"` (位置参数, 交互模式)
- **Claude**: `claude -p "prompt"` (打印模式, 或交互模式)
- **Qwen**: `qwen -i "prompt"`

### 2. 执行定义 (Execution Definitions) - 提示词注册表

在 `monoco/features/*/executions/` 中将标准的 "Executions" 定义为模板。

示例:

- **`refine-issue`**: 读取粗略的 Issue 文件，生成严格遵循 `monoco-issue` 本体论的精炼版本。
- **`draft-fix`**: 读取 Bug Issue + 代码上下文，提出修复计划。
- **`review-pr`**: 读取 Diff，提供严格的代码审查。

### 3. 连接状态持久化 (Connection State Persistence)

为了避免每次执行都进行高昂的运行时检查，系统将引入 **状态缓存机制**。

- **检查脚本**: 封装 `scripts/check_agents.sh` (或 `.bat`)，负责实际的二进制检测和 Ping 测试。
- **状态文件**: 检查结果将被写入 `~/.monoco/agent_state.yaml`。

  ```yaml
  last_checked: "2026-01-16T10:00:00Z"
  providers:
    gemini:
      available: true
      path: "/usr/local/bin/gemini"
      latency_ms: 200
    claude:
      available: false
      error: "Authorization failed"
  ```

- **Monoco Doctor**: 作为手动触发器，运行检查脚本并刷新状态文件。
- **运行时逻辑**: `monoco agent` 命令和 Extension 默认 **直接读取状态文件**。只有在状态文件缺失或过期（如 > 7 天）时才尝试自动刷新。

## 详细设计 (Detailed Design)

### 工作流整合

1. **Extension**: 启动时读取 `~/.monoco/agent_state.yaml`。如果 `gemini.available` 为 `true`，则在 UI 中亮起相关功能（如 CodeLens）。
2. **CLI**: 运行任务前快速校验状态文件。

### CLI 命令

```bash
monoco agent <task> [target] --using <framework>
```

- `<task>`: 任务名称，如 `refine`, `review`, `generate`.
- `[target]`: 目标文件路径或 ID (如 `FEAT-0078`).
- `--using`: 覆盖默认 Agent (例如强制使用 `claude` 即使默认是 `gemini`).

### 配置 (Configuration)

更新 `monoco.core.config`:

```yaml
agent:
  default: "gemini"
  timeout: 300
executions:
  refine-issue:
    provider: "claude" # 可以为特定任务指定特定模型
```

## 验收标准 (Acceptance Criteria)

1. **通用适配层**: 为 Claude, Gemini, 和 Qwen 实现 `AgentClient` 适配器。
2. **运行时检测**: 系统能检测已安装的 CLI 并在缺失时发出警告。
3. **Execution 注册表**: 支持从 Feature 目录加载提示词模板。
4. **概念验证 (PoC)**: 实现 `monoco agent refine <issuepkg>`，使用配置的 Agent 润色 Issue 文件。
