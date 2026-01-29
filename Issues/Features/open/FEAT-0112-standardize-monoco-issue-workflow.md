---
id: FEAT-0112
type: feature
status: open
stage: review
title: 标准化 Monoco Issue 工作流
created_at: '2026-01-29T23:05:07'
updated_at: '2026-01-29T23:11:58'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0112'
files: []
isolation:
  type: branch
  ref: feat/feat-0112-标准化-monoco-issue-工作流
  created_at: '2026-01-29T23:05:08'
---

## FEAT-0112: 标准化 Monoco Issue 工作流

将 Monoco Issue 工作流整合为严格的 "Plan - Build - Submit - Merge" 模型，通过新的 Flow Skill 和更新的 CLI 行为强制执行。

### 背景

当前工作流定义较为松散，存在歧义（例如 Action 与 State 的区别）。我们需要规范生命周期，以更好地支持自主代理（Validator over Reviewer）并强制执行工程规范（默认分支隔离）。

### 核心概念

1.  **4 个原子操作**:
    *   **Plan**: 创建/编辑 Issue。状态: `Draft`。
    *   **Build**: 开始工作。状态: `Doing`。
    *   **Submit**: 触发 Oracle/Validator。状态: `Review` (如果通过)。
    *   **Merge**: 交付价值。状态: `Done`。
2.  **Validator over Reviewer**: `Submit` 是触发 Oracle 的闸门。
3.  **隔离**: `Build` (Start) 默认必须强制执行隔离（分支）。

### 任务

- [x] **CLI 重构: 默认分支**
    - 修改 `monoco issue start` 默认使用 `--branch`。
    - 添加 `--no-branch` 或 `--direct` 标志用于特权主分支操作。
- [x] **Skill: Monoco Flow**
    - 创建 `Toolkit/monoco/skills/monoco-flow/SKILL.md`。
    - 定义 4-Action 模型的规范 Mermaid 流程图。
    - 显式建模 "Oracle Loop" (Submit -> Reject -> Fix -> Retry)。
- [x] **文档更新**
    - 更新 `Cortex/docs/zh/theory/` 以反映规范模型。
    - 更新 `monoco-issue` 中的 `SKILL.md` 以引用新定义（本体层）。

### 验收标准

- [x] `monoco issue start <ID>` 无需标志自动创建分支。
- [x] 新 skill `/flow:monoco-flow` 引导代理完成标准化生命周期。
- [x] 文档清楚区分 Actions（动词）和 States（形容词）。

## Review Comments

- [x] Implemented CLI changes for default branching.
- [x] Created monoco-flow skill.
- [x] Updated issue skill policies.
- [x] Verified with unit tests.
