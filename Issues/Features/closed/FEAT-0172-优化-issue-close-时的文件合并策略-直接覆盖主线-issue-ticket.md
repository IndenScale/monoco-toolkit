---
id: FEAT-0172
uid: 9fb8f8
type: feature
status: closed
stage: done
title: 优化 issue close 时的文件合并策略：直接覆盖主线 issue ticket
created_at: '2026-02-04T11:17:02'
updated_at: 2026-02-04 13:48:51
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0172'
files:
- monoco/features/issue/commands.py
- monoco/features/issue/core.py
- tests/features/issue/test_close_multi_branch.py
criticality: medium
solution: implemented
opened_at: '2026-02-04T11:17:02'
closed_at: '2026-02-04T13:48:51'
---

## FEAT-0172: 优化 issue close 时的文件合并策略：直接覆盖主线 issue ticket

## Objective
<!-- Describe the "Why" and "What" clearly. Focus on value. -->

当前 `monoco issue close` 在执行 Smart Atomic Merge 时，会将 Issue ticket 文件（如 `Issues/Features/open/FEAT-XXX.md`）也纳入冲突检测范围。这导致以下问题：

1. 如果主线和 feature branch 都修改了 Issue 文件（例如都更新了 checkbox 状态），合并会被阻止
2. Issue 文件本质上是工作流元数据，应该以 feature branch 的版本为准（包含最新的开发状态、评论等）
3. 主线的 Issue 文件通常是过时的初始状态

本功能要求修改合并策略：**Issue ticket 文件在 close 时直接以 feature branch 版本覆盖主线版本，不进行冲突检查**。

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [x] `sync_files` 不再将 Issue 文件本身加入 `files` 列表
- [x] `merge_issue_changes` 在冲突检测时排除 Issue 文件
- [x] `merge_issue_changes` 使用 `git checkout` 合并文件时跳过 Issue 文件
- [x] Issue 文件由 `update_issue` 统一处理（移动目录 + 状态更新）
- [x] 测试验证主线和 feature branch 都有 Issue 修改时能正常 close

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->
<!-- - [ ] Parent Task -->
<!--   - [ ] Sub Task -->

- [x] 修改 `core.py::sync_issue_files`：从 changed_files 中排除 Issue 文件本身
- [x] 修改 `core.py::merge_issue_changes`：从 files_to_merge 中排除 Issue 文件
- [x] 验证 `update_issue` 正确处理 Issue 文件的目录移动和状态更新
- [x] 运行测试验证场景：主线和 feature branch 都有 Issue 修改时能正常 close

## Review Comments

### 实现总结

**问题**: 当主线和 feature branch 都修改了 Issue ticket 文件时，`monoco issue close` 会因冲突检测而失败。

**解决方案**: Issue 文件作为工作流元数据，在 close 时直接以 feature branch 版本为准，不做冲突检查。

**修改位置** (`monoco/features/issue/core.py`):

1. **sync_issue_files** (line ~1381): 从 `changed_files` 中过滤掉 Issue 文件本身，确保 `files` 字段不包含 Issue 文件

2. **merge_issue_changes** (line ~1478):
   - 创建新的 `files_to_merge` 列表，排除 Issue 文件
   - 只对 `files_to_merge` 进行冲突检测
   - 只对 `files_to_merge` 执行 `git_checkout_files`

**验证**: Issue 文件由 `update_issue` 函数单独处理（负责移动目录 `open/` → `closed/` 和更新状态），无需通过 git merge 合并。
