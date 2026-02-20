---
id: CHORE-0051
uid: 3b9f2d
type: chore
status: closed
stage: done
title: 测试 worktree 全流程并评估问题
created_at: '2026-02-20T22:31:08'
updated_at: '2026-02-20T22:34:04'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0051'
- '#EPIC-0000'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- test_worktree_flow.md
criticality: low
solution: implemented
opened_at: '2026-02-20T22:31:08'
closed_at: '2026-02-20T22:34:04'
isolation:
  type: worktree
  ref: CHORE-0051-测试-worktree-全流程并评估问题
  path: /Users/indenscale/Documents/Projects/Monoco/Monoco/.monoco/worktrees/chore-0051-测试-worktree-全流程并评估问题
  created_at: '2026-02-20T22:31:15'
---

## CHORE-0051: 测试 worktree 全流程并评估问题

## Objective
通过实际操作验证 monoco issue 在 worktree 场景下的完整工作流，识别潜在问题。

## Acceptance Criteria
- [x] 成功创建 worktree
- [x] 在 worktree 中执行 sync-files
- [x] 在 worktree 中执行 submit
- [x] 执行 close 清理 worktree

## Technical Tasks
- [x] 创建 CHORE issue
- [x] 启动 worktree 隔离环境
- [x] 在 worktree 中创建测试文件并提交
- [x] 执行 sync-files 同步文件列表
- [x] 执行 submit 提交审查
- [x] 执行 close 关闭 issue

## Review Comments
Worktree 全流程测试完成，发现以下问题：
1. sync-files 在 worktree 中工作正常
2. submit 需要在 worktree 中执行
