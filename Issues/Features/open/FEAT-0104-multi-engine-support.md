---
id: FEAT-0104
uid: g7h8i9
type: feature
status: open
stage: draft
title: 支持多引擎适配 (Gemini & Claude)
created_at: '2026-01-25T14:30:00'
updated_at: '2026-01-25T14:30:00'
priority: medium
parent: null
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0008'
- '#FEAT-0104'
files:
- monoco/features/scheduler/worker.py
- monoco/features/scheduler/engines.py
---

## FEAT-0104: 支持多引擎适配 (Gemini & Claude)

### 目标
重构 Worker 的执行层，支持除了 `gemini` 之外的 `claude` 引擎，并为未来扩展预留接口。

### 背景
目前 `worker.py` 中直接硬编码了针对 `gemini` CLI 的调用逻辑（`[engine, "-y", prompt]`）。随着模型生态的发展，我们需要支持 Claude 等其他强大的 Agent 运行时。

### 需求
1. **抽象引擎接口**: 定义 `AgentEngine` 协议或基类，负责组装命令行参数。
2. **实现适配器**:
   - `GeminiEngine`: 对应 `gemini -y <prompt>`。
   - `ClaudeEngine`: 对应 `claude <prompt>` (需确认具体 CLI 参数)。
3. **配置集成**: Role 定义中 `engine` 字段应能动态选择适配器。
4. **错误处理**: 针对不同引擎的特定错误（如 Auth 失败、Rate Limit）提供统一的异常封装。

### 任务
- [ ] 创建 `monoco/features/scheduler/engines.py`。
- [ ] 定义 `EngineAdapter` 抽象基类。
- [ ] 迁移现有的 Gemini 逻辑到 `GeminiAdapter`。
- [ ] 实现 `ClaudeAdapter` (需调研 anthropic cli 调用方式)。
- [ ] 修改 `Worker` 类，在初始化时通过工厂模式获取 Adapter 实例。
