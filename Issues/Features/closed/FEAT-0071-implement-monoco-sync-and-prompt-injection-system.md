---
id: FEAT-0071
uid: d32825
type: feature
status: closed
stage: done
title: Implement Monoco Sync and Prompt Injection System
created_at: '2026-01-15T15:01:21'
opened_at: '2026-01-15T15:01:21'
updated_at: '2026-01-15T15:09:32'
closed_at: '2026-01-15T15:09:32'
parent: EPIC-0014
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0014'
- '#FEAT-0071'
- agent-native
- cli
- prompt-engineering
---

## FEAT-0071: Implement Monoco Sync and Prompt Injection System

## 背景 (Context)

为了实现 "Agent Environment Integration"，我们需要一个核心机制来协调各 Feature 模块，收集它们对 Agent 环境的需求（如 System Prompt），并将其注入到目标文件（如 GEMINI.md）。

## 目标 (Objective)

实现 `monoco sync` 命令及底层的注入引擎。

1. **Core Sync Loop**: 遍历注册的 Feature，收集 `integrate()` 返回的元数据。
2. **Prompt Injection Strategy**: 定义规范的 Markdown 结构（H3 Global / H4 Feature），实现幂等写入。
3. **Agent Manager**: 支持 `CLAUDE.md`, `GEMINI.md`, `QWEN.md`, `AGENTS.md` (Neutral)。忽略 `Cursor` 及其它 IDE 专属配置。
4. **Scope Control**: 支持 Project (CWD), User (Global), 或特定目录的注入。

## 验收标准 (Acceptance Criteria)

- [x] **Feature Protocol**: 所有的 Feature (Issue/Spike/Config) 都必须通过 standard Protocol 暴露 Prompt。
- [x] **Sync Command**: `monoco sync` 能够正确生成或更新 `GEMINI.md` 等文件。
- [x] **Idempotency**: 多次运行 sync，文件内容应当保持稳定，不会产生重复段落。
- [x] **Managed Block**: 仅修改 `# Monoco Toolkit` 及其子标题下的内容，不触碰用户手写的其他段落。
- [x] **Multi-Target**: 一次 sync 可以同时更新多个 Agent 配置文件（如同时存在 CLAUDE.md 和 GEMINI.md 时）。

## 技术任务 (Technical Tasks)

- [x] **Core**: 定义 `MonocoFeature` Protocol (Python Abstract Base Class)，包含 `integrate() -> IntegrationData`。
- [x] **Core**: 实现 `FeatureRegistry`，动态加载 core features。
- [x] **Sync Engine**: 实现 `PromptInjector` 类。
  - [x] 支持 Markdown AST 解析或 Regex 匹配。
  - [x] 实现 "Find or Create Section" 逻辑（H3 `### Monoco Toolkit`）。
  - [x] 实现子段落（H4）的排序与拼接。
- [x] **CLI**: 实现 `monoco sync` 命令。
  - [x] 参数: `--targets` (default: auto detect), `--path` (default: cwd).
- [x] **Adapters**: 为现有的 `issue`, `spike`, `config` 模块实现 `integrate()` 接口，暴露其 System Prompts。

## Review Comments

- [x] Self-Review
