---
id: CHORE-0046
uid: d2b75a
type: chore
status: open
stage: doing
title: 架构重构：Agent Session 职责拆分与生命周期管理
created_at: '2026-02-06T09:43:48'
updated_at: '2026-02-06T10:37:50'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0046'
- '#EPIC-0000'
files: []
criticality: low
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-06T09:43:48'
---

## CHORE-0046: 架构重构：Agent Session 职责拆分与生命周期管理

## Objective

强化 Agent Session 的职责边界，通过强制回收和工具拦截机制，确保 "开发" 与 "评审/合拢" 职能的物理隔离，符合 Trunk-Based Development 质量门禁要求。

## Acceptance Criteria

- [ ] Daemon 监听到 Issue Stage 变更为 `review` 后，能自动识别并强制终止对应的 `Engineer` 角色 Session。
- [ ] 实现 Agent 框架层的 Pre-Tool Hook，当角色为 `Engineer` 时拦截 `monoco issue close` 工具的执行。
- [ ] 提供明确的拦截反馈，指导 Agent monoco submit issue 而非尝试合拢。

## Technical Tasks

- [ ] **Daemon 层增强**:
  - [ ] 在 `AgentScheduler` 中添加 `terminate_session(issue_id, role)` 接口。
  - [ ] 更新 `IssueStageHandler`，在阶段跃迁至 `review` 时触发强制回收逻辑。
- [ ] **拦截层实现**:
  - [ ] 在 Agent 执行链路中注入校验逻辑（Pre-Tool Hook）。
  - [ ] 定义角色特权指令白名单/黑名单。
- [ ] **验证**:
  - [ ] 模拟 Engineer 尝试 `close` 动作，确认被拦截。
  - [ ] 验证 `submit` 后 Session 是否被物理销毁。

## Review Comments

<!-- Required for Review/Done stage. Record review feedback here. -->
