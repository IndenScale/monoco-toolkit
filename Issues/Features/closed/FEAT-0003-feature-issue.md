---
parent: EPIC-0001
id: FEAT-0003
type: feature
status: closed
title: "Feature: Issue Management (Local)"
created_at: 2026-01-08
solution: implemented
tags: [toolkit, feature, issue, architecture]
---

parent: EPIC-0001

## FEAT-0003: Issue Management (Local)

## Objective

实现 `monoco issue` 核心动作，专注于工单生命周期管理和结构化进度统计，不干预内容编写。

## Acceptance Criteria

1. **Create**: `monoco issue create <epic|story|task|bug> --title "..."` 自动创建文件并分配 ID。
2. **Close**: `monoco issue close {ID} --solution {type}` 将工单移动至对应类型的 `closed/` 目录，并更新状态为 `closed`。
3. **Cancel**: `monoco issue cancel {ID}` 将工单标记为 `cancelled`。
4. **Scope**: `monoco issue scope` 展示树状进度统计。
   - 支持 `--sprint {sprint-id}` 仅显示特定迭代。
   - 统计格式：`[Epic] Title (2/5 Stories Done)`。
5. **No List**: 按照要求删除通用 list 命令，通过 scope 实现概览。

## Technical Tasks

- [ ] Implement `Issue` models and directory mapping.
- [ ] Implement `monoco issue create` with auto-increment ID logic.
- [ ] Implement `monoco issue archive/cancel` with file move logic.
- [ ] Implement `monoco issue scope` with `Rich.Tree` visualization.
- [ ] Implement `--sprint` filter for scope scanning.
