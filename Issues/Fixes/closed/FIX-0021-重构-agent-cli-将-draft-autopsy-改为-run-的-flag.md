---
id: FIX-0021
uid: c5a7b6
type: fix
status: closed
stage: done
title: 重构 agent CLI：将 draft、autopsy 改为 run 的 flag
created_at: '2026-01-30T08:46:34'
updated_at: '2026-01-30T08:47:55'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0021'
files: []
opened_at: '2026-01-30T08:46:34'
closed_at: '2026-01-30T08:47:55'
solution: implemented
isolation:
  type: branch
  ref: feat/fix-0021-重构-agent-cli-将-draft-autopsy-改为-run-的-flag
  created_at: '2026-01-30T08:46:36'
---

## FIX-0021: 重构 agent CLI：将 draft、autopsy 改为 run 的 flag

## Objective
当前 `monoco agent` 的 API 设计不合理，`draft` 和 `autopsy` 作为独立命令过于分散，应该作为 `run` 命令的 flag 来提供更一致的用户体验。

## Acceptance Criteria
- [x] `draft` 改为 `run --draft --desc "..."` 形式
- [x] `autopsy` 改为 `run --autopsy <ID>` 形式
- [x] 保持 `kill`, `list`, `logs` 作为独立管理命令
- [x] 更新错误提示信息使用新的 flag 语法

## Technical Tasks
- [x] 移除 `draft` 命令定义，改为内部函数 `_run_draft()`
- [x] 移除 `autopsy` 命令定义，改为内部函数 `_run_autopsy()`
- [x] 在 `run` 命令添加 `--draft`, `--desc`, `--autopsy` flags
- [x] 更新帮助文档和错误信息

## Review Comments
API 更简洁，符合 CLI 设计惯例。
