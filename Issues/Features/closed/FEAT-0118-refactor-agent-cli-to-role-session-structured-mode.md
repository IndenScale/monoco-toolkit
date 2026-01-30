---
id: FEAT-0118
uid: d4b49d
type: feature
status: closed
stage: done
title: Refactor Agent CLI to Role-Session Structured Mode
created_at: '2026-01-30T14:11:10'
updated_at: 2026-01-30 14:25:04
parent: EPIC-0019
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0019'
- '#FEAT-0118'
files:
- Issues/Features/open/FEAT-0118-refactor-agent-cli-to-role-session-structured-mode.md
- monoco/features/scheduler/cli.py
- monoco/features/scheduler/defaults.py
- monoco/features/scheduler/models.py
- monoco/features/scheduler/reliability.py
- monoco/features/scheduler/worker.py
- monoco/main.py
criticality: medium
opened_at: '2026-01-30T14:11:10'
closed_at: '2026-01-30T14:25:03'
solution: implemented
---

## FEAT-0118: Refactor Agent CLI to Role-Session Structured Mode

## Objective
重构 `monoco agent` 的命令行架构，从“业务功能导向”转向“资源角色导向”。
消除硬编码的 `draft` 和 `autopsy` 命令，将管理职责收敛至结构化的子命令中，确保 CLI 设计符合 Agent Native 的核心哲学：Role (能力模板) 与 Session (执行实例) 的清晰分离。

## Acceptance Criteria
- [x] **结构化命名空间**:
  - `monoco agent run`: 唯一的启动入口。
  - `monoco agent session [list|kill|logs|autopsy]`: 实例生命周期管理。
  - `monoco agent role [list|info|...]`: 角色定义管理。
  - `monoco agent provider [list|check]`: 外部 Provider/Engine 管理。
- [x] **语义精简**: 移除 `agent draft`, `agent autopsy`。
- [x] **顶层收敛**: 移除顶层 `monoco role` 命令，将其并入 `monoco agent role`。
- [x] **职责清晰**: `run` 命令不再包含逻辑分叉，仅负责根据指定的 Role 启动 Session。

## Technical Tasks
- [x] **CLI 重构**:
  - [x] 修改 `monoco/features/scheduler/cli.py` 实现结构化 Typer。
  - [x] 移除 `main.py` 中的顶层 `role` 挂载。
- [x] **逻辑整合**:
  - [x] 将 `_run_draft` 和 `_run_autopsy` 逻辑合入角色分发流程。
  - [x] 实现 `monoco agent provider` 管理逻辑。
- [x] **文档与验证**:
  - [x] 更新 `monoco agent --help` 说明文档。
  - [x] 验证现有测试用例。

## Review Comments
- IndenScale: 确认重构符合 Agent Native 哲学。
- IndenScale: 定位并清理了过时的 Role (crafter/auditor) 命名，确立了 Planner/Builder/Reviewer/Merger/Coroner/Manager 六大标准角色。
- IndenScale: 补全了 `monoco agent provider` 管理指令，完善了架构闭环。

## Delivery
<!-- Monoco Auto Generated -->
**Commits (1)**:
- `84506de` docs(issue): update task status for FEAT-0118

**Touched Files (1)**:
- `Issues/Features/open/FEAT-0118-refactor-agent-cli-to-role-session-structured-mode.md`
