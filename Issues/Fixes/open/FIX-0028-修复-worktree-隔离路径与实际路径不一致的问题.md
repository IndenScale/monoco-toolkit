---
id: FIX-0028
uid: d37f98
type: fix
status: open
stage: review
title: 修复 worktree 隔离路径与实际路径不一致的问题
created_at: '2026-02-20T22:37:16'
updated_at: '2026-02-20T22:50:36'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0028'
files:
- src/monoco/features/issue/core.py
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-20T22:37:16'
---

## FIX-0028: 修复 worktree 隔离路径与实际路径不一致的问题

## Objective
修复 `monoco issue start` 创建的 worktree 中，`isolation.path` 记录的路径与实际 worktree 物理路径不一致的问题。

## Acceptance Criteria
- [x] 识别问题根因（macOS iCloud Firmlink 机制）
- [x] 修复代码从 git 获取实际 worktree 路径
- [x] 修复后 `isolation.path` 与实际路径一致

## Technical Tasks
- [x] 调查 worktree 路径不一致的根本原因
- [x] 使用 `git worktree list --porcelain` 获取实际路径
- [x] 更新 `start_issue_isolation` 函数使用实际路径
- [x] 提交修复并验证

## Review Comments
### 问题根因
macOS 开启 iCloud Drive 桌面与文稿文件夹同步后，`~/Documents` 实际物理路径变为 `~/Library/Mobile Documents/com~apple~CloudDocs/Documents/`。系统在原位置留下 Firmlink（类似软链接但由系统特殊处理）。

当执行 `git worktree add .monoco/worktrees/xxx` 时：
1. Git canonicalize 路径，跟随 Firmlink 找到物理路径
2. Git 在物理路径创建 worktree
3. 但代码记录的仍是逻辑路径 `.monoco/worktrees/xxx`

### 修复方案
创建 worktree 后，调用 `git.get_worktrees()` 获取实际路径，使用实际路径更新 `isolation_meta`。

修复代码：
```python
# FIX-0028: Get actual worktree path from git (handles macOS iCloud Firmlink)
actual_wt_path = wt_path
try:
    worktrees = git.get_worktrees(project_root)
    for wt_info in worktrees:
        wt_disk_path, _, wt_branch = wt_info
        if wt_branch and branch_name in wt_branch:
            actual_wt_path = Path(wt_disk_path)
            break
except Exception:
    pass
```
