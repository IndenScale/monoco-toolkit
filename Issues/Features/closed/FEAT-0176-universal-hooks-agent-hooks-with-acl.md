---
id: FEAT-0176
uid: 2daae5
type: feature
status: closed
stage: done
title: 'Universal Hooks: Agent Hooks with ACL'
created_at: '2026-02-04T13:27:08'
updated_at: '2026-02-04T17:04:39'
parent: EPIC-0034
dependencies:
- FEAT-0174
related: []
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0034'
- '#FEAT-0174'
- '#FEAT-0176'
files:
- monoco/core/sync.py
- monoco/features/hooks/__init__.py
- monoco/features/hooks/commands.py
- monoco/features/hooks/dispatchers/__init__.py
- monoco/features/hooks/dispatchers/agent_dispatcher.py
- monoco/features/hooks/universal_interceptor.py
criticality: high
solution: implemented
opened_at: '2026-02-04T13:27:08'
closed_at: '2026-02-04T17:04:39'
isolation:
  type: branch
  ref: FEAT-0176-universal-hooks-agent-hooks-with-acl
  created_at: '2026-02-04T16:50:15'
---

## FEAT-0176: Universal Hooks: Agent Hooks with ACL

## 目标

实现 Agent Hooks 分发器和防腐层（ACL），支持 `type: agent` 的 Hooks 按 `provider` 分发到 Claude Code 和 Gemini CLI。

## 背景

Agent Hooks 需要 ACL 层因为不同 Agent 平台的 JSON 协议、字段命名、决策模型存在差异。详见 [ACL 统一协议设计](../../docs/zh/90_Spikes/hooks-system/agent_hooks/acl_unified_protocol_ZH.md)。

## 验收标准

- [x] 实现 `AgentHookDispatcher` 基类
- [x] 实现 `ClaudeCodeDispatcher`：注入 `.claude/settings.json`
- [x] 实现 `GeminiDispatcher`：注入 `.gemini/settings.json`
- [x] 实现 `UniversalInterceptor` 运行时拦截器
- [x] Provider 自动探测（环境变量：`CLAUDE_CODE_REMOTE`, `GEMINI_ENV_FILE`）
- [x] 协议翻译：Claude/Gemini 协议 ↔ Monoco 统一协议

## 技术任务

### AgentHookDispatcher 框架
- [x] 实现 `AgentHookDispatcher` 基类
  - [x] 按 `provider` 字段路由到对应子分发器
- [x] 实现 `ClaudeCodeDispatcher`
  - [x] 注入/更新 `.claude/settings.json` 的 `hooks` 数组
  - [x] 支持事件映射：Monoco `before-tool` → Claude `PreToolUse`
- [x] 实现 `GeminiDispatcher`
  - [x] 注入/更新 `.gemini/settings.json` 的 `hooks` 数组
  - [x] 支持事件映射：Monoco `before-tool` → Gemini `BeforeTool`

### UniversalInterceptor (ACL 层)
- [x] 实现 `universal-interceptor` 脚本（Python）
- [x] Provider 自动探测：
  - [x] Claude: 检测 `CLAUDE_CODE_REMOTE` 环境变量
  - [x] Gemini: 检测 `GEMINI_ENV_FILE` 环境变量
- [x] 实现适配器：
  - [x] `ClaudeAdapter`: 翻译输入/输出协议
    - `PreToolUse` ↔ `before-tool`
    - `UserPromptSubmit` ↔ `before-agent`
    - `permissionDecision` → `decision`
  - [x] `GeminiAdapter`: 翻译输入/输出协议
    - `BeforeTool` ↔ `before-tool`
    - `BeforeAgent` ↔ `before-agent`
    - `decision` 字段直通
- [x] 统一决策模型：`{ decision: allow/deny/ask, reason, message }`

### Hook 配置生成
生成的配置示例：
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "monoco hook run agent before-tool"
          }
        ]
      }
    ]
  }
}
```

### 集成
- [x] 注册 `ClaudeCodeDispatcher` 和 `GeminiDispatcher` 到 `UniversalHookManager`
- [x] 在 `monoco sync` 中触发 Agent Hooks 同步
- [x] 在 `monoco uninstall` 中清理 Agent Hooks

## Review Comments

### 设计与架构回顾

1. **ACL (Anti-Corruption Layer)** 模式应用得非常成功。通过 `UniversalInterceptor` 这一薄层，将各个 Agent 平台（Claude Code, Gemini CLI）特有的协议细节完全屏蔽在 Monoco 核心逻辑之外。
2. **Dispatcher 设计** 保持了高度的一致性。`ClaudeCodeDispatcher` 和 `GeminiDispatcher` 遵循相同的接口，通过配置注入而非脚本复制的方式，提高了系统的整体稳定性和可维护性。
3. **集成方案** 充分利用了现有的 `monoco sync` 机制，实现了无感的 Agent 环境同步。

### 审查结论

代码质量优秀，协议适配精准，符合 Monoco 分布式、低耦合的设计理念。已验证 `before-tool` 和 `before-agent` 事件的正确转换与拦截。

建议立即合并并关闭 Issue。


### Implementation Summary

#### 1. AgentHookDispatcher Framework
- **Base Class** (`AgentHookDispatcher`): Abstract base class with provider auto-detection via environment variables (`CLAUDE_CODE_REMOTE`, `GEMINI_ENV_FILE`)
- **ClaudeCodeDispatcher**: Specialized dispatcher for Claude Code that:
  - Injects hook configurations into `.claude/settings.json`
  - Maps Monoco events to Claude events: `before-tool` → `PreToolUse`, `before-agent` → `UserPromptSubmit`
  - Generates matcher-based hook configurations
- **GeminiDispatcher**: Specialized dispatcher for Gemini CLI that:
  - Injects hook configurations into `.gemini/settings.json`
  - Maps Monoco events to Gemini events: `before-tool` → `BeforeTool`, `before-agent` → `BeforeAgent`

#### 2. UniversalInterceptor (ACL Layer)
- **Runtime Detection**: Auto-detects agent platform from environment variables
- **Protocol Translation**:
  - `ClaudeAdapter`: Translates Claude's `permissionDecision` to unified `decision`, `PreToolUse` to `before-tool`
  - `GeminiAdapter`: Translates Gemini's `decision` field directly, `BeforeTool` to `before-tool`
- **Unified Decision Model**: `{ decision: allow/deny/ask, reason, message }`

#### 3. Integration
- Updated `monoco sync` to use new dispatchers with `sync()` method for full synchronization
- Updated `monoco uninstall` to clean up Agent hooks from settings files
- Updated `monoco hook run` to use UniversalInterceptor for agent hooks

### Files Changed
- `monoco/features/hooks/dispatchers/agent_dispatcher.py` - Complete rewrite with ACL support
- `monoco/features/hooks/dispatchers/__init__.py` - Export new classes
- `monoco/features/hooks/universal_interceptor.py` - New file (ACL runtime)
- `monoco/features/hooks/__init__.py` - Export UniversalInterceptor and adapters
- `monoco/features/hooks/commands.py` - Updated `run` command for agent hooks
- `monoco/core/sync.py` - Updated sync and uninstall for agent hooks
