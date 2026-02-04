---
id: FEAT-0179
uid: 283ca5
type: feature
status: open
stage: draft
title: 治理与简化 Skill 体系：Role/Workflow 融合与 JIT 劝导
created_at: '2026-02-04T20:40:16'
updated_at: '2026-02-04T20:40:16'
parent: EPIC-0030
dependencies:
- CHORE-0039
related: []
domains:
- DevEx
- AgentEmpowerment
tags:
- '#EPIC-0030'
- '#FEAT-0179'
files:
- .gemini/skills/
- AGENTS.md
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-04T20:40:16'
---

## FEAT-0179: 治理与简化 Skill 体系：Role/Workflow 融合与 JIT 劝导

## Objective
通过消除 Role、Workflow 和 Atom 技能之间的逻辑冗余，显著精简 Skill 体系。引入基于 Hooks 的 JIT 劝导机制，将静态规则约束转变为动态环境反馈，提升 Agent 执行效率。

## Acceptance Criteria
- [ ] `.gemini/skills` 目录下的冗余技能（Workflow/Atom）被移除
- [ ] Role 技能整合了必要的工作流逻辑，初始化速度提升
- [ ] `AGENTS.md` 中的资源声明得到简化
- [ ] 实现至少一个工作流阶段的 JIT 劝导（如：start 分支检查）

## Technical Tasks
- [ ] **Skill 融合**: 将 `monoco_workflow_agent_*` 逻辑合并入 `monoco_role_*`
- [ ] **清理冗余**: 删除所有 `monoco_atom_*` 技能文件
- [ ] **重构 AGENTS.md**: 简化角色资源配置，移除对已删除技能的引用
- [ ] **实现 JIT 注入**: 基于 CHORE-0039 的设计，在关键工具调用前后注入劝导信息

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->