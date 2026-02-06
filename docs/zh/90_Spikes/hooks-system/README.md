# Spike: 通用 Hooks 系统 (Universal Hooks System)

> 专题编号：SPIKE-HOOKS
> 关联 Issue：[FEAT-0173 实现通用 Hooks 注册与安装机制](../../../Issues/Features/open/FEAT-0173-implement-universal-hooks-registration-and-install.md)

## 1. 概述

本 Spike 旨在调研主流 Agent 框架（如 Claude Code, Gemini CLI）、Git 以及 IDE（如 VSCode）的钩子（Hooks）机制，为 Monoco 构建一套统一、可扩展且支持多平台的 Hooks 管理系统方案。

### 核心挑战

- **跨平台兼容性**：同一份 Hook 脚本如何同时服务于 Git, Claude Code, Gemini CLI 等不同目标环境。
- **元数据管理**：如何声明 Hook 的触发时机（Events）、匹配规则（Matchers）和安装目标。
- **生命周期自动化**：通过 `monoco sync` 实现零配置安装，通过 `monoco uninstall` 实现彻底清理。

## 2. 调研进度

| 专题                          | 状态      | 说明                                               |
| :---------------------------- | :-------- | :------------------------------------------------- |
| [Agent Hooks](./agent_hooks/) | 🟢 已完成 | 调研了 Claude Code 和 Gemini CLI 的机制。          |
| [Git Hooks](./git_hooks/)     | 🟢 已完成 | 制定了 Git Hooks 的通用 Front Matter 协议与映射。  |
| [IDE Hooks](./ide_hooks/)     | 🟢 已完成 | 明确了 VS Code 配置注入与协议级 Hooks 的集成路径。 |

## 3. 详细报告索引

### Agent Hooks

- [Claude Code Hooks 调查报告](./agent_hooks/claude_code_hooks_ZH.md)
- [Gemini CLI Hooks 调查报告](./agent_hooks/gemini_cli_hooks_ZH.md)
- [**重点：统一防腐层 (ACL) 设计方案**](./agent_hooks/acl_unified_protocol_ZH.md)

### Git Hooks

- [Git Hooks 标准化方案](./git_hooks/git_hooks_standard_ZH.md)

### IDE Hooks

- [IDE Hooks 标准化方案 (VS Code & LSP)](./ide_hooks/ide_hooks_standard_ZH.md)

---

## 4. 方案构思 (Draft)

基于调研结果，Monoco 通用 Hooks 系统将采用 **脚本注释 Front Matter** (Inspired by Claude Code/Gemini CLI) 方案：

```bash
#!/bin/bash
# ---
# type: agent
# agent_type: gemini-cli
# event: BeforeTool
# matcher: write_file
# ---
# Hook logic here...
```

`UniversalHookManager` 将通过解析这些元数据，决定将其安装到 `.git/hooks/`, `.claude/settings.json` 还是 `.gemini/settings.json` 中。
