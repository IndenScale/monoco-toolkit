---
id: FEAT-0163
uid: ee3e62
type: feature
status: open
stage: doing
title: 在 issue submit 运行过程中自动执行 sync-files
created_at: '2026-02-03T11:13:37'
updated_at: 2026-02-03 11:13:39
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0163'
files: []
criticality: medium
solution: null
opened_at: '2026-02-03T11:13:37'
isolation:
  type: branch
  ref: feat/feat-0163-在-issue-submit-运行过程中自动执行-sync-files
  path: null
  created_at: '2026-02-03T11:13:39'
---

## FEAT-0163: 在 issue submit 运行过程中自动执行 sync-files

## Objective
在执行 `monoco issue submit` 时自动运行 `sync-files` 逻辑，以确保交付物的文件清单始终是最新的，防止后续原子合并因清单缺失或陈旧而失败。同时保留独立的 `monoco issue sync-files` 命令供手动使用。

## Acceptance Criteria
- [ ] 执行 `monoco issue submit` 时，自动计算当前分支与 Trunk 的文件差异并更新 Ticket。
- [ ] 即使开发者忘记手动运行 `sync-files`，在提交评审时 Ticket 的 `files` 字段也应是正确的。
- [ ] 原有的独立 `monoco issue sync-files` 命令功能保持不变。

## Technical Tasks
- [ ] 调研 `monoco/features/issue/commands.py` 中 `submit` 命令的实现。
- [ ] 在 `submit` 函数逻辑中插入对 `core.sync_issue_files` 或相应逻辑的调用。
- [ ] 添加回归测试或手动验证。

## Review Comments
