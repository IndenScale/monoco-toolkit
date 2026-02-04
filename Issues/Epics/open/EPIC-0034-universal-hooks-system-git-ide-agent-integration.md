---
id: EPIC-0034
uid: fc7d0a
type: epic
status: open
stage: draft
title: 'Universal Hooks System: Git/IDE/Agent Integration'
created_at: '2026-02-04T13:26:48'
updated_at: '2026-02-04T14:50:00'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0034'
- '#FEAT-0174'
- '#FEAT-0175'
- '#FEAT-0176'
- '#FEAT-0177'
files:
- docs/zh/90_Spikes/hooks-system/README.md
- docs/zh/90_Spikes/hooks-system/agent_hooks/acl_unified_protocol_ZH.md
- docs/zh/90_Spikes/hooks-system/agent_hooks/claude_code_hooks_ZH.md
- docs/zh/90_Spikes/hooks-system/agent_hooks/gemini_cli_hooks_ZH.md
- docs/zh/90_Spikes/hooks-system/git_hooks/git_hooks_standard_ZH.md
- docs/zh/90_Spikes/hooks-system/ide_hooks/ide_hooks_standard_ZH.md
criticality: high
solution: null
opened_at: '2026-02-04T13:26:48'
---

## EPIC-0034: Universal Hooks System: Git/IDE/Agent Integration

## 背景

目前 Monoco 仅支持基础的 Git Hooks（基于文件名识别），但随着功能扩展，我们需要支持多 Agent 框架（如 Claude Code, Gemini CLI）以及 IDE 场景下的钩子。原有的管理方式无法承载复杂的元数据需求（如类型细分、平台适配、动态开启等）。

## 目标

实现一套基于脚本注释 Front Matter 的通用 Hooks 注册、解析与安装机制，并将其深度集成到 `monoco sync` 流程中。

## 架构决策

基于 Spike 调研（[SPIKE-HOOKS](../../docs/zh/90_Spikes/hooks-system/README.md)），采用**类型分层 + Provider 细分**的架构：

### 1. 一级分类：Hook 类型 (type)

| 类型 | 说明 | 触发场景 | Provider 必填 |
|------|------|----------|--------------|
| `git` | 原生 Git Hooks | 提交、合并、推送等 Git 操作 | 否 |
| `ide` | IDE 集成 Hooks | 文件保存、项目打开、构建等 | 是 |
| `agent` | Agent 框架 Hooks | Agent 会话、工具调用、权限请求等 | 是 |

### 2. 二级分类：Provider 细分

**Agent Providers:**
| Provider | 标识符 | 配置目标 |
|----------|--------|----------|
| Claude Code | `claude-code` | `.claude/settings.json` |
| Gemini CLI | `gemini-cli` | `.gemini/settings.json` |

**IDE Providers:**
| Provider | 标识符 | 配置目标 |
|----------|--------|----------|
| VS Code | `vscode` | `.vscode/tasks.json`, `.vscode/settings.json` |

### 3. 安装目标路径

```
.git/hooks/<event>                    # git 类型
.claude/settings.json → hooks[]       # agent 类型 + provider: claude-code
.gemini/settings.json → hooks[]       # agent 类型 + provider: gemini-cli
.vscode/tasks.json                    # ide 类型 + provider: vscode
```

### 4. 防腐层 (ACL) 设计

- **Agent Hooks 需要 ACL**: 不同 Agent 平台的 JSON 协议、字段命名、决策模型存在差异
- **Git/IDE Hooks 直接透传**: 无需协议转换，Monoco 仅负责安装和触发管理

## 子任务拆分

| Issue | 内容 | 依赖 |
|-------|------|------|
| FEAT-0174 | Core Models and Parser | - |
| FEAT-0175 | Git Hooks Dispatcher | FEAT-0174 |
| FEAT-0176 | Agent Hooks with ACL | FEAT-0174 |
| FEAT-0177 | IDE Hooks Dispatcher | FEAT-0174 |

## 验收标准

- [x] 完成 Spike 调研：Agent/Git/IDE Hooks 标准化方案
- [ ] 完成 FEAT-0174: 核心模型与解析器
- [ ] 完成 FEAT-0175: Git Hooks 分发器
- [ ] 完成 FEAT-0176: Agent Hooks 与 ACL 层
- [ ] 完成 FEAT-0177: IDE Hooks 分发器
- [ ] `monoco sync` 集成所有 Hook 类型
- [ ] `monoco uninstall` 正确清理所有注入的 Hooks

## Review Comments
<!-- 评审阶段时填写 -->
