---
id: FEAT-0201
uid: a078e4
type: feature
status: open
stage: draft
title: 默认使用 worktree 隔离，保留 branch 作为可选 flag
created_at: '2026-02-16T15:49:56'
updated_at: '2026-02-16T15:49:56'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0201'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-16T15:49:56'
---

## FEAT-0201: 默认使用 worktree 隔离，保留 branch 作为可选 flag

## Objective
将 `monoco issue start` 的默认隔离模式从 branch 改为 worktree，以支持多 Agent 并发开发的安全隔离，同时保留 `--branch` flag 供简单场景使用。

## Acceptance Criteria
- [ ] `monoco issue start <id>` 默认创建 worktree（而非 branch）
- [ ] `--branch` flag 可以显式切换回 branch 模式
- [ ] `--direct` flag 保持现状（直接在当前分支工作）
- [ ] worktree 创建在 `.monoco/worktrees/<issue-id>/` 目录下
- [ ] 更新后的行为在 AGENTS.md 中有清晰文档
- [ ] 向后兼容：已有 branch 模式的 Issue 可以正常关闭和清理

## Technical Tasks

- [ ] 修改 `src/monoco/features/issue/commands.py` 中的 `start` 命令
  - [ ] 将 `branch` 默认从 `True` 改为 `False`
  - [ ] 将 `worktree` 默认从 `False` 改为 `True`
  - [ ] 调整互斥逻辑：`--branch` 和 `--worktree` 仍然互斥
- [ ] 测试 worktree 自动端口分配（如需要）
- [ ] 更新 AGENTS.md 文档，说明新的默认行为
- [ ] 更新 `--help` 文本，清晰描述 flag 行为

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
