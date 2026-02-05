---
id: FEAT-0183
uid: 8c5728
type: feature
status: closed
stage: done
title: 实现 post-issue-create 实时 Lint 反馈机制
created_at: '2026-02-05T10:08:58'
updated_at: '2026-02-05T10:14:08'
parent: EPIC-0027
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0027'
- '#FEAT-0183'
files:
- monoco/core/output.py
- monoco/features/issue/commands.py
- monoco/features/issue/hooks/builtin/__init__.py
- monoco/features/issue/hooks/integration.py
criticality: medium
solution: implemented
opened_at: '2026-02-05T10:08:58'
closed_at: '2026-02-05T10:14:08'
isolation:
  type: branch
  ref: FEAT-0183-实现-post-issue-create-实时-lint-反馈机制
  created_at: '2026-02-05T10:08:59'
---

## FEAT-0183: 实现 post-issue-create 实时 Lint 反馈机制

## Objective

在 Issue 创建后立即触发 Lint 校验，并通过隔离的 `stderr` 流提供实时反馈（Suggestions），指导 Agent 补充缺失的元数据。

## Acceptance Criteria

- [x] 实现 `post-issue-create` 内置钩子，集成 Lint 校验逻辑
- [x] 重构 `OutputManager` 支持 `stdout`（数据）与 `stderr`（建议/反馈）的分离
- [x] 重构 `HookContextManager` 和 `handle_hook_result` 以支持非阻塞的实时反馈输出
- [x] 验证 Agent 模式（--json）下流隔离的正确性

## Technical Tasks

- [x] 完善 `monoco/core/output.py` 中的流管理
- [x] 在 `monoco/features/issue/hooks/builtin/__init__.py` 中添加 `post_create_hook`
- [x] 修改 `monoco/features/issue/hooks/integration.py` 的反馈逻辑
- [x] 验证 `monoco issue create` 的输出效果

## Review Comments

- 成功实现了 Stdout 与 Stderr 的隔离。
- 钩子返回的 Suggestions 现在会通过 `info` 级别输出到 Stderr。
