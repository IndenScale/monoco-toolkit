---
id: FEAT-0010
type: feature
status: closed
stage: Done
priority: NORMAL
solution: implemented
title: 增强 Init 命令 (Enhanced Init Command)
description: 'Expand `monoco init` to recursively initialize all sub-modules (Issue,
  Spike, I18n, Skills) to ensure a fully ready environment with a single command.

  '
dependencies: []
related: []
tags:
- '#EPIC-0001'
- '#FEAT-0010'
- cli
- devops
- init
parent: EPIC-0001
uid: a66263
---

## FEAT-0010: 增强 Init 命令 (Enhanced Init Command)

## 目标 (Objective)

增强 `monoco init`，使其成为项目初始化的单一入口。它不仅应该脚手架 `Issues` 目录，还应该触发 `Spike`、`I18n` 和 `Skills` 模块的初始化逻辑，确保只需一个命令即可完成完整一致的环境设置。

## 对比与差距分析 (Comparison & Gap Analysis)

| 模块       | 当前 `monoco init`                    | 当前能力                                                | 差距                                                        |
| :--------- | :------------------------------------ | :------------------------------------------------------ | :---------------------------------------------------------- |
| **Core**   | 脚手架 `.monoco/config.yaml`.         | `core/setup.py` 中的 `init_cli`                         | 无.                                                         |
| **Issue**  | 脚手架 `Issues/{Type}` 目录 (硬编码). | 基本目录创建.                                           | 逻辑硬编码在 `core/setup.py` 中，而不是委托给 `issue` 模块. |
| **Spike**  | **忽略**.                             | 存在 `monoco spike init` (设置 `.gitignore`, 创建目录). | `init` 不调用 `spike init`.                                 |
| **I18n**   | **忽略**.                             | 无 `init` 命令. 依赖 `config` 默认值.                   | 应该填充 `config.i18n` 或确保默认值明确.                    |
| **Skills** | **忽略**.                             | 无代码.                                                 | 需要脚手架 `Toolkit/skills` 或类似结构.                     |

## 技术任务 (Technical Tasks)

- [x] **基础设施: 模块资源接口**: 定义一种标准方式 (`get_resources()`) 供功能模块 (`issue`, `spike`, `i18n`) 暴露其 `SKILL` (文档) 和 `PROMPT` (代理指南) 内容。
- [x] **重构 Issue Init**: 将 Issue 目录脚手架从 `core/setup.py` 提取到 `features/issue`。实现 `get_resources` 以返回 Issue 管理技能。
- [x] **重构 Spike Init**: 集成 `spike.init`。实现 `get_resources` 以返回 Spike 方法论技能。
- [x] **创建 I18n Init**: 实现 `i18n.init`。实现 `get_resources` 以返回 I18n 工作流技能。
- [x] **实现 Skills Init**:
  - 创建 `Toolkit/skills` 目录。
  - 从所有模块聚合 `SKILL` 内容，并在 `Toolkit/skills` 中写入/更新相应文件。
- [x] **实现 Agent 文档注入**:
  - 目标 `AGENTS.md`, `GEMINI.md`, 和 `CLAUDE.md`。
  - 实现“部分替换”实用程序: 找到 `## Monoco Toolkit`，替换直到下一个 `##` 或 EOF 之间的所有内容为来自模块的聚合 `PROMPT` 内容。
  - 确保幂等性（无重复部分）。
- [x] **编排**: 更新 `monoco.core.setup.init_cli` 以驱动此序列。

## 实施说明 (Implementation Notes)

- **术语更新**: 在重构 `issue` 模块资源期间，术语已从 `Story/Task/Bug` 更新为 **`Feature/Chore/Fix`** 以与 Agentic 工作流保持一致。
- **Feature 定义**: `Feature` (前身为 Story) 的定义已明确增强为 `Feature = Design + Dev + Test + Doc + i18n`，强制文档和国际化作为原子价值交付的一部分。
- **资源聚合**: `skills` 模块现在动态地从注册的功能模块中提取 `SKILL` 和 `PROMPT` 内容，确保 `monoco init` 始终部署最新的定义而无需代码重复。

## 验收标准 (Acceptance Criteria)

1.  **一站式服务 (One-Stop Shop)**: `monoco init` 设置 Config, Issues, Spikes, I18n, 和 **Skills**。
2.  **技能填充 (Skill Population)**: `Toolkit/skills` 填充了源自模块本身的 `issue`, `spike`, `i18n` 技能指南。
3.  **Agent 文档 (Agent Docs)**: `AGENTS.md` (及其他) 被创建/更新。它们包含 `## Monoco Toolkit` 部分，其中包含所有已启用模块的说明。
4.  **幂等性 (Idempotency)**: 多次运行 `init` 会就地更新 `## Monoco Toolkit` 部分而不会重复。
5.  **模块化 (Modular)**: Core 不持有内容字符串；它从模块中提取。

## Review Comments

- [x] Self-Review
