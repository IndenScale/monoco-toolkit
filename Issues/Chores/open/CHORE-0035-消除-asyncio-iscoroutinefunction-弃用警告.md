---
id: CHORE-0035
uid: dc8c24
type: chore
status: open
stage: review
title: 消除 asyncio.iscoroutinefunction 弃用警告
created_at: '2026-02-03T10:41:01'
updated_at: '2026-02-03T10:50:20'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0035'
- '#EPIC-0000'
files: []
criticality: low
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T10:41:01'
---

## CHORE-0035: 消除 asyncio.iscoroutinefunction 弃用警告

## Objective
替换代码中已弃用的 `asyncio.iscoroutinefunction` 为 `inspect.iscoroutinefunction`，以支持更高版本的 Python 并清理 pytest 警告。

## Acceptance Criteria
- [x] 所有 `asyncio.iscoroutinefunction` 的调用均已替换为 `inspect.iscoroutinefunction`。
- [x] 运行 `pytest` 不再出现相关的 `DeprecationWarning`。
- [x] 现有测试全部通过。

## Technical Tasks
- [x] 全局搜索 `asyncio.iscoroutinefunction` 的使用点。
- [x] 在相关文件中引入 `inspect` 模块（如果尚未引入）。
- [x] 执行替换并验证。
- [x] 运行性能回归或单元测试确保逻辑未变。

## Review Comments
所有 `asyncio.iscoroutinefunction` 已成功替换为 `inspect.iscoroutinefunction`。经过验证，`pytest` 运行正常且不再报相关弃用警告。
