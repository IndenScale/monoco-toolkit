---
id: FEAT-0149
uid: 7750aa
type: feature
status: backlog
stage: freezed
title: 设计与实现 Monoco 原生钩子系统
created_at: '2026-02-01T20:56:45'
updated_at: '2026-02-02T10:39:38'
parent: EPIC-0025
dependencies: []
related:
- EPIC-0025
domains:
- AgentEmpowerment
tags:
- '#EPIC-0000'
- '#EPIC-0025'
- '#FEAT-0149'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-01T20:56:45'
---

## FEAT-0149: 设计与实现 Monoco 原生钩子系统

## 背景与目标

本 Epic 旨在设计和实现 Monoco 原生钩子系统，用于统一管理代理生命周期和生态系统工具。通过建立标准化的事件总线和钩子接口，解决当前 CLI 工具（如 gemini、kimi）私有钩子导致的生态碎片化问题。该系统将提供比标准 Git 钩子更丰富的上下文信息（如会话 ID、Issue ID），支持跨不同代理和工具的生命周期事件编排。

## 目标

实现统一的 Monoco 原生钩子系统，用于管理代理生命周期和生态系统工具，解决 CLI 工具（gemini、kimi 等）中私有钩子导致的生态碎片化问题。

**背景：**
- **问题**：当前 CLI 工具（gemini、kimi）实现了各自的私有代理钩子，导致生态系统碎片化。标准 Git 钩子缺乏必要的上下文信息（如会话 ID、Issue ID）。
- **目标**：创建一个原生钩子系统，能够跨不同代理和工具编排生命周期事件。
- **参考**：
    - **Kimi CLI 钩子**：Kimi CLI 支持 "Wire Mode"（基于标准输入输出的 JSON-RPC），可发出 `TurnBegin`、`StepBegin`、`ToolCall` 等事件。这是比内部钩子更推荐的集成方式。

## 调研结论 (2026-02-02)

经过对 Kimi Agent SDK、Claude Agent SDK、Gemini CLI Hooks 和 ACP (Agent Client Protocol) 的深入调研，**决定搁置此特性**。

### 各平台现状

| 平台 | Hook 系统 | 架构方式 | 事件类型 | 通信协议 |
|------|-----------|----------|----------|----------|
| **Kimi CLI/SDK** | Wire Protocol | JSON-RPC 事件流 | `TurnBegin`, `StepBegin`, `ToolCall`, `ApprovalRequest` | JSON-RPC over stdio |
| **Claude Code/SDK** | Native Hooks | 回调函数 | `PreToolUse`, `PostToolUse`, `UserPromptSubmit` | 内部 SDK 协议 |
| **Gemini CLI** | External Hooks | 外部命令 | `BeforeTool`, `AfterTool`, `BeforeAgent` | stdin/stdout JSON |
| **ACP** | 协议标准 | LSP-like | 未定义 Hooks | JSON-RPC |

### 标准化障碍

1. **架构差异巨大**：Kimi 使用 JSON-RPC 事件流，Claude 使用回调函数，Gemini 使用外部命令
2. **事件模型不兼容**：Kimi 采用 Turn→Step→ToolCall 层级，Claude/Gemini 采用 Pre/Post 钩子模式
3. **通信协议不同**：JSON-RPC vs 内部协议 vs Plain JSON
4. **控制权模型差异**：请求-响应 vs 回调返回值 vs 退出码
5. **生态定位分化**：各厂商都在构建自己的生态护城河，趋势是分化而非收敛

### 建议

- **时机不成熟**：各平台尚未形成统一标准，ACP 也未涉及 Hooks 标准
- **技术债务风险**：现在强行实现，未来标准出台后需要大规模重构
- **替代方案**：聚焦 Git Hooks 集成（FEAT-0145），等待 ACP 成熟

详见调研报告（可询问查看完整报告）。

## 验收标准
- [-] Monoco 钩子系统架构已定义并文档化。
- [-] 核心钩子引擎已实现。
- [-] 已演示与 Kimi CLI "Wire Mode" 的集成。
- [x] 标准 Git 钩子（pre-commit、pre-push）已通过 Monoco 集成（参见 FEAT-0145）。

## 技术任务
- [-] 设计事件总线和钩子接口。
- [-] 在 `monoco/core/hooks` 中实现钩子注册表。
- [-] 实现 Kimi CLI Wire Mode 适配器。
- [x] 实现 Git 钩子集成（参见 FEAT-0145）。

## Review Comments

### 2026-02-02 调研结论

**决定**：将此特性移至 backlog，等待行业标准成熟。

**理由**：
1. Agent Hooks 标准化是一个"过早优化"的问题
2. 当前各平台都在快速迭代，标准尚未稳定
3. Monoco 应暂时跟随而非引领这一领域
4. 资源应投入到更有价值的特性上

**后续行动**：
- 关注 ACP (Agent Client Protocol) 发展
- 定期检查各平台 Hooks 标准是否收敛
- 保持与 Kimi Wire Protocol 的兼容性（已支持）
