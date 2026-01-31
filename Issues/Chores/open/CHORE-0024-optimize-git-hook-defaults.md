---
id: CHORE-0024
uid: 8ad649
type: chore
status: open
stage: review
title: Optimize Git Hook Defaults
created_at: '2026-01-31T10:29:47'
updated_at: '2026-01-31T10:50:51'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0024'
- '#EPIC-0000'
files: []
criticality: low
opened_at: '2026-01-31T10:29:47'
isolation:
  type: branch
  ref: feat/chore-0024-optimize-git-hook-defaults
  created_at: '2026-01-31T10:30:05'
---

## CHORE-0024: Optimize Git Hook Defaults

## Objective
优化 Git Hook 的默认行为配置，采用“保守默认”策略以提高安全性。
1. 将 `GitCleanupHook` 的 `auto_delete_merged_branches` 默认值设为 `False`，防止意外删除分支。
2. 在 `workspace.yaml` 中显式启用 `git_cleanup` Hook，并设置 `auto_switch_to_main: true`。

## Acceptance Criteria
- [x] `GitCleanupHook` 在未提供配置时，`auto_delete_merged_branches` 默认为 `False`。
- [x] `.monoco/workspace.yaml` 包含 `session_hooks` 配置段。
- [x] 验证 Hook 可以在 Session 结束时正确触发。

## Technical Tasks
- [x] 修改 `monoco/core/hooks/builtin/git_cleanup.py`，更新默认参数。
- [x] 更新 `.monoco/workspace.yaml`，添加 `session_hooks` 配置。

## Review Comments
- Validated default value is False in code.
- Verified workspace.yaml configuration.
