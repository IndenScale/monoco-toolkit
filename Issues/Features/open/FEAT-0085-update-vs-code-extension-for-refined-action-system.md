---
id: FEAT-0085
uid: e0bd61
type: feature
status: open
stage: draft
title: 更新 VS Code 扩展以支持优化的动作系统
created_at: "2026-01-16T23:45:53"
opened_at: "2026-01-16T23:45:53"
updated_at: "2026-01-16T23:45:53"
dependencies: []
related: []
tags: []
---

## FEAT-0085: 更新 VS Code 扩展以支持优化的动作系统

## 目标 (Objective)

更新 VS Code 扩展（TypeScript 客户端）以完全支持 FEAT-0084 中定义的“极简动作集”。扩展应基于 CLI 报告的 Issue 当前状态动态渲染 CodeLens 动作（例如 `$(play) Start`, `$(tools) Develop`），替换通用的“Agent Actions”菜单。

## 验收标准 (Acceptance Criteria)

1.  **动态渲染**：编辑器显示与 Issue 元数据中 `actions` 字段对应的特定 CodeLens 动作（Start, Develop, Submit 等）。
2.  **命令绑定**：点击这些动作将触发正确的底层 CLI 命令（例如 Develop 触发 `monoco agent run ...`，Submit 触发 `monoco issue submit`）。
3.  **移除旧代码**：移除旧的通用的 "Agent Actions" CodeLens。
4.  **图标支持**：动作应渲染其指定的图标（例如 `$(check)`）。

## 技术任务 (Technical Tasks)

- [x] **数据获取**：更新 `ActionService.ts` 以从 `monoco issue scope`（或文件解析）输出中检索可用动作。
- [x] **Provider 更新**：重构 `IssueCodeLensProvider.ts` 以遍历 `actions` 列表并生成单独的 `CodeLens` 对象。
- [x] **命令处理程序**：确保 `monoco.runAction` 或新的处理程序能够执行 CLI 返回的特定命令/参数。
