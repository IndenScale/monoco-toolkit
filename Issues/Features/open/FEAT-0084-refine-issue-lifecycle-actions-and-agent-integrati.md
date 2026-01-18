---
id: FEAT-0084
uid: fd7853
type: feature
status: open
stage: draft
title: 优化 Issue 生命周期动作与 Agent 集成
created_at: '2026-01-16T23:32:20'
opened_at: '2026-01-16T23:32:20'
updated_at: '2026-01-16T23:32:20'
dependencies: []
related: []
tags:
- '#FEAT-0084'
---

## FEAT-0084: 优化 Issue 生命周期动作与 Agent 集成

## 目标 (Objective)

优化 Monoco Issue 生命周期动作，使其更加简洁且语义明确（`Investigate`, `Start`, `Develop`, `Submit`, `Accept`, `Reject`, `Cancel`）。通过提供标准化的 `prompty` 模板作为模块资源，并将这些资源初始化到用户工作区，实现这些动作与 Agent 系统的集成。

## 验收标准 (Acceptance Criteria)

1.  **简化的动作模型**: 更新 `IssueAction` 在检查 `AvailableActions` 时的逻辑，以反映新的“极简动作集”。
2.  **Agent 资源**: 在 `monoco.features.agent` 中创建 `investigate.prompty`, `develop.prompty`, `verify.prompty` (用于 Submit/Accept), 和 `architect.prompty` (用于 Investigate) 作为资源。
3.  **初始化**: `monoco agent init`（或 `monoco init` 的一部分）将这些资源复制到 `.monoco/actions/` 或类似位置。
4.  **CLI 集成**: `monoco agent list` 准确反映这些新能力。
5.  **文档**: 更新 `docs/zh/extensions/features/commands.md` 和相关文档以反映新工作流。

## 技术任务 (Technical Tasks)

- [x] **定义 Prompts**: 在 `monoco/features/agent/resources/` 中为 `investigate`, `develop`, `verify`, 和 `critique` 创建标准的 `.prompty` 文件。
- [x] **更新核心逻辑**: 修改 `monoco/features/issue/core.py` -> `get_available_actions` 以实现新的状态流转规则。
- [x] **更新 Agent Init**: 确保 `monoco/features/agent/core.py` 处理初始化期间的资源复制。
- [x] **文档**: 更新文档以描述新的动作语义。
