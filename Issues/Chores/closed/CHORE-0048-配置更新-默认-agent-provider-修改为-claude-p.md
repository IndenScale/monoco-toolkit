---
id: CHORE-0048
uid: 05c771
type: chore
status: closed
stage: done
title: 配置更新：默认 Agent Provider 修改为 Claude -p
created_at: '2026-02-06T09:43:50'
updated_at: '2026-02-06T09:43:50'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
  - '#CHORE-0048'
  - '#EPIC-0000'
files: []
criticality: low
solution: implemented
opened_at: '2026-02-06T09:43:50'
---

## CHORE-0048: 配置更新：默认 Agent Provider 修改为 Claude -p

## Objective

切换系统默认 Agent 引擎为 `claude` (Claude Code CLI)，并调整为 "非自动确认" (Non-YOLO) 模式，以提升交互的受控度，特别是在核心架构清理期间。

## Acceptance Criteria

- [x] `AgentTask` 的引擎默认值变为 `claude`。
- [x] `ClaudeAdapter` 产生的指令不再包含 `-y`。
- [x] 当执行 `claude -p` 时，确保不开启危险的权限跳过参数。

## Technical Tasks

- [x] **默认值修改**:
  - [x] 修改 `src/monoco/core/scheduler/base.py` 中 `AgentTask` 的默认 engine 为 `claude`。
  - [x] 修改 `src/monoco/features/agent/models.py` 中的 Pydantic 默认值。
- [x] **适配器重构**:
  - [x] 更新 `src/monoco/core/scheduler/engines.py` 中的 `ClaudeAdapter`，移除 `-y` 逻辑。
- [x] **验证**:
  - [x] `ClaudeAdapter` 当前已经是 `claude -p` 格式，不含 `-y` 参数。

## Review Comments

已完成配置更新：
- `AgentTask.engine` 默认值已从 `"gemini"` 改为 `"claude"`
- `RoleTemplate.engine` 默认值已从 `"gemini"` 改为 `"claude"`
- `ClaudeAdapter` 更新为 `claude -p <prompt> --permission-mode acceptEdits`
  - 不含 `-y` 危险参数
  - `--permission-mode acceptEdits` 实现平衡：自动接受编辑，但其他操作仍需确认
