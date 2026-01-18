---
parent: EPIC-0002
id: FEAT-0003
type: feature
status: closed
title: 特性: Issue 管理 (本地) (Issue Management - Local)
created_at: 2026-01-08
solution: implemented
tags: [toolkit, feature, issue, architecture]
---

## FEAT-0003: 特性: Issue 管理 (本地)

## 目标 (Objective)

实现 `monoco issue` 核心动作，专注于工单生命周期管理和结构化进度统计，不干预内容编写。

## 验收标准 (Acceptance Criteria)

1. **创建 (Create)**: `monoco issue create <epic|story|task|bug> --title "..."` 自动创建文件并分配 ID。
2. **关闭 (Close)**: `monoco issue close {ID} --solution {type}` 将工单移动至对应类型的 `closed/` 目录，并更新状态为 `closed`。
3. **取消 (Cancel)**: `monoco issue cancel {ID}` 将工单标记为 `cancelled`。
4. **范围 (Scope)**: `monoco issue scope` 展示树状进度统计。
   - 支持 `--sprint {sprint-id}` 仅显示特定迭代。
   - 统计格式: `[Epic] Title (2/5 Stories Done)`。
5. **无列表 (No List)**: 按照要求删除通用 list 命令，通过 scope 实现概览。

## 技术任务 (Technical Tasks)

- [x] 实现 `Issue` 模型和目录映射。
- [x] 实现带有自增 ID 逻辑的 `monoco issue create`。
- [x] 实现带有文件移动逻辑的 `monoco issue archive/cancel`。
- [x] 使用 `Rich.Tree` 可视化实现 `monoco issue scope`。
- [x] 实现用于范围扫描的 `--sprint` 过滤器。
