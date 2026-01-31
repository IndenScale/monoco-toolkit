---
id: FEAT-0124
uid: f31835
type: feature
status: closed
stage: done
title: Issue Lifecycle Triggers
created_at: '2026-01-31T10:36:48'
updated_at: '2026-01-31T10:48:27'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0124'
files: []
criticality: medium
opened_at: '2026-01-31T10:36:48'
closed_at: '2026-01-31T10:47:01'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0124-issue-lifecycle-triggers
  created_at: '2026-01-31T10:37:05'
---

## FEAT-0124: Issue Lifecycle Triggers

## Objective
实现 Issue 生命周期与 Agent 模块的联动触发机制。当 Issue 状态发生特定转换（如 Start 或 Submit）时，自动触发预配置的操作（如运行 Agent）。
核心目的是通过 `post_actions` 机制，将 Issue 管理与 Agent 开发无缝衔接，打造流畅的自动化工作流。

## Acceptance Criteria
- [x] `TransitionConfig` 模型支持 `post_actions` 字段，用于定义后续操作。
- [x] `monoco issue` 状态转换逻辑支持执行 `post_actions` 中的命令。
- [x] 支持在 `workspace.yaml` 中配置 `start` 动作触发 `monoco agent run --role engineer`。
- [x] 支持在 `workspace.yaml` 中配置 `submit` 动作触发 `monoco agent run --role reviewer`。
- [x] 确保命令执行的稳定性和错误处理（Triggers 失败不应回滚状态转换，但应报警）。

## Technical Tasks
- [x] **Config Schema Update**:
    - [x] 修改 `monoco/core/config.py` 中的 `TransitionConfig`，增加 `post_actions: List[str]` 字段。
- [x] **Logic Implementation**:
    - [x] 在 `monoco/features/issue/core.py` 的状态转换逻辑中，添加 `execute_post_actions` 处理函数。
    - [x] 在 `monoco/features/issue/engine/machine.py` 中更新 `validate_transition` 返回 transition 对象。
    - [x] 实现命令模板替换逻辑（支持 `{id}`, `{title}` 等变量）。
- [x] **Integration & Config**:
    - [x] 更新 `.monoco/workspace.yaml`，为 `start` 和 `submit` 转换添加示例 Trigger 配置。
- [x] **Verification**:
    - [x] 创建测试 Issue，验证 `monoco issue start` 是否正确唤起 Agent。

## Review Comments
- Self-verified: Commands trigger correctly and pass context.
- Verified detach mode works as expected.
