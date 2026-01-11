---
id: FEAT-0013
type: feature
status: closed
stage: done
title: 实现 monoco issue list 命令
created_at: '2026-01-11T11:07:44.936747'
opened_at: '2026-01-11T11:07:54.651842'
updated_at: '2026-01-11T11:10:42.635925'
closed_at: '2026-01-11T11:10:42.635955'
solution: implemented
dependencies: []
related: []
tags:
- cli
- ux
---

## FEAT-0013: 实现 monoco issue list 命令

## Objective

实现一个强大的 `list` 命令，允许用户以表格形式查看和筛选 Issue，弥补 `scope` (树状视图) 在平铺展示和多维筛选方面的不足。

## Acceptance Criteria

1. **Command**: `monoco issue list` 可用。
2. **默认视图**: 显示所有状态为 `OPEN` 的 Issue。
3. **筛选支持**:
   - `--status`: 支持筛选 open, backlog, closed (或 all)。
   - `--type`: 支持筛选 feature, fix, chore, epic。
   - `--stage`: 支持筛选 todo, doing, review, done。
4. **展示形式**: 使用 rich table 展示 ID, Type, Status, Stage, Title, UpdatedAt。
5. **Workspace Support**: 复用 FEAT-0012 的工作区感知能力 (`--root`)。

## Technical Tasks

- [x] Implementing `list` command in `monoco/features/issue/commands.py`.
- [x] Add filtering logic to `list_issues` or post-process in command.
- [x] Update documentation.
