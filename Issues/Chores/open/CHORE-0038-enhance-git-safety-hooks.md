---
id: CHORE-0038
uid: 9a3c4d
type: chore
status: open
stage: draft
title: Enhance Git Safety Hooks
created_at: '2026-02-03T20:51:00'
updated_at: '2026-02-03T20:51:00'
parent: EPIC-0000
dependencies: []
related: []
domains:
- DevEx
- Git
tags:
- '#CHORE-0038'
- '#EPIC-0000'
files:
- .git/hooks/
- scripts/
criticality: medium
solution: null
opened_at: '2026-02-03T20:51:00'
---

## CHORE-0038: Enhance Git Safety Hooks

## Objective
增强 Git Hooks 机制，严格防止在 `main` 或 `master` 分支上直接进行 Commit 操作。近期发生的跨分支 Commit 污染事件表明，仅靠人为规范不足以保证分支隔离，需要强制的技术手段来维护主干的整洁。

## Acceptance Criteria
- [ ] **Pre-commit Hook**: 在 `main`/`master` 分支尝试 commit 时，自动拦截并报错，提示需切换分支。
- [ ] **Pre-checkout Hook** (Optional): 切换分支前检查当前工作区是否有未提交变更，防止携带变更污染目标分支。
- [ ] **Bypass Support**: 允许通过特定标志（如环境变量）在紧急情况下绕过检查（仅限管理员）。

## Technical Tasks
- [ ] 编写或更新 `.git/hooks/pre-commit` 脚本。
- [ ] 实现分支名称检测逻辑 (Current Branch vs Protected Branches)。
- [ ] 集成到 `monoco init` 或 `setup` 流程中，确保开发者环境自动安装这些 Hooks。
- [ ] 文档更新：说明受保护分支策略及 Hooks 机制。

## Review Comments