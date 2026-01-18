---
id: FEAT-0086
uid: d3099b
type: feature
status: closed
stage: done
title: DDD Issue 建模 (影子对象层)
created_at: '2026-01-17T07:56:27'
opened_at: '2026-01-17T07:56:27'
updated_at: '2026-01-17T08:22:07'
closed_at: '2026-01-17T08:22:07'
parent: EPIC-0015
solution: implemented
dependencies: []
related: []
tags:
- '#EPIC-0015'
- '#FEAT-0086'
path: /Users/indenscale/Documents/Projects/Monoco/Toolkit/Issues/Features/open/FEAT-0086-ddd-issue-modeling-shadow-object-layer.md
---

## FEAT-0086: DDD Issue 建模 (影子对象层)

## 目标 (Objective)

将目前基于 "Dict + Regex" 的轻量级 Issue 表示层，重构为基于 **DDD (领域驱动设计)** 的 **充血领域模型 (Shadow Object Layer)**。

这一层将作为 "Markdown 文件" 与 "业务逻辑" 之间的中间件，提供精确的状态管理、Block 级的内容操作能力，并为未来的细粒度 Agent Action 奠定基础。

## 验收标准 (Acceptance Criteria)

- [x] 创建 `monoco.features.issue.domain` 模块。
- [x] 完成 **Issue Aggregate** 的建模，包含 `IssueState`, `IssueFrontmatter`, `IssueBody`。
- [x] 实现 **MarkdownParser**，能够将文档解析为带行号信息的 `ContentBlock` 列表。
- [x] 状态转移逻辑被封装在声明式的 `Transition` 模型中，而非散落在代码各处。
- [x] 更新 `monoco issue inspect` 命令，支持 `--ast` flag 以输出 JSON 格式的 AST 结构以供调试。

## 技术任务 (Technical Tasks)

- [x] **定义领域模型**: 在 `monoco/features/issue/domain/models.py` 中定义以下核心类:
  - `Issue` (Aggregate Root)
  - `IssueFrontmatter` (包含 Metadata 和 State Validation 逻辑)
  - `IssueBody` (Entity) 与 `ContentBlock` (Value Object)
- [x] **实现解析器**: 在 `monoco/features/issue/domain/parser.py` 中实现基于行扫描的解析逻辑，能够识别 Heading, TaskList, Frontmatter 等块类型。
- [x] **状态机建模**: 定义 `Transition` 和 `Action` 模型，并在 `TransitionService` 中实现权限与流转校验。
- [x] **重构 Validator**: 修改 `IssueValidator`，使其遍历 `Issue.body.blocks` 进行逻辑校验，而非重复使用正则。
- [x] **CLI 增强**: 更新 `inspect` 子命令，支持 `monoco issue inspect <id> --ast` 以输出详细的 AST 结构。

## Review Comments

- [x] Self-Review

## Delivery

<!-- Monoco Auto Generated -->

**Commits (1)**:

- `2a1208d` feat(issue): implement ddd issue modeling and parser

**Touched Files (26)**:

- `"Issues/Chores/closed/CHORE-0004-vscode-\346\217\222\344\273\266\347\230\246\345\256\242\346\210\267\347\253\257\346\236\266\346\236\204\351\207\215\346\236\204.md"`
- `.github/workflows/publish-vscode-extension.yml`
- `Kanban/apps/webui/package.json`
- `Kanban/apps/webui/src/app/components/LayoutShell.tsx`
- `Kanban/apps/webui/src/app/components/StatusBar.tsx`
- `Kanban/apps/webui/src/app/contexts/TerminalContext.tsx`
- `Kanban/apps/webui/src/app/providers.tsx`
- `Kanban/apps/webui/src/components/terminal/TerminalPanel.tsx`
- `Kanban/apps/webui/src/components/terminal/XTermView.tsx`
- `debug_import.py`
- `extensions/vscode/.eslintrc.json`
- `extensions/vscode/.gitignore`
- `extensions/vscode/.vscodeignore`
- `extensions/vscode/client/src/bootstrap.ts`
- `extensions/vscode/client/src/extension.ts`
- `extensions/vscode/client/src/test/suite/bootstrap.test.ts`
- `extensions/vscode/server/src/indexer.ts`
- `extensions/vscode/server/src/server.ts`
- `monoco/core/agent/adapters.py`
- `monoco/core/output.py`
- `monoco/features/pty/core.py`
- `monoco/features/pty/router.py`
- `monoco/features/pty/server.py`
- `monoco/features/spike/core.py`
- `monoco/main.py`
- `uv.lock`
