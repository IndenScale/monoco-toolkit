---
id: FEAT-0111
uid: d2df83
type: feature
status: closed
stage: done
title: Add force-prune option for issue close command
created_at: '2026-01-29T18:41:05'
updated_at: 2026-01-30 08:23:11
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0111'
files:
- monoco/features/issue/commands.py
- tests/features/issue/test_prune.py
opened_at: '2026-01-29T18:41:05'
closed_at: '2026-01-30T08:23:10'
solution: implemented
---

## FEAT-0111: Add force-prune option for issue close command

## 目标

使用 squash merge 工作流时，Git 无法自动检测到功能分支已合并到 main。这会导致 `monoco issue close` 在尝试修剪分支时失败，因为 Git 的安全检查会阻止删除"未合并"的分支。

我们需要一个 `--force-prune` 选项，允许用户覆盖 Git 的合并检测，在确认 issue 确实已关闭后强制删除分支。

## 验收标准

- [x] `monoco issue close <id> --force-prune` 成功删除 squash-merged 分支
- [x] 命令在强制删除前显示明确的警告
- [x] 不使用 `--force-prune` 时，行为保持不变（安全默认）
- [x] 文档已更新，解释何时使用此选项

## 技术任务

- [x] 为 `issue close` 命令添加 `--force-prune` 标志
- [x] 使用 `git branch -D` 而非 `git branch -d` 实现强制删除逻辑
- [x] 添加确认提示，警告用户关于强制删除的风险
- [x] 更新命令帮助文本和文档
- [x] 为 squash-merge 场景添加测试用例

## Review Comments
Verified.

### Self Review
- Implemented `--force-prune` option in `commands.py`.
- Added interactive confirmation prompt using `typer.confirm`.
- Added logic to bypass confirmation in Agent mode (`--json`) or if `--force` is also provided (though `--force-prune` implies force).
- Verified implementation with `tests/features/issue/test_prune.py` covering both interactive and JSON modes.
- Ensured existing `prune_issue_resources` logic (using `force=True`) is correctly leveraged.
