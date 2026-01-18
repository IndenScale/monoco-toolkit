---
id: FEAT-0081
uid: 009188
type: feature
status: closed
stage: done
title: 'Prompty Action System: Context-Aware Agent Skills'
created_at: '2026-01-15T23:46:19'
opened_at: '2026-01-15T23:46:19'
updated_at: '2026-01-15T23:52:11'
closed_at: '2026-01-15T23:52:11'
parent: EPIC-0010
solution: implemented
dependencies: []
related: []
tags:
- '#EPIC-0010'
- '#FEAT-0081'
---

## FEAT-0081: Prompty Action System: Context-Aware Agent Skills

## 目标 (Objective)

重构 Agent 执行系统，从内置硬编码的 `executions` 模式切换为基于 **Prompty** 格式的动态 **Action** 体系。支持从用户全局和项目局部加载配置，并根据当前编辑器的上下文内容（如 Issue 类型、阶段等）动态过滤和展示可用 Action。

## 策略 (Strategy)

1. **Prompty 格式适配**: 采用标准 Prompty 格式（YAML Frontmatter + Template），增加 Monoco 特有的 `when` 匹配逻辑。
2. **多级发现模式**:
   - 用户级: `~/.monoco/actions/*.prompty`
   - 项目级: `./.monoco/actions/*.prompty`
3. **上下文评估引擎**: 在 Frontmatter 中定义 `when` 字段（支持 `idMatch`, `typeMatch`, `stageMatch` 等），后端负责评估当前文件是否符合触发条件。
4. **接口升级**: 升级 CLI `monoco agent list` 接口，支持传入当前文件的元数据，返回动态过滤后的结果。

## 验收标准 (Acceptance Criteria)

1. 系统不再从 `monoco/features/*/executions/` 加载内置动作。
2. 在 `~/.monoco/actions/` 下放置一个 `.prompty` 文件，CLI `monoco agent list` 能成功识别。
3. 在 `.prompty` 的 Frontmatter 中设置 `when.stage: "draft"`，则该动作仅在文件 `stage` 为 `draft` 时出现在 Hover/CodeLens 中。
4. VS Code Extension 能够将当前文件的 Frontmatter 实时传递给后端进行过滤评估。

## 技术任务 (Technical Tasks)

- [x] **[Core]** 实现 `monoco.core.agent.prompty.PromptyAction` 模型与解析器。
- [x] **[Core]** 实现 `ActionRegistry` 支持多路径扫描（$HOME 与 Project）。
- [x] **[Core]** 实现上下文匹配逻辑 (Context Matcher)，支持对 IssueMetadata 字段进行评估。
- [x] **[CLI]** 升级 `monoco agent list --json`，支持通过 `--context` 传入 JSON 元数据进行动态过滤。
- [x] **[LSP/Extension]** 在请求 Actions 时提取当前 Markdown 的 Frontmatter 并作为上下文发送。
- [x] **[UI]** 适配新的动作展示逻辑，确保 Sidebar/Hover/CodeLens 同步更新。

## Review Comments

- [x] Self-Review
