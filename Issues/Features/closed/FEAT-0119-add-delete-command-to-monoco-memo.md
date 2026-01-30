---
id: FEAT-0119
uid: 7959b6
type: feature
status: closed
stage: done
title: Add delete command to monoco memo
created_at: '2026-01-30T15:16:04'
updated_at: '2026-01-30T15:20:35'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0119'
files: []
criticality: medium
opened_at: '2026-01-30T15:16:04'
closed_at: '2026-01-30T15:20:35'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0119-add-delete-command-to-monoco-memo
  created_at: '2026-01-30T15:18:03'
---

## FEAT-0119: Add delete command to monoco memo

## Objective
为 `monoco memo` 模块添加删除功能，允许用户通过 ID 删除不再需要的备忘录条目，以便更好地管理 Inbox。

## Acceptance Criteria
- [x] 支持命令 `monoco memo delete <ID>`。
- [x] 执行后从 `Memos/inbox.md` 中物理移除对应 ID 的条目。
- [x] 如果 ID 不存在，显示友好的错误提示。
- [x] 删除成功后显示确认信息。

## Technical Tasks
- [x] 在 `monoco/features/memo/core.py` 中实现 `delete_memo(issues_root, memo_id)` 函数。
  - [x] 解析 `inbox.md` 内容。
  - [x] 过滤掉目标 ID 的 Memo。
  - [x] 重写文件内容。
- [x] 在 `monoco/features/memo/cli.py` 中添加 `delete` 子命令。
  - [x] 接收 `id` 参数。
  - [x] 调用核心逻辑并处理结果反馈。

## Review Comments
- All technical tasks completed.
- Unit tests added and verified.
- Manual verification passed.