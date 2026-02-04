# Monoco Unified Hooks System

> **Status**: Implemented & Operational
> **Domain**: Foundation, DevEx
> **Related Epic**: [EPIC-0034](../../Issues/Epics/open/EPIC-0034-universal-hooks-system-git-ide-agent-integration.md)

## 1. 系统概述

Monoco Unified Hooks System 是一个跨平台、多智能体的统一钩子管理框架。它通过拦截 Git 生命周期、IDE 事件及 Agent 行为，将静态的 Skill 约束转化为 **Just-in-Time (JIT) 劝导**。

### 核心优势
- **协议解耦 (ACL)**: 一套脚本逻辑通过 `UniversalInterceptor` 自动适配 Gemini CLI 和 Claude Code。
- **非破坏性安装**: Git Dispatcher 自动备份并合并现有钩子，确保与 Husky/pre-commit 兼容。
- **按需触发**: 支持基于 Glob Matcher 的暂存文件过滤，减少无效执行。

## 2. 核心架构

### 2.1 拦截器 (Universal Interceptor / ACL)
位于 `monoco.features.hooks.universal_interceptor`。它充当 Agent 与 Monoco 之间的翻译官：
1. **输入归一化**: 将 `Gemini.BeforeTool` 或 `Claude.PreToolUse` 转换为 `UnifiedHookInput`。
2. **脚本执行**: 注入 `MONOCO_HOOK_EVENT` 等环境变量，通过 `stdin` 传递 JSON。
3. **输出适配**: 将脚本返回的 `UnifiedDecision` 转换回特定 Agent 的 JSON 协议（如 Gemini 的 `hookSpecificOutput`）。

### 2.2 分发器 (Dispatchers)
位于 `monoco.features.hooks.dispatchers`。负责物理安装：
- **GitDispatcher**: 在 `.git/hooks/` 下创建 Shell 代理脚本。
- **AgentDispatcher**: 在 `.gemini/settings.json` 或 `.claude/settings.json` 中注入配置条目。

## 3. 脚本开发规范

### 3.1 Front Matter 声明
所有脚本必须在头部声明元数据，由 `HookParser` 解析：

```bash
#!/bin/bash
# ---
# type: agent
# provider: gemini-cli
# event: before-tool
# matcher: ["write_file", "replace"]
# priority: 10
# description: "执行写入前的分支安全检查"
# ---
```

### 3.2 响应协议 (UnifiedDecision)
脚本必须向 `stdout` 输出 JSON：

```json
{
  "decision": "allow",     // allow | deny | ask
  "reason": "...",        // 仅 deny 时必填
  "message": "...",       // 显示给用户的 UI 消息
  "metadata": {           // 扩展上下文
    "additionalContext": "这里注入 JIT 劝导提示词"
  }
}
```

## 4. 管理命令

| 操作 | 命令 |
| :--- | :--- |
| **同步安装** | `monoco sync` (自动扫描脚本并分发) |
| **手动测试** | `python -m monoco.features.hooks.universal_interceptor <path> < input.json` |
| **清理** | `monoco uninstall` |

## 5. JIT 劝导最佳实践

利用 `metadata.additionalContext` 字段，你可以：
1. **纠正行为**: 当 Agent 忘记 `sync-files` 时，拦截并给出指令。
2. **风险警示**: 当 Agent 修改核心模块时，注入“请务必运行测试”的提示。
3. **强制工作流**: 阻止在 `main` 分支进行任何 `write_file` 操作。
