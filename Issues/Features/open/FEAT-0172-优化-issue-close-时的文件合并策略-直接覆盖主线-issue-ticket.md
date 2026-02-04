---
id: FEAT-0172
uid: 9fb8f8
type: feature
status: open
stage: doing
title: 优化 issue close 时的文件合并策略：直接覆盖主线 issue ticket
created_at: '2026-02-04T11:17:02'
updated_at: '2026-02-04T11:17:27'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0172'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T11:17:02'
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
- [ ] `sync_files` 不再将 Issue 文件本身加入 `files` 列表
- [ ] `merge_issue_changes` 在冲突检测时排除 Issue 文件
- [ ] `merge_issue_changes` 使用 `git checkout` 合并文件时跳过 Issue 文件
- [ ] Issue 文件由 `update_issue` 统一处理（移动目录 + 状态更新）
- [ ] 测试验证主线和 feature branch 都有 Issue 修改时能正常 close

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

<!-- Status Syntax: -->
<!-- [ ] To Do -->
<!-- [/] Doing -->
<!-- [x] Done -->
<!-- [~] Cancelled -->
<!-- - [ ] Parent Task -->
<!--   - [ ] Sub Task -->

- [ ] 修改 `core.py::sync_issue_files`：从 changed_files 中排除 Issue 文件本身
- [ ] 修改 `core.py::merge_issue_changes`：从 files_to_merge 中排除 Issue 文件
- [ ] 验证 `update_issue` 正确处理 Issue 文件的目录移动和状态更新
- [ ] 运行测试验证场景：主线和 feature branch 都有 Issue 修改时能正常 close

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
