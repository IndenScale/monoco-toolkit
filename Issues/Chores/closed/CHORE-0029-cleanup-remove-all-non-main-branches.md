---
id: CHORE-0029
uid: e11f5f
type: chore
status: closed
stage: done
title: 'Cleanup: Remove all non-main branches'
created_at: '2026-02-01T22:56:30'
updated_at: '2026-02-01T22:58:13'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0029'
- '#EPIC-0000'
files: []
criticality: low
opened_at: '2026-02-01T22:56:30'
closed_at: '2026-02-01T22:58:13'
solution: implemented
isolation:
  type: branch
  ref: feat/chore-0029-cleanup-remove-all-non-main-branches
  created_at: '2026-02-01T22:56:47'
---

## CHORE-0029: Cleanup: Remove all non-main branches

## Objective
清理所有非 `main` 的分支，保持仓库整洁。

## Acceptance Criteria
- [x] 所有非 `main` 的本地分支均已被删除。
- [x] 当前分支保持在 `main`。

## Technical Tasks
- [x] 列出并确认待删除的分支。
- [x] 强制删除所有非 `main` 的本地分支。

## Review Comments
- 已成功删除除 `main` 和当前工作分支外的所有本地分支。
