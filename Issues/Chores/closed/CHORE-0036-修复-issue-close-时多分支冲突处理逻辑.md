---
id: CHORE-0036
uid: 11b40a
type: chore
status: closed
stage: done
title: 修复 issue close 时多分支冲突处理逻辑
created_at: '2026-02-03T13:43:22'
updated_at: '2026-02-03T14:08:07'
parent: EPIC-0000
dependencies: []
related:
- FIX-0009
domains: []
tags:
- '#EPIC-0000'
- '#CHORE-0036'
files:
- monoco/features/issue/commands.py
- monoco/features/issue/core.py
- tests/features/issue/test_cross_branch_search.py
- tests/features/issue/test_close_multi_branch.py
- tests/features/issue/test_sync_files_uncommitted.py
criticality: high
solution: implemented
opened_at: '2026-02-03T13:43:22'
closed_at: '2026-02-03T14:08:07'
isolation:
  type: branch
  ref: feat/chore-0036-修复-issue-close-时多分支冲突处理逻辑
  created_at: '2026-02-03T13:46:26'
---

## CHORE-0036: 修复 issue close 时多分支冲突处理逻辑

## Objective
修复 `monoco issue close` 在处理多分支 Issue 冲突时的设计缺陷。

当前行为：当 Issue 文件在 main 和 feature 分支同时存在时，`close` 命令报错：
```
Error: Issue XXX found in multiple branches: main, feat/xxx
```

## Problem Analysis

### 当前有问题的逻辑
1. `close` 命令检测到多分支存在时，尝试选择性合并（selective checkout）
2. 使用 files 字段过滤需要合并的文件
3. 如果文件路径包含特殊字符（如中文），可能导致 git pathspec 匹配失败

### 设计原则
**Issue 文件是元数据，应该总是以 working branch 的版本为准。**

当执行 `close` 时：
1. 如果 main 和 feature 分支都有同一 Issue
2. 应该**直接删除 main 的 Issue 文件**，用 feature 分支的版本覆盖
3. 不需要复杂的选择性合并逻辑

## Acceptance Criteria
- [x] `monoco issue close` 在多分支冲突时，用 feature 分支版本覆盖 main
- [x] 正确处理中文/特殊字符文件路径
- [x] 简化合并逻辑，移除不必要的 selective checkout

## Technical Tasks

- [x] 修改 `monoco issue close` 命令的冲突处理逻辑
- [x] 当检测到多分支时，直接使用 feature 分支版本覆盖
- [x] 删除 main 分支的旧 Issue 文件
- [x] 测试中文文件名的处理
- [x] sync-files 检测未提交变更并报错

## Design Notes

### 预期行为

**当前（有问题）：**
```python
# 检测到多分支存在
if issue_exists_in_multiple_branches():
    # 尝试选择性合并 - 容易失败
    selective_checkout(files)
```

**修复后：**
```python
# 检测到多分支存在
if issue_exists_in_multiple_branches():
    # 直接删除 main 的 Issue 文件，使用 feature 分支版本
    delete_issue_from_main()
    use_feature_branch_version()
```

## Review Comments

### 设计决策

1. **多分支冲突处理**：Issue 文件作为元数据，在 `close` 时直接用 feature 分支版本覆盖 main 分支版本，避免复杂的选择性合并逻辑。

2. **Slug ID 匹配**：使用 `feat-XXXX` 这样的 slug ID 进行匹配，而不是完整分支名称，支持中文等特殊字符文件名。

3. **未提交变更检测**：`sync-files` 和 `submit` 时检测未提交变更，强制用户显式处理（提交/丢弃/忽略），保持工作目录清晰。

### 测试覆盖

- 多分支冲突处理场景
- 中文文件名处理
- 未提交变更检测（未提交、未暂存、未跟踪）

## Delivery
<!-- Monoco Auto Generated -->
**Commits (2)**:
- `8b055ed` feat(issue): CHORE-0036 改进 sync-files 检测未提交变更
- `37a733d` fix(issue): CHORE-0036 修复 issue close 时多分支冲突处理逻辑

**Touched Files (11)**:
- `"Issues/Chores/open/CHORE-0036-\344\277\256\345\244\215-issue-close-\346\227\266\345\244\232\345\210\206\346\224\257\345\206\262\347\252\201\345\244\204\347\220\206\351\200\273\350\276\221.md"`
- `"Issues/Features/open/FEAT-0165-enhance-issue-cli-and-templates-for-smoother-life\nc.md"`
- `Issues/Features/open/FEAT-0165-enhance-issue-cli-and-templates-for-smoother-lifec.md`
- `Issues/Fixes/open/FIX-0010-implement-backoff-strategy-for-daemon-scheduler-to.md`
- `Issues/Fixes/open/FIX-0011-document-memo-storage-location-in-cli-help-and-doc.md`
- `Memos/architect-trigger-issue-analysis.md`
- `monoco/features/issue/commands.py`
- `monoco/features/issue/core.py`
- `tests/features/issue/test_close_multi_branch.py`
- `tests/features/issue/test_cross_branch_search.py`
- `tests/features/issue/test_sync_files_uncommitted.py`
