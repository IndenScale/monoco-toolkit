---
id: FEAT-0117
uid: 08a709
type: feature
status: closed
stage: done
title: Enforce strict branch context for issue lifecycle commands
created_at: '2026-01-30T09:20:32'
updated_at: '2026-01-30T09:25:11'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0117'
files: []
criticality: medium
opened_at: '2026-01-30T09:20:32'
closed_at: '2026-01-30T09:25:11'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0117-enforce-strict-branch-context-for-issue-lifecycle-
  created_at: '2026-01-30T09:21:57'
---

## FEAT-0117: Enforce strict branch context for issue lifecycle commands

## Objective
强制在 `monoco issue` 生命周期命令中执行分支上下文检查。防止意外的嵌套分支（分支上的分支），确保符合主干开发流程。

## Acceptance Criteria
- [x] `monoco issue create` 若不在 `main` 分支则失败。
- [x] `monoco issue start` 若不在 `main` 分支则失败（除非使用 `--no-branch` 或 `--direct`）。
- [x] `monoco issue submit` 若在 `main` 分支则失败。
- [x] `monoco issue close` 若不在 `main` 分支则失败。
- [x] 所有命令支持 `--force` 绕过检查。

## Technical Tasks
- [x] 在 `commands.py` 中实现 `_validate_branch_context` 辅助函数。
- [x] 为相关命令添加 `--force` 选项。
- [x] 将验证逻辑集成到 `create`, `start`, `submit`, `close` 中。

## Review Comments
逻辑已人工验证。
- `create`: 限制在 TRUNK。
- `start`: 限制在 TRUNK (若创建分支)。
- `submit`: 禁止在 TRUNK。
- `close`: 限制在 TRUNK。
