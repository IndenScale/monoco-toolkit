---
id: FIX-0019
uid: bff7c3
type: fix
status: closed
stage: done
title: Fix Courier CLI ServiceError Handling
created_at: '2026-02-07T11:33:52'
updated_at: '2026-02-07T11:36:56'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0019'
files:
- .gitignore
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- src/monoco/features/courier/commands.py
criticality: high
solution: implemented
opened_at: '2026-02-07T11:33:52'
closed_at: '2026-02-07T11:36:56'
isolation:
  type: branch
  ref: FIX-0019-fix-courier-cli-serviceerror-handling
  created_at: '2026-02-07T11:34:03'
---

## FIX-0019: Fix Courier CLI ServiceError Handling

## Objective

修复 Courier CLI 命令中异常处理的 AttributeError 问题。
当前的 `stop_service` 等命令错误地尝试从 `ServiceError` 基类访问 `ServiceNotRunningError` 等子类，导致 `AttributeError`。需要改为直接导入并使用异常类。

## Acceptance Criteria

- [x] `monoco courier stop` 在服务未运行时不再抛出 `AttributeError`。
- [x] 异常捕获逻辑使用正确的异常类。

## Technical Tasks

- [x] 修复 `src/monoco/features/courier/commands.py` 中的异常导入和捕获。

## Review Comments

修复已验证。
