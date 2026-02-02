---
id: FIX-0006
uid: 30a4fe
type: fix
status: open
stage: review
title: monoco issue close 读取错误分支的 Issue 状态
created_at: '2026-02-02T20:47:02'
updated_at: '2026-02-02T21:03:29'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0006'
files:
- monoco/features/issue/core.py
- monoco/features/issue/commands.py
- tests/features/issue/test_cross_branch_search.py
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-02T20:47:02'
isolation:
  type: branch
  ref: feat/fix-0006-monoco-issue-close-读取错误分支的-issue-状态
  created_at: '2026-02-02T20:51:02'
---

## FIX-0006: monoco issue close 读取错误分支的 Issue 状态

## Objective

### 问题描述
`monoco issue close` 命令在执行时，检查的是当前 `main` 分支上的 Issue 文件状态，而不是 feature branch 上的实际状态。这导致以下问题：

1. **工作流断裂**：在 feature branch 上完成工作后，回到 main 分支执行 `close` 时，由于 main 分支的 Issue 文件仍是旧状态（open/draft），无法正确执行 close 操作
2. **自动化受阻**：影响了自动 cherry-pick 工作流的价值，因为 cherry-pick 后需要在 main 分支上手动修改 Issue 状态

### 预期行为
`monoco issue close` 应该实现极简智能匹配：
- **自动搜索**：根据 issue 编号在所有本地分支中自动查找对应的 Issue 文件
- **Golden Path**：只找到一个匹配时，静默使用，不给用户任何选择负担
- **冲突即报错**：当多个分支存在同名 Issue 时，直接报错退出，提示用户先解决冲突（如合并分支或删除重复）
- **未找到**：当所有分支都找不到该 Issue 时，给出清晰错误提示

### 影响范围
- 所有使用 `monoco issue start --branch` 创建 feature branch 的工作流
- 依赖自动 cherry-pick 的 CI/CD 流程

## Acceptance Criteria
- [ ] `monoco issue close` 自动在所有本地分支中搜索指定 issue 编号
- [ ] 只找到一个匹配时，静默执行，无需用户干预
- [ ] 当多个分支存在同名 Issue 时，直接报错退出（不交互）
- [ ] 当所有分支都找不到该 Issue 时，给出清晰错误提示
- [ ] 修复后 cherry-pick 工作流可以正常闭环

## Technical Tasks

### 调研阶段
- [x] 定位 `monoco issue close` 命令的实现代码
- [x] 分析当前 Issue 状态读取逻辑（确定硬编码 main 分支的位置）
- [x] 调研 Git 分支切换和文件读取的最佳实践

### 实现阶段
- [x] 实现跨分支 Issue 搜索逻辑（使用 `git ls-tree` 遍历分支）
- [x] 实现简单匹配计数逻辑：0个=报错，1个=使用，多个=报错
- [x] 错误信息设计：多分支冲突时提示用户合并分支或删除重复 Issue
- [x] 更新相关帮助文档

### 验证阶段
- [x] 编写单元测试覆盖多分支场景 (13 tests added)
- [~] 手动测试 feature branch -> main 的完整工作流 (deferred to integration testing)
- [~] 验证 cherry-pick 后 close 命令正常工作 (deferred to integration testing)

## Review Comments

### Implementation Summary

Implemented cross-branch issue search for `monoco issue close` command.

**Key Design Decisions:**
1. **Golden Path Simplicity**: No user interaction required for the common case
2. **Fail Fast on Conflict**: Multiple branch matches result in immediate error
3. **Git-native Approach**: Uses `git ls-tree` to search without checking out branches

**Code Changes:**
- `core.py`: Added 3 new functions (~200 lines)
  - `find_issue_path_across_branches()`: Main entry point
  - `_find_branches_with_file()`: Helper to check file existence across branches
  - `_search_issue_in_branches()`: Deep search when file not in working tree
- `commands.py`: Modified `close` command to use new search logic
- `test_cross_branch_search.py`: 13 comprehensive unit tests

**Test Coverage:**
- Local file found (no git)
- Local file in git repo (golden path)
- Local file conflict (multiple branches)
- Cross-branch search (file only in other branch)
- Not found anywhere
- Workspace issue handling
- Invalid issue ID handling

**Manual Testing Notes:**
Deferred to integration testing phase due to complex git state requirements.
