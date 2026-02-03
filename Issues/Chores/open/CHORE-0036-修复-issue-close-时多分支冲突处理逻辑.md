---
id: CHORE-0036
uid: 11b40a
type: chore
status: open
stage: doing
title: 修复 issue close 时多分支冲突处理逻辑
created_at: '2026-02-03T13:43:22'
updated_at: '2026-02-03T13:46:26'
parent: EPIC-0000
dependencies: []
related:
- FIX-0009
domains: []
tags:
- '#EPIC-0000'
- '#CHORE-0036'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T13:43:22'
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
- [ ] `monoco issue close` 在多分支冲突时，用 feature 分支版本覆盖 main
- [ ] 正确处理中文/特殊字符文件路径
- [ ] 简化合并逻辑，移除不必要的 selective checkout

## Technical Tasks

- [ ] 修改 `monoco issue close` 命令的冲突处理逻辑
- [ ] 当检测到多分支时，直接使用 feature 分支版本覆盖
- [ ] 删除 main 分支的旧 Issue 文件
- [ ] 测试中文文件名的处理

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
