---
id: FIX-0018
uid: dd1095
type: fix
status: closed
stage: done
title: 修复 issue close 命令在文件重命名或删除时失败的问题
created_at: '2026-02-06T10:29:02'
updated_at: 2026-02-06 10:30:19
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0018'
files:
- src/monoco/core/git.py
- src/monoco/features/issue/core.py
criticality: high
solution: implemented
opened_at: '2026-02-06T10:29:02'
closed_at: '2026-02-06T10:30:19'
---

## FIX-0018: 修复 issue close 命令在文件重命名或删除时失败的问题

## FIX-0018: 修复 issue close 命令在文件重命名或删除时失败的问题

## Objective

修复 `monoco issue close` 命令在处理文件重命名或删除时的异常行为。目前该命令通过检出 `files` 列表中的文件进行原子合并，如果列表中包含已删除或重命名的旧路径，`git checkout` 会报错导致流程中断。

## Acceptance Criteria

- [x] `merge_issue_changes` 能够识别分支中已删除的文件并执行 `git rm`。
- [x] `merge_issue_changes` 在执行 `git checkout` 前会校验文件是否存在于目标分支，避免无效路径报错。
- [x] 重命名操作现在可以在 `close` 时被正确同步（原路径删除，新路径检出）。

## Technical Tasks

- [x] **增强 Git 核心工具**:
  - [x] 在 `monoco.core.git` 中添加 `file_exists_in_ref` 检查工具。
  - [x] 在 `monoco.core.git` 中添加 `git_rm` 封装工具。
- [x] **重构合并逻辑**:
  - [x] 优化 `monoco.features.issue.core.merge_issue_changes` 函数。
  - [x] 实现基于存在性检查的条件检出。
  - [x] 实现针对被删文件的同步删除动作。

## Review Comments

- 2026-02-06: 修复了文件重命名/删除导致原子合并中断的缺陷。
