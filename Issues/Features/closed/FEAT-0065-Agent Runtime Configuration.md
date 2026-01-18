---
id: FEAT-0065
uid: 28f630
type: feature
status: closed
stage: done
title: 智能体运行时配置 (Agent Runtime Configuration)
created_at: "2026-01-15T08:55:53"
opened_at: "2026-01-15T08:55:53"
updated_at: "2026-01-16T08:34:01"
closed_at: "2026-01-16T08:34:01"
parent: EPIC-0012
solution: implemented
dependencies: []
related: []
tags: []
---

## FEAT-0065: 智能体运行时配置 (Agent Runtime Configuration)

## 目标

实现智能体运行时（如 Cursor, Gemini CLI, Claude Desktop）的配置层。
Monoco 将实际的模型推理和提供商管理委托给这些运行时。
本功能严格专注于配置 Monoco 与这些工具之间的“桥梁”。

## 验收标准

1. **注册配置**: 用户可以在 `monoco.yaml` (或 `.monoco/config.yaml`) 中启用/禁用特定的智能体运行时。
2. **路径解析**: 用户可以覆盖运行时的默认可执行文件路径（例如指向特定的 `cursor` 二进制文件）。
3. **无提供商管理**: 明确移除任何管理模型提供商 API 密钥或模型 ID 的逻辑。Monoco 假设运行时会处理这些内容。

## 技术任务

- [x] 在 `monoco.core.config` 中定义 `AgentRuntimeConfig` 模式。
- [x] 在 `monoco.core.integrations` 中实现配置加载与合并逻辑。
- [x] 更新 `DetectFrameworks` 以尊重用户覆盖（例如，如果某个运行时被显式禁用）。

## Review Comments

- [x] Self-Review
