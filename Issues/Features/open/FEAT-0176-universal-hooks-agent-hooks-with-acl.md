---
id: FEAT-0176
uid: 2daae5
type: feature
status: open
stage: draft
title: 'Universal Hooks: Agent Hooks with ACL'
created_at: '2026-02-04T13:27:08'
updated_at: '2026-02-04T14:50:00'
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
- docs/zh/90_Spikes/hooks-system/agent_hooks/acl_unified_protocol_ZH.md
criticality: high
solution: null
opened_at: '2026-02-04T13:27:08'
---

## FEAT-0176: Universal Hooks: Agent Hooks with ACL

## 目标

实现 Agent Hooks 分发器和防腐层（ACL），支持 `type: agent` 的 Hooks 按 `provider` 分发到 Claude Code 和 Gemini CLI。

## 背景

Agent Hooks 需要 ACL 层因为不同 Agent 平台的 JSON 协议、字段命名、决策模型存在差异。详见 [ACL 统一协议设计](../../docs/zh/90_Spikes/hooks-system/agent_hooks/acl_unified_protocol_ZH.md)。

## 验收标准

- [ ] 实现 `AgentHookDispatcher` 基类
- [ ] 实现 `ClaudeCodeDispatcher`：注入 `.claude/settings.json`
- [ ] 实现 `GeminiDispatcher`：注入 `.gemini/settings.json`
- [ ] 实现 `UniversalInterceptor` 运行时拦截器
- [ ] Provider 自动探测（环境变量：`CLAUDE_CODE_REMOTE`, `GEMINI_ENV_FILE`）
- [ ] 协议翻译：Claude/Gemini 协议 ↔ Monoco 统一协议

## 技术任务

### AgentHookDispatcher 框架
- [ ] 实现 `AgentHookDispatcher` 基类
  - [ ] 按 `provider` 字段路由到对应子分发器
- [ ] 实现 `ClaudeCodeDispatcher`
  - [ ] 注入/更新 `.claude/settings.json` 的 `hooks` 数组
  - [ ] 支持事件映射：Monoco `before-tool` → Claude `PreToolUse`
- [ ] 实现 `GeminiDispatcher`
  - [ ] 注入/更新 `.gemini/settings.json` 的 `hooks` 数组
  - [ ] 支持事件映射：Monoco `before-tool` → Gemini `BeforeTool`

### UniversalInterceptor (ACL 层)
- [ ] 实现 `universal-interceptor` 脚本（Python）
- [ ] Provider 自动探测：
  - [ ] Claude: 检测 `CLAUDE_CODE_REMOTE` 环境变量
  - [ ] Gemini: 检测 `GEMINI_ENV_FILE` 环境变量
- [ ] 实现适配器：
  - [ ] `ClaudeAdapter`: 翻译输入/输出协议
    - `PreToolUse` ↔ `before-tool`
    - `UserPromptSubmit` ↔ `before-agent`
    - `permissionDecision` → `decision`
  - [ ] `GeminiAdapter`: 翻译输入/输出协议
    - `BeforeTool` ↔ `before-tool`
    - `BeforeAgent` ↔ `before-agent`
    - `decision` 字段直通
- [ ] 统一决策模型：`{ decision: allow/deny/ask, reason, message }`

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
- [ ] 注册 `ClaudeCodeDispatcher` 和 `GeminiDispatcher` 到 `UniversalHookManager`
- [ ] 在 `monoco sync` 中触发 Agent Hooks 同步
- [ ] 在 `monoco uninstall` 中清理 Agent Hooks

## Review Comments
<!-- 评审阶段时填写 -->
