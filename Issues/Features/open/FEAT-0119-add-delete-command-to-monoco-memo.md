---
id: FEAT-0119
uid: 7959b6
type: feature
status: open
stage: doing
title: Add delete command to monoco memo
created_at: '2026-01-30T15:16:04'
updated_at: '2026-01-30T15:18:02'
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
---

## FEAT-0119: Add delete command to monoco memo

## Objective
为 `monoco memo` 模块添加删除功能，允许用户通过 ID 删除不再需要的备忘录条目，以便更好地管理 Inbox。

## Acceptance Criteria
- [ ] 支持命令 `monoco memo delete <ID>`。
- [ ] 执行后从 `Memos/inbox.md` 中物理移除对应 ID 的条目。
- [ ] 如果 ID 不存在，显示友好的错误提示。
- [ ] 删除成功后显示确认信息。

## Technical Tasks
- [ ] 在 `monoco/features/memo/core.py` 中实现 `delete_memo(issues_root, memo_id)` 函数。
  - [ ] 解析 `inbox.md` 内容。
  - [ ] 过滤掉目标 ID 的 Memo。
  - [ ] 重写文件内容。
- [ ] 在 `monoco/features/memo/cli.py` 中添加 `delete` 子命令。
  - [ ] 接收 `id` 参数。
  - [ ] 调用核心逻辑并处理结果反馈。

## Review Comments