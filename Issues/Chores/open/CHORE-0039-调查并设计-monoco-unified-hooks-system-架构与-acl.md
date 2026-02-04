---
id: CHORE-0039
uid: 93cd6c
type: chore
status: open
stage: doing
title: 调查并设计 Monoco Unified Hooks System 架构与 ACL
created_at: '2026-02-04T20:40:16'
updated_at: '2026-02-04T20:58:16'
parent: EPIC-0034
dependencies: []
related: []
domains:
- Foundation
- DevEx
tags:
- '#CHORE-0039'
- '#EPIC-0034'
files:
- Issues/Features/open/FEAT-0179-治理与简化-skill-体系-role-workflow-融合与-jit-劝导.md
- docs/zh/40_hooks/README.md
- docs/zh/40_hooks/agent_feedback_loop.md
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T20:40:16'
isolation:
  type: branch
  ref: CHORE-0039-调查并设计-monoco-unified-hooks-system-架构与-acl
  created_at: '2026-02-04T20:43:07'
---

## CHORE-0039: 调查并设计 Monoco Unified Hooks System 架构与 ACL

## Objective
调查并设计一套统一的钩子系统，用于实现 Just-in-Time (JIT) 劝导。该系统需整合 Git Hooks、IDE Hooks 以及 Agent 框架 Hooks，通过反馈环将环境约束动态注入 Agent 会话。

## Acceptance Criteria
- [ ] 完成对 Gemini CLI 和 Claude Code 钩子机制的调研
- [ ] 创建并完善 `docs/zh/40_hooks/` 目录下的架构文档
- [ ] 定义统一的 Hook 触发与 Prompt 注入协议
- [ ] 论证 JIT 劝导在减少 Skill 冗余方面的有效性

## Technical Tasks
- [ ] 调研现有 Agent 框架的 Middleware/Hooks 注入点
- [ ] 设计 Monoco Unified Hooks 的注册与分发逻辑
- [ ] 更新 `docs/zh/40_hooks/README.md`，定义架构草案
- [ ] 设计首批 JIT 场景（如：代码提交前的 sync-files 劝导）

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->