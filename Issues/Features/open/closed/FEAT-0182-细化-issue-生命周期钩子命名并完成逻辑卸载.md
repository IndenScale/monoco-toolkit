---
id: FEAT-0182
uid: ad7eb1
type: feature
status: closed
stage: done
title: 细化 Issue 生命周期钩子命名并完成逻辑卸载
created_at: '2026-02-05T09:58:25'
updated_at: '2026-02-05T10:01:07'
parent: EPIC-0027
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0027'
- '#FEAT-0182'
files:
- monoco/features/issue/commands.py
- monoco/features/issue/hooks/builtin/__init__.py
- monoco/features/issue/hooks/models.py
- tests/test_issue_hooks.py
criticality: medium
solution: implemented
opened_at: '2026-02-05T09:58:25'
closed_at: '2026-02-05T10:01:07'
isolation:
  type: branch
  ref: FEAT-0182-细化-issue-生命周期钩子命名并完成逻辑卸载
  created_at: '2026-02-05T09:58:31'
---

## FEAT-0182: 细化 Issue 生命周期钩子命名并完成逻辑卸载

## Objective

重构 Issue 生命周期钩子系统，提升建模粒度并彻底完成命令逻辑的卸载，确保 Monoco 治理机制的高内聚与低耦合。

## Acceptance Criteria

- [x] IssueEvent 命名变更为 `pre-issue-{transaction}` 格式
- [x] 原本硬编码在 `submit` 命令中的同步和 Lint 逻辑已搬迁至内置钩子
- [x] 原本硬编码在 `submit` 命令中的报告生成逻辑已搬迁至内置钩子
- [x] 单元测试已同步通过最新命名协议

## Technical Tasks

- [x] 修改 `monoco/features/issue/hooks/models.py` 中的枚举值
- [x] 在 `monoco/features/issue/hooks/builtin/__init__.py` 中实现具体卸载逻辑
- [x] 清理 `monoco/features/issue/commands.py` 中的臃肿代码
- [x] 更新 `tests/test_issue_hooks.py` 并验证

## Review Comments

- 钩子系统已成功拦截含有占位符的本任务提交请求。
- 逻辑卸载后，`submit` 命令代码行数显著减少。
