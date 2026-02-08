# Codex CLI vs Kimi CLI vs Gemini CLI 架构对比报告

> 研究时间: 2026-02-08
> 研究范围: .references/repos/codex, kimi-cli, gemini-cli

---

## 1. 工具设计 (Tool Design)

### 1.1 Codex CLI (OpenAI)

**架构特点**:

- **双实现架构**: 提供 TypeScript (legacy) 和 Rust (codex-rs) 两种实现
- **分层架构**:
  - `codex-cli/`: 用户界面层 (Node.js/TypeScript)
  - `codex-rs/`: 核心执行引擎 (Rust)
  - `protocol/`: 协议定义
  - `app-server/`: 应用服务器

**命令系统**:

```rust
// 基于 Rust 的核心结构
codex-rs/
  ├── core/src/          # 核心逻辑
  │   ├── codex.rs      # 主 Codex 结构
  │   ├── agent/        # Agent 管理
  │   ├── tools/        # 工具实现
  │   └── hooks/        # Hooks 系统
  ├── cli/src/          # CLI 实现
  └── protocol/src/     # 协议定义
```

**沙箱安全**:

- macOS: Apple Seatbelt (`sandbox-exec`)
- Linux: Docker 容器 + iptables 防火墙
- 网络隔离 + 目录限制

### 1.2 Kimi CLI (Moonshot)

**架构特点**:

- **纯 Python 实现**: 基于 `kosong` 框架
- **Soul-Agent-Runtime 三层架构**:
  - `KimiSoul`: 核心智能体运行时
  - `Agent`: 代理配置和工具集
  - `Runtime`: 执行环境和资源管理

**命令系统**:

```python
kimi_cli/
  ├── soul/
  │   ├── kimisoul.py    # Soul 实现
  │   ├── agent.py       # Agent 定义
  │   ├── context.py     # 上下文管理
  │   └── toolset.py     # 工具集
  ├── tools/             # 工具实现
  │   ├── multiagent/    # 多代理工具
  │   ├── file/          # 文件操作
  │   └── shell/         # Shell 执行
  └── wire/              # Wire 协议
```

**特色功能**:

- Flow Skill: 支持 Mermaid/D2 流程图定义工作流
- Ralph Loop: 自主迭代模式
- ACP (Agent Client Protocol): IDE 集成协议

### 1.3 Gemini CLI (Google)

**架构特点**:

- **TypeScript 双包架构**:
  - `packages/cli`: 前端界面层
  - `packages/core`: 后端核心层
  - `packages/a2a-server`: Agent-to-Agent 服务

**命令系统**:

```typescript
packages/
  ├── cli/src/           # CLI 前端
  │   ├── ui/           # 用户界面
  │   └── commands/     # 命令处理
  ├── core/src/         # 核心后端
  │   ├── tools/        # 工具实现
  │   ├── config/       # 配置管理
  │   └── confirmation-bus/  # 确认机制
  └── a2a-server/       # A2A 协议服务
```

**设计原则**:

- 模块化: CLI 与 Core 分离，支持多前端
- 可扩展: 工具系统支持动态添加
- 用户体验: 丰富的交互式终端体验

---

## 2. 记忆系统 (Memory System)

### 2.1 Codex CLI

**记忆机制**:

```rust
// ~/.codex/AGENTS.md - 项目级记忆
// AGENTS.md at repo root - 项目级记忆
// AGENTS.md in current working directory - 子目录级记忆
```

**特点**:

- **分层记忆加载**: 个人 (~/.codex/) → 项目 (repo root) → 子目录 (cwd)
- **AGENTS.md 格式**: Markdown 格式的系统提示词
- **无持久化对话历史**: 依赖会话级别的线程历史
- **History 配置**: 支持配置历史记录保存 (`history.maxSize`, `history.saveHistory`)

**配置示例**:

```yaml
# ~/.codex/config.yaml
history:
  maxSize: 1000
  saveHistory: true
  sensitivePatterns: []
```

### 2.2 Kimi CLI

**记忆机制**:

```python
# ~/.kimi/sessions/{workdir_md5}/{session_id}/context.jsonl
# Session-based 上下文持久化
```

**特点**:

- **会话级记忆**: 每个会话有独立的 context.jsonl
- **Context 类**: 专门的上下文管理，支持 checkpoint/restore
- **自动压缩**: `SimpleCompaction` 自动管理上下文长度
- **Skills 系统**: 项目级和个人级的 SKILL.md 文件

**记忆层级**:

1. Built-in skills (内置)
2. User-level skills (~/.config/agents/skills/)
3. Project-level skills (.agents/skills/)

**关键代码**:

```python
class Context:
    def __init__(self, file_backend: Path):
        self.file_backend = file_backend
        self.history: list[Message] = []

    async def checkpoint(self, with_user_message: bool = False):
        # 持久化到文件

    async def restore(self):
        # 从文件恢复
```

### 2.3 Gemini CLI

**记忆机制**:

```typescript
// ~/.gemini/GEMINI.md - 全局记忆文件
// .gemini/GEMINI.md - 项目级记忆 (可选)
```

**特点**:

- **`save_memory` 工具**: 专门用于保存长期记忆
- **GEMINI.md 文件**: Markdown 格式，自动加载到上下文
- **记忆分区**: `## Gemini Added Memories` 专门区域
- **可编辑性**: 用户可以直接编辑 GEMINI.md

**工具实现**:

```typescript
// packages/core/src/tools/memoryTool.ts
class MemoryTool extends BaseDeclarativeTool {
  static readonly Name = 'save_memory'

  async execute(params: SaveMemoryParams): Promise<ToolResult> {
    // 追加到 ~/.gemini/GEMINI.md
    // 格式: - {fact}
  }
}
```

**记忆文件结构**:

```markdown
# User context

... 用户自定义内容 ...

## Gemini Added Memories

- My preferred programming language is Python.
- The project I'm currently working on is called 'gemini-cli'.
```

---

## 3. Hooks 支持

### 3.1 Codex CLI

**Hooks 系统**:

```rust
// codex-rs/core/src/hooks/
pub(crate) struct Hooks {
    after_agent: Vec<Hook>,
}

pub(crate) struct HookPayload {
    pub(crate) session_id: ThreadId,
    pub(crate) cwd: PathBuf,
    pub(crate) triggered_at: DateTime<Utc>,
    pub(crate) hook_event: HookEvent,
}

pub(crate) enum HookEvent {
    AfterAgent {
        thread_id: ThreadId,
        turn_id: String,
        input_messages: Vec<String>,
        last_assistant_message: Option<String>,
    },
}
```

**特点**:

- **事件类型**: 目前支持 `AfterAgent` (Agent 执行后)
- **配置方式**: 通过 `config.notify` 配置外部命令
- **异步执行**: Hook 函数是异步的，返回 `HookOutcome`
- **JSON Payload**: 通过标准输入传递序列化的 HookPayload

**配置示例**:

```yaml
# ~/.codex/config.yaml
notify: ['notify-send', 'Codex Done'] # Agent 执行后发送通知
```

### 3.2 Kimi CLI

**Hooks 支持**: ⚠️ **有限**

- **无原生 Hooks 系统**: 没有类似 Codex 的 hooks 机制
- **Wire 协议事件**: 通过 Wire 协议暴露生命周期事件
  - `TurnBegin`, `StepBegin`, `StepInterrupted`
  - `CompactionBegin`, `CompactionEnd`
  - `SubagentEvent`
- **Slash 命令**: 支持 `/command` 形式的命令拦截

**扩展机制**:

```python
# 通过 Wire 协议监听事件
class Wire:
    def soul_side(self) -> WireSoulSide:
        # 发送事件

    def ui_side(self) -> WireUISide:
        # 接收事件
```

### 3.3 Gemini CLI

**Hooks 支持**: ⚠️ **未发现原生 Hooks 系统**

- **无显式 Hooks**: 代码中没有发现类似 Codex 的 hooks 机制
- **确认机制**: 通过 `confirmation-bus` 实现用户确认流程
- **工具拦截**: 在工具执行前进行确认

---

## 4. Sub-agent 与 Agent Warm 支持

### 4.1 Codex CLI

**Sub-agent 架构**:

```rust
// codex-rs/core/src/agent/guards.rs
pub const MAX_THREAD_SPAWN_DEPTH: usize = 3;

pub struct AgentGuard {
    depth: usize,
}

// Sub-agent 作为独立的线程/会话
pub struct SubAgentSource {
    pub parent_thread_id: ThreadId,
    pub depth: usize,
}
```

**特点**:

- **嵌套深度限制**: 最大 3 层嵌套
- **独立上下文**: Sub-agent 有自己的 ThreadId 和上下文
- **委派模式**: 主 Agent 通过工具调用委派任务

**Sub-agent 类型**:

- 内置 Sub-agents (通过配置启用)
- 动态 Sub-agents (通过 API 创建)

### 4.2 Kimi CLI

**Sub-agent 架构**:

```python
# kimi_cli/tools/multiagent/task.py
class Task(CallableTool2[Params]):
    """Task tool to delegate work to subagents"""

    async def _run_subagent(self, agent: Agent, prompt: str) -> ToolReturnValue:
        # 创建独立的 context 文件
        subagent_context_file = await self._get_subagent_context_file()
        context = Context(file_backend=subagent_context_file)
        soul = KimiSoul(agent, context=context)

        # 通过 Wire 协议转发事件
        def _super_wire_send(msg: WireMessage):
            event = SubagentEvent(
                task_tool_call_id=current_tool_call_id,
                event=msg,
            )
            super_wire.soul_side.send(event)
```

**特点**:

- **Task 工具**: 专门的 `Task` 工具创建 sub-agent
- **Labor Market**: `LaborMarket` 管理可用的 sub-agents
- **动态创建**: `CreateSubagent` 工具支持运行时创建 sub-agent
- **独立 Context**: 每个 sub-agent 有自己的 context 文件
- **事件转发**: Sub-agent 的事件通过 `SubagentEvent` 转发给父 agent

**Agent Spec 配置**:

```yaml
# Agent 定义文件
name: default
system_prompt: ...
tools:
  - ReadFile
  - WriteFile
  - Task # 启用 sub-agent 工具
subagents:
  researcher:
    system_prompt: 'You are a research specialist...'
    tools: [ReadFile, SearchWeb]
```

### 4.3 Gemini CLI

**Sub-agent 架构**:

```typescript
// packages/core/src/tools/save-memory.ts (类似工具架构)
// .gemini/agents/*.md - Agent 定义文件
```

**特点**:

- **Markdown 定义**: Sub-agents 定义为 `.gemini/agents/*.md` 文件
- **YAML Frontmatter**: 前置配置定义 agent 属性
- **内置 Sub-agents**:
  - `codebase_investigator`: 代码库分析
  - `cli_help`: CLI 帮助
  - `generalist_agent`: 任务路由

**Agent 定义格式**:

```markdown
---
name: security-auditor
description: Specialized in finding security vulnerabilities
kind: local
tools:
  - read_file
  - grep_search
model: gemini-2.5-pro
temperature: 0.2
max_turns: 10
timeout_mins: 5
---

You are a ruthless Security Auditor...
```

**A2A 协议** (Agent-to-Agent):

- 支持远程 sub-agents
- 基于 A2A (Agent2Agent) 协议
- 实验性功能

---

## 5. 对比总结

| 特性           | Codex CLI             | Kimi CLI               | Gemini CLI              |
| -------------- | --------------------- | ---------------------- | ----------------------- |
| **实现语言**   | Rust + TypeScript     | Python                 | TypeScript              |
| **架构模式**   | 双实现(legacy+modern) | Soul-Agent-Runtime     | CLI+Core 分离           |
| **记忆系统**   | AGENTS.md 分层        | Context.jsonl + Skills | GEMINI.md + save_memory |
| **记忆持久化** | 配置历史              | 会话级持久化           | 全局 GEMINI.md          |
| **Hooks**      | ✅ 完整 (AfterAgent)  | ⚠️ Wire 事件           | ❌ 未发现               |
| **Sub-agent**  | ✅ 深度限制           | ✅ Labor Market        | ✅ Markdown 定义        |
| **Agent Warm** | ❌                    | ❌                     | ❌                      |
| **沙箱安全**   | ✅ Seatbelt/Docker    | ❌                     | ❌                      |
| **流程控制**   | Plan/Execute 模式     | Ralph Loop/Flow        | 标准模式                |
| **IDE 集成**   | LSP                   | ACP 协议               | 内置支持                |

### 关键差异分析

**1. 记忆系统设计**:

- **Codex**: AGENTS.md 偏"指令/提示词"，分层加载
- **Kimi**: Context.jsonl 偏"对话历史"，会话级管理
- **Gemini**: GEMINI.md 偏"用户偏好"，工具驱动保存

**2. Sub-agent 模型**:

- **Codex**: 运行时线程模型，深度限制
- **Kimi**: Labor Market 模型，动态雇佣
- **Gemini**: 文件定义模型，声明式配置

**3. 扩展机制**:

- **Codex**: Hooks 系统 + MCP 工具
- **Kimi**: Wire 协议 + Skills + MCP
- **Gemini**: Sub-agents + Extensions + MCP

**4. 安全模型**:

- **Codex**: 最强，原生沙箱支持
- **Kimi**: 依赖用户确认 (YOLO 模式)
- **Gemini**: 用户确认 + Policy Engine

---

## 6. 对 Monoco 的启示

1. **记忆系统**: 参考 Kimi 的 Context 持久化 + Gemini 的 GEMINI.md 用户编辑能力
2. **Sub-agent**: 参考 Kimi 的 Labor Market 模型 + Gemini 的声明式定义
3. **Hooks**: 参考 Codex 的 hooks 系统设计，支持事件订阅
4. **安全**: 参考 Codex 的沙箱实现，考虑 seatbelt/docker 集成
5. **协议**: 参考 Kimi 的 Wire 协议设计，实现标准化的 Agent 通信
