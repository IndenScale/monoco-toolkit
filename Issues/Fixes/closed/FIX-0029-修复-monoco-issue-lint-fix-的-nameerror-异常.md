---
id: FIX-0029
uid: e3b51d
type: fix
status: closed
stage: done
title: 修复 monoco issue lint --fix 的 NameError 异常
created_at: '2026-02-20T22:37:20'
updated_at: '2026-02-20T22:39:58'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0029'
files:
- src/monoco/features/issue/linter.py
criticality: high
solution: implemented
opened_at: '2026-02-20T22:37:20'
closed_at: '2026-02-20T22:39:58'
---

## FIX-0029: 修复 monoco issue lint --fix 的 NameError 异常

## Objective
修复 `monoco issue lint --fix` 命令执行时出现的 `NameError: name 'all_issue_ids' is not defined` 异常。

## Acceptance Criteria
- [x] `monoco issue lint --fix <file>` 不再抛出 NameError
- [x] 修复后 lint --fix 功能正常工作
- [x] 单元测试通过

## Technical Tasks
- [x] 定位 `run_lint` 函数中 `all_issue_ids` 变量未定义的问题
- [x] 在 fix 验证代码块前添加变量存在性检查
- [x] 如变量不存在，重新扫描工作区获取 issue IDs 和 domains
- [x] 提交修复并验证

## Review Comments
问题根因：`run_lint` 函数在 `fix=True` 时会重新运行验证，但此时 `all_issue_ids` 和 `valid_domains` 变量可能未定义（它们只在 `file_paths` 为真值时的 if 块内定义）。

修复方案：在 fix 验证代码块前使用 try/except 检查变量是否存在，如不存在则重新扫描工作区获取。
