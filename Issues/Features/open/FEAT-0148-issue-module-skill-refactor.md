---
id: FEAT-0148
uid: 326e1a
type: feature
status: open
stage: draft
title: Issue Module Skill 原子化重构
created_at: '2026-01-31T20:04:50'
updated_at: '2026-02-01T22:42:00'
parent: EPIC-0027
dependencies: []
related: []
domains:
- IssueGovernance
tags:
- '#EPIC-0027'
- '#FEAT-0148'
files: []
criticality: high
opened_at: '2026-01-31T20:04:50'
---

## FEAT-0148: Issue Module Skill 原子化重构

## Objective

当前 `issue-lifecycle-workflow` 过于臃肿，混合了多个职责阶段（创建、启动、开发、提交、评审、关闭），违反了单一职责原则。本 Epic 旨在将其拆分为更细粒度的原子 Flow Skills，并明确区分 **Copilot 模式**（人类主导）和 **Autopilot 模式**（Agent 自主执行）的技能设计。

**价值主张**:
- 提高灵活性：不同场景使用不同 Flow，不必强制走完整生命周期
- 明确职责：每个 Flow 只负责一个明确的阶段
- 支持协作：产品经理、架构师、开发者可以使用各自专注的 Flow
- 便于维护：修改一个 Flow 不会影响其他 Flow

## Acceptance Criteria

- [ ] Copilot 模式原子 Flow Skills 创建完成（3 个）
- [ ] Autopilot Planner Role 和 Flow Skill 创建完成
- [ ] 现有 `issue-lifecycle-workflow` 重构或废弃
- [ ] 所有新 Skill 遵循 `resources/{lang}/` 多语言结构
- [ ] Skill 同步机制验证通过

## Technical Tasks

### Phase 1: Copilot Skills (Issue Module)
- [ ] 创建 `issue_create_workflow` - Memo 到 Issue 的转化流程
- [ ] 创建 `issue_refine_workflow` - Issue 调查细化流程  
- [ ] 创建 `issue_develop_workflow` - Issue 开发交付流程
- [ ] 更新 `monoco/features/issue/resources/skills/` 结构

### Phase 2: Autopilot Skills (Agent Module)
- [ ] 创建 `planner.yaml` Role 定义
- [ ] 创建 `flow_planner` Flow Skill
- [ ] 更新 `monoco/features/agent/resources/roles/` 和 `skills/`

### Phase 3: 重构与清理
- [ ] 重构现有 `issue_lifecycle_workflow`
- [ ] 更新 Skill 分发配置
- [ ] 验证 `.claude/skills/` 同步结果
- [ ] 废弃旧版 lifecycle workflow（可选）

## Architecture

```
monoco/features/issue/
└── resources/
    ├── en/SKILL.md, zh/SKILL.md     # Core Skill (copilot: 命令参考)
    └── skills/
        ├── issue_create_workflow/        # 创建 Issue 工作流
        ├── issue_refine_workflow/        # 调查细化工作流  
        └── issue_develop_workflow/       # 开发交付工作流

monoco/features/agent/
└── resources/
    ├── roles/
    │   ├── planner.yaml              # 新角色: 规划/细化
    │   ├── engineer.yaml             # 现有: 开发
    │   ├── manager.yaml              # 现有: 管理
    │   └── reviewer.yaml             # 现有: 评审
    └── skills/
        ├── flow_planner/               # 规划执行流
        ├── flow_engineer/              # 现有: 开发执行流
        └── flow_reviewer/              # 现有: 评审执行流
```

## Related Issues

- 相关 Feature 已归档至 `.archives/issues-archive-20260201.tar.gz`

## Review Comments

- 2026-01-31: Epic 创建完成，定义了 Issue Module Skill 原子化重构的目标和范围。
- 包含 Copilot 模式原子 Flow Skills 和 Autopilot Planner Role 的创建计划。
