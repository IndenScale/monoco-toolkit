# ADR-001: Issue Lifecycle Hooks

## 状态

**Proposed** - 待评审

## 背景

当前 `monoco issue` 命令（create/start/submit/close）将以下逻辑混合在命令实现中：

1. **前置条件检查**：分支上下文验证、working tree 状态检查
2. **核心状态切换**：Issue status/stage 变更
3. **后置处理**：报告生成、资源清理、提醒输出

这导致：

- 命令代码臃肿（如 `submit` 约 100 行）
- 检查逻辑难以复用和定制
- Agent 反馈格式不统一

## 决策

### 1. Issue Hooks 作为一等公民

**核心原则**：Issue Lifecycle Hooks 是 Monoco **领域模型的一部分**，与 Git/Agent/IDE Hooks 处于同一抽象层级，而非 Agent Hooks 的派生。

```
┌─────────────────────────────────────────────────────────────┐
│                    Monoco Universal Hooks                    │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│  Git Hooks  │ Agent Hooks │  IDE Hooks  │   Issue Hooks     │
│  (原生事件)  │ (Agent 事件) │ (IDE 事件)  │ (Issue 生命周期)   │
└─────────────┴─────────────┴─────────────┴───────────────────┘
                                                   │
                          ┌────────────────────────┼────────────────────────┐
                          │                        │                        │
                          ▼                        ▼                        ▼
                   ┌─────────────┐        ┌─────────────┐          ┌─────────────┐
                   │ 本地 CLI    │        │ Agent 桥接   │          │  Webhook    │
                   │ 直接触发    │        │ (Tool Hooks)│          │  (未来)     │
                   └─────────────┘        └─────────────┘          └─────────────┘
```

### 2. 分层架构

#### Layer 1: Issue 领域层（核心）

定义 Issue 专属的事件和协议：

```python
class IssueEvent(str, Enum):
    # Issue Lifecycle
    PRE_CREATE = "pre-create"
    POST_CREATE = "post-create"
    PRE_START = "pre-start"
    POST_START = "post-start"
    PRE_SUBMIT = "pre-submit"
    POST_SUBMIT = "post-submit"
    PRE_CLOSE = "pre-close"
    POST_CLOSE = "post-close"

    # Agnostic Agent Lifecycle (Canonical ACL)
    PRE_SESSION = "pre-session"
    POST_SESSION = "post-session"
    PRE_AGENT = "pre-agent"
    POST_AGENT = "post-agent"
    PRE_SUBAGENT = "pre-subagent"
    POST_SUBAGENT = "post-subagent"
    PRE_TOOL_USE = "pre-tool-use"
    POST_TOOL_USE = "post-tool-use"
    PRE_COMPACT = "pre-compact"

class IssueHookResult:
    """Issue Hook 执行结果"""
    decision: Literal["allow", "deny", "warn"]
    message: str
    diagnostics: List[Diagnostic]
    suggestions: List[str]  # 给 Agent 的可操作建议
```

特点：

- **与触发方式解耦**：不关心是被 CLI 调用、Agent 触发还是 Webhook 触发
- **领域语义丰富**：参数包含 `issue_id`, `from_status`, `to_status` 等 Issue 领域概念
- **可独立测试**：无需 Agent 环境即可测试 Issue Hooks

#### Layer 2: 触发适配层（可插拔）

不同触发方式通过适配器转换为 Issue 事件：

| 触发器     | 适配器             | 说明                                 |
| ---------- | ------------------ | ------------------------------------ |
| 本地 CLI   | `DirectTrigger`    | 命令直接调用 IssueHookDispatcher     |
| Agent Tool | `AgentToolAdapter` | 拦截 `monoco issue *` 命令，解析参数 |
| Git Hook   | `GitEventAdapter`  | 如：提交时自动触发 `pre-submit`      |
| Webhook    | `WebhookAdapter`   | 未来：GitHub PR 状态变更触发         |

**Agent Tool 适配示例**：

```python
class AgentToolAdapter:
    """将 Agent 的 PreToolUse 事件转换为 Issue 事件"""

    def translate(self, agent_event: dict) -> Optional[IssueEventContext]:
        tool_input = agent_event.get("tool_input", {})
        command = tool_input.get("command", "")

        # 解析命令: "monoco issue submit FEAT-0123"
        match = parse_monoco_issue_command(command)
        if not match:
            return None  # 不是 issue 命令，忽略

        return IssueEventContext(
            event=self.map_command_to_event(match.subcommand),
            issue_id=match.issue_id,
            trigger_source="agent",
            raw_context=agent_event
        )

### 3. 命名统一与 ACL 映射

为了保持 Monoco 内部逻辑的纯粹性，所有内置钩子事件均采用 `pre-` 和 `post-` 前缀。当与外部 Agent (Claude Code/Gemini CLI) 对接时，由 `TriggerAdapter` 负责词法映射。

**映射表 (Canonical Mapping)：**

| Monoco 规范事件 (Internal) | Claude Code 对应 | Gemini CLI 对应 |
| :--- | :--- | :--- |
| `pre-session` | `SessionStart` | `SessionStart` |
| `post-session` | `SessionEnd` | `SessionEnd` |
| `pre-agent` | `UserPromptSubmit` | `BeforeAgent` |
| `post-agent` | `Stop` | `AfterAgent` |
| `pre-subagent` | `SubagentStart` | - |
| `post-subagent` | `SubagentStop` | - |
| `pre-tool-use` | `PreToolUse` | `BeforeTool` |
| `post-tool-use` | `PostToolUse` | `AfterTool` |
| `pre-compact` | `PreCompact` | `PreCompress` |

**优势：**
1. **开发者无感**：编写 Monoco 钩子时只需记住 `pre/post` 对称主语。
2. **跨平台兼容**：同一个 `pre-tool-use` 钩子可以自动适配不同 Agent。
3. **架构解耦**：Agent 的版本更迭和命名变迁不会影响 Monoco 领域的事件定义。
```

### 3. 检查层次边界

明确划分不同层次的职责：

| 层次                 | 职责                 | 示例                                                      | 执行者                 |
| -------------------- | -------------------- | --------------------------------------------------------- | ---------------------- |
| **Issue Lint**       | Issue 数据自身完整性 | status/stage 合法性、必填字段、acceptance criteria 完成度 | `monoco issue lint`    |
| **Pre-Issue-Hooks**  | 命令执行前置条件     | 分支检查、working tree 状态、files 同步状态               | Issue Hooks (`pre-*`)  |
| **Core Action**      | 纯粹的状态切换       | update status/stage                                       | 命令核心逻辑           |
| **Post-Issue-Hooks** | 命令成功后的处理     | 报告生成、todo 提醒、资源清理                             | Issue Hooks (`post-*`) |

**关键原则**：Issue Lint **不涉及**工作区状态，只检查 ticket 本身。工作区状态检查属于 Pre-Issue-Hooks。

### 4. 决策与反馈模型

Hooks 返回结构化决策，Agent 可以解析并采取行动：

```python
class HookDecision(str, Enum):
    ALLOW = "allow"   # 检查通过，继续执行
    WARN = "warn"     # 有警告但允许继续（Agent 收到警告和建议）
    DENY = "deny"     # 检查失败，阻止命令执行

# Agent 收到的反馈格式
{
    "decision": "deny",
    "message": "Issue lint failed: acceptance criteria incomplete",
    "diagnostics": [
        {"line": 45, "severity": "error", "message": "Uncheck item: 'Implement API'"}
    ],
    "suggestions": [
        "运行 'monoco issue lint FEAT-0123 --fix' 自动修复",
        "检查 Technical Tasks 是否全部标记完成",
        "确认 'files' 字段已同步 (monoco issue sync-files)"
    ],
    "context": {
        "issue_id": "FEAT-0123",
        "current_branch": "FEAT-0123-login-page",
        "uncommitted_changes": True
    }
}
```

### 5. 命令执行流程

```
用户/Agent: monoco issue submit FEAT-0123

┌─────────────────────────────────────────────────────────────┐
│  TRIGGER ADAPTER (根据执行环境选择)                           │
│  - 本地 CLI: DirectTrigger                                   │
│  - Agent: AgentToolAdapter (拦截 PreToolUse)                 │
└────────────────┬────────────────────────────────────────────┘
                 │ IssueEventContext
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  PRE_SUBMIT Hooks                                           │
│  - 检查分支上下文 (feature branch?)                          │
│  - 检查 working tree 状态                                   │
│  - 调用 lint（可选）                                         │
│  - 自定义策略检查                                            │
└───────────────┬─────────────────────────────────────────────┘
                │ HookDecision
                ▼
       ┌─────────────────┐
       │  DENY? ─────────┼───► 返回结构化错误 + 建议给 Agent
       └────────┬────────┘      (允许 Agent 自动修复后重试)
                │ ALLOW / WARN
                ▼
┌─────────────────────────────────────────────────────────────┐
│  CORE ACTION                                                │
│  - 纯粹的 status/stage 状态变更                              │
│  - 最小化逻辑，不内嵌检查                                     │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  POST_SUBMIT Hooks                                          │
│  - 生成 delivery report                                     │
│  - 输出下一步操作建议                                         │
│  - 触发后续工作流（如自动创建 PR）                            │
└─────────────────────────────────────────────────────────────┘
                │
                ▼
        返回结果 + 所有 Hook 反馈
```

## 后果

### 正面影响

1. **单一职责**：Action 只关注状态切换（~30 行 vs ~100 行）
2. **可测试性**：Issue Hooks 可脱离 Agent 环境独立测试
3. **可扩展性**：用户可添加自定义策略（如公司特定的提交检查）
4. **多触发器支持**：同一套 Hooks 可被 CLI、Agent、Git、Webhook 触发
5. **Agent 体验**：统一的反馈格式，Agent 可以解析 suggestions 并自动采取行动

### 负面影响

1. **架构复杂度**：需要维护触发器注册、适配器、Hook 执行三层
2. **概念 overhead**：开发者需要理解分层架构
3. **性能开销**：多层转发可能增加延迟（但同步执行可接受）

### 风险缓解

- **向后兼容**：无 Hooks 时命令行为完全不变
- **渐进采用**：可以先只在 `submit` 命令中试点
- **调试支持**：提供 `--debug-hooks` 参数查看每层转发详情

## 替代方案

### 方案 A：纯 Agent Tool Hooks（拒绝）

直接用 `PreToolUse` 拦截 `monoco issue *` 命令，在脚本内解析参数。

**拒绝原因**：

- 无法支持本地 CLI 独立执行 Hooks
- 每个 Hook 都要重复解析命令参数
- 语义不清晰，难以管理和排序

### 方案 B：YAML 配置化检查（拒绝）

使用 YAML 配置定义检查规则，而非 Hook 脚本。

**拒绝原因**：

- 灵活性不足（难以表达复杂逻辑如分支关系分析）
- 需要实现 DSL 解析器
- 与现有 Hooks 生态系统割裂

## 实现计划

### Phase 1: 基础设施

1. 定义 `IssueEvent` 枚举和 `IssueHookResult` 模型
2. 实现 `IssueHookDispatcher`（核心执行器）
3. 实现 `DirectTrigger`（本地 CLI 触发）
4. 实现 `AgentToolAdapter`（Agent 环境桥接）

### Phase 2: 命令集成

1. 重构 `submit` 命令，集成 pre/post hooks
2. 重构 `start` 命令，集成 pre/post hooks
3. 重构 `close` 命令，集成 pre/post hooks
4. 保持向后兼容（无 hooks 时行为不变）

### Phase 3: 内置 Hooks

1. `pre-submit`：分支检查 + lint 调用（默认启用）
2. `post-submit`：报告生成 + 建议输出
3. `post-start`：todo 提醒 + 分支信息

### Phase 4: 自定义 Hooks

1. 支持 `.monoco/hooks/issue/` 自定义脚本
2. 配置项启用/禁用内置 hooks
3. 支持 hooks 优先级和条件执行

## 关键技术决策

### Q1: 如何处理 Agent 环境的 Hook 执行？

**决策**：通过 `AgentToolAdapter` 桥接，而非直接暴露 Issue Hooks 给 Agent。

```python
# Agent 环境流程
agent_event = receive_from_stdin()  # PreToolUse
issue_context = AgentToolAdapter().translate(agent_event)
if issue_context:
    result = IssueHookDispatcher().execute(issue_context)
    send_to_stdout(AgentToolAdapter().translate_back(result))
```

### Q2: Issue Lint 与 Issue Hooks 的关系？

**决策**：Lint 是独立的可复用模块，Hooks 可以选择调用它。

```python
# pre-submit hook 示例
#!/bin/bash
# 调用 lint 检查
lint_result=$(monoco issue lint "$ISSUE_ID" --format json)
if [ $? -ne 0 ]; then
    # 构造 HookDecision
    echo '{"decision": "deny", "diagnostics": ...}'
fi
```

### Q3: 如何确保向后兼容？

**决策**：

1. 无 Hooks 目录时，命令行为完全不变
2. 内置 Hooks 默认启用但可通过配置禁用
3. 提供 `--no-hooks` 参数临时跳过 Hooks

## 参考

- [Universal Hooks 文档](../40_hooks/README.md)
- [ACL 统一协议](../90_Spikes/hooks-system/agent_hooks/acl_unified_protocol_ZH.md)
- [Claude Code Hooks](../90_Spikes/hooks-system/agent_hooks/claude_code_hooks_ZH.md)
- [Gemini CLI Hooks](../90_Spikes/hooks-system/agent_hooks/gemini_cli_hooks_ZH.md)
- [Issue 命令实现](../../../monoco/features/issue/commands.py)
- [Lint 实现](../../../monoco/features/issue/linter.py)

## 记录

- **提出**: 2026-02-05
- **更新**: 2026-02-05（明确分层架构）
- **作者**: @indenscale
- **相关 Issue**: FEAT-0180
