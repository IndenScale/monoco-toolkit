---
id: FEAT-0181
uid: 806e54
type: feature
status: open
stage: doing
title: Implement Issue Lifecycle Hooks (ADR-001)
created_at: '2026-02-05T08:58:16'
updated_at: '2026-02-05T08:59:09'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0181'
files:
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Features/open/FEAT-0180-issue-lifecycle-hooks-pre-post-command-validation.md
- docs/zh/98_ADRs/ADR-001-issue-lifecycle-hooks.md
- docs/zh/98_ADRs/ADR-002-lint-error-collection-strategy.md
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-05T08:58:16'
isolation:
  type: branch
  ref: FEAT-0181-implement-issue-lifecycle-hooks-adr-001
  created_at: '2026-02-05T08:58:21'
---

## FEAT-0181: Implement Issue Lifecycle Hooks (ADR-001)

## Objective
根据 ADR-001 实现 Issue 生命周期钩子系统。该系统将 Issue 的状态变更逻辑（如 submit, start, close）与前置条件检查、后置处理逻辑解耦。通过引入分层架构（Trigger -> Dispatcher -> Hook），使 Monoco 能够支持多环境（CLI, Agent, IDE）下的统一生命周期治理。

## Acceptance Criteria
- [ ] 实现 `IssueEvent` 枚举，涵盖 create, start, submit, close 的 before/after 事件。
- [ ] 实现 `IssueHookDispatcher` 核心逻辑，能够发现并执行本地钩子脚本。
- [ ] 提供 `DirectTrigger` 适配器，支持本地 CLI 命令触发钩子。
- [ ] 提供 `AgentToolAdapter` 适配器，实现 Agent 环境下的钩子桥接。
- [ ] 重构 `monoco issue submit/start/close` 命令，接入 Hook 流程并保持向后兼容。
- [ ] 实现内置的 `before-submit` 钩子（包含 lint 和分支检查）。
- [ ] 钩子返回的建议（suggestions）能够被 Agent 解析并展示。

## Technical Tasks

- [x] **Phase 0: 方案设计与 Issue 细化**
- [ ] **Phase 1: 基础设施建设**
  - [ ] 定义核心模型：`IssueEvent`, `IssueHookResult`, `HookDecision`
  - [ ] 实现钩子加载与分发逻辑 `IssueHookDispatcher`
  - [ ] 实现基础适配器 `DirectTrigger`
- [ ] **Phase 2: 命令集成与重构**
  - [ ] 重构 `submit` 命令集成生命周期钩子
  - [ ] 重构 `start` 命令集成生命周期钩子
  - [ ] 重构 `close` 命令集成生命周期钩子
  - [ ] 实现 `--no-hooks` 和 `--debug-hooks` 参数
- [ ] **Phase 3: 内置与自定义钩子支持**
  - [ ] 实现默认内置钩子（Branch check, Lint trigger）
  - [ ] 建立钩子存放目录规范（`.monoco/hooks/issue/`）
  - [ ] 文档更新：在 `docs/` 下添加钩子开发指南

## Review Comments


