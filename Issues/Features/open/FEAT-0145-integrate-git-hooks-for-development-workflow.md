---
id: FEAT-0145
uid: 6d6bf7
type: feature
status: open
stage: draft
title: Integrate Git Hooks for Development Workflow
created_at: '2026-02-01T20:57:03'
updated_at: '2026-02-01T20:57:03'
parent: EPIC-0030
dependencies: []
related:
- FEAT-0141
domains: []
tags:
- '#EPIC-0030'
- '#FEAT-0145'
- '#FEAT-0141'
files: []
criticality: medium
opened_at: '2026-02-01T20:57:03'
---

## FEAT-0145: Integrate Git Hooks for Development Workflow

## 背景与目标

将 Git Hooks 集成到 Monoco 工作流中，确保开发规范在提交阶段被强制执行。当前缺少必要字段（如关闭 Issue 的 `solution` 字段）的问题可能破坏索引器或依赖关系，手动修复容易出错。通过 `pre-commit` 钩子运行 `monoco issue lint` 可以在提交前拦截不合规的更改，`pre-push` 钩子可检查关键 Issue 状态（可选配置）。本功能需要创建钩子模板、实现安装逻辑，并确保与现有 Monoco 命令的集成。

## Objective
Integrate Git Hooks (pre-commit, pre-push) into the Monoco workflow to ensure data integrity and process compliance.

**Context**:
- **Problem**: Issues with missing required fields (e.g., `solution` for closed issues) can break the indexer or dependencies. Manual fixes are error-prone.
- **Solution**: Use `pre-commit` to run `monoco issue lint` and prevent non-compliant commits.

## Acceptance Criteria
- [ ] `monoco sync` (or similar command) installs/updates git hooks.
- [ ] `pre-commit` hook runs `monoco issue lint` and blocks commit on failure.
- [ ] `pre-push` hook checks for uncompleted critical issues (optional/configurable).

## Technical Tasks
- [ ] Create hook templates in `monoco/assets/hooks`.
- [ ] Extend `monoco sync` to install hooks into `.git/hooks`.
- [ ] Implement the `pre-commit` logic (calling the linter).
- [ ] 设计 Hooks 模板存放目录 (`monoco/core/githooks/templates/`)
- [ ] 实现 `pre-push` hook：检查关键 Issue 状态（可选配置）
- [ ] 实现 `post-checkout` hook：自动同步 Issue 状态（可选）
- [ ] 支持 Hooks 模板自定义

## Review Comments

### 2026-02-02 整合更新

**变更**:
- Parent 从 EPIC-0025 调整为 EPIC-0030 (DevEx & Infrastructure)
- 整合了 FEAT-0141 的技术任务（模板目录、pre-push/post-checkout hooks）
- FEAT-0141 已标记为 duplicate 并关闭

**归属理由**: Git Hooks 属于开发者体验基础设施，与 EPIC-0030 的 "Code Quality Infrastructure" 和 "Local Development Environment" 目标一致。