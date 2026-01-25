---
id: FEAT-0106
type: feature
status: closed
stage: done
title: 通过根节点 (Sink Root) 强制执行 Epic 的显式父级关联
created_at: '2026-01-25T00:00:00'
updated_at: '2026-01-25T22:11:13'
priority: high
parent: EPIC-0000
dependencies: []
related: []
domains:
- intelligence
tags:
- '#EPIC-0000'
- '#FEAT-0106'
- issue-system
- linter
- toolkit
files: []
closed_at: '2026-01-25T22:11:13'
solution: implemented
owner: indenscale
---

## FEAT-0106: 通过根节点 (Sink Root) 强制执行 Epic 的显式父级关联

### 问题 (Problem)
当前的 Linter 配置会针对缺失 `parent`、`dependencies` 和 `related` 字段的 Epic 报告 `Schema Error`。与其他 Ticket 类型不同，顶层 Epic 在逻辑上确实没有父级，导致严格的 Schema（要求显式字段）与物理现实之间存在冲突。

### 解决方案 (Solution)
实施 "Sink Epic" 模式：
1.  **协议 (Protocol)**：建立 `EPIC-0000` 作为 Monoco 宇宙的虚拟/物理根节点。
2.  **Schema**：维持对 `parent` 字段的严格要求，以消除歧义。
3.  **自动化 (Automation)**：
    -   更新 `monoco issue create`，在创建 Epic 时默认指向 `EPIC-0000`。
    -   为现有的“孤儿” Epic 提供迁移路径。

### 任务 (Tasks)

- [x] 在 `Monoco/Issues` 中定义 `EPIC-0000` 规范。
- [x] 更新 `IssueMetadata` 模型以确认严格的字段验证配置。
- [x] 修改 `monoco issue create` 命令以注入 Epic 的默认父级。
- [x] 创建迁移脚本或手动更新 Toolkit 中现有的孤儿 Epic。
- [x] 验证 `monoco issue lint --json` 在 Epic 上不再通过 Schema Error。

## Review Comments

- [x] Self-Review
