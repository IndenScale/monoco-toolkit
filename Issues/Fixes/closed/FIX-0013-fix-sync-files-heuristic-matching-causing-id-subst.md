---
id: FIX-0013
uid: c95460
type: fix
status: closed
stage: done
title: Fix sync-files heuristic matching causing ID substring collision
created_at: '2026-02-04T12:17:27'
updated_at: '2026-02-04T12:21:58'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0013'
files:
- monoco/features/issue/core.py
- tests/features/issue/test_branch_id_matching.py
criticality: high
solution: cancelled
opened_at: '2026-02-04T12:17:27'
closed_at: '2026-02-04T12:21:58'
---

## FIX-0013: Fix sync-files heuristic matching causing ID substring collision

## Objective
<!-- Describe the "Why" and "What" clearly. Focus on value. -->

当前 `sync_issue_files()` 函数中的启发式匹配使用子串匹配：
```python
if issue_id.lower() in current.lower():
    target_ref = current
```

这导致 `FEAT-1` 会错误匹配到 `feat/feat-123-login` 分支，造成交叉污染。

需要改为严格的 ID 匹配：只匹配分支名中的 ID 部分，且必须完全相等。

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [x] 将启发式匹配改为严格的 ID 边界匹配
- [x] 支持分支格式 `feat/<id>-slug` 和 `feat/<id>`
- [x] 添加测试用例验证边界情况

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

- [x] 修改 `sync_issue_files()` 中的分支匹配逻辑
- [x] 添加辅助函数 `_extract_issue_id_from_branch()` 用于提取分支中的 ID
- [x] 使用正则表达式确保精确匹配
- [x] 更新单元测试

## Solution

修复启发式匹配使用子串匹配的问题：
- 原代码：`if issue_id.lower() in current.lower()` 导致 `FEAT-1` 匹配 `feat/feat-123-login`
- 新代码：使用正则表达式提取分支名中的 ID 部分，进行精确相等匹配
- 新增 `_extract_issue_id_from_branch()` 函数支持多种分支格式（feat/fix/chore/epic）

## Review Comments

- 测试覆盖 34 个用例，包括边界情况
- 关键安全测试：`FEAT-1` 不会错误匹配 `feat/feat-123-*` 分支
