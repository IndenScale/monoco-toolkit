---
id: CHORE-0026
uid: d47049
type: chore
status: open
stage: doing
title: 统一资源加载架构：迁移到 Multi-skill with i18n 架构
created_at: '2026-01-31T20:44:47'
updated_at: '2026-01-31T20:45:16'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0026'
- '#EPIC-0000'
files: []
criticality: medium
opened_at: '2026-01-31T20:44:47'
---

## CHORE-0026: 统一资源加载架构：迁移到 Multi-skill with i18n 架构

## Objective

当前项目资源加载存在架构混乱：
1. **架构不一致**: 部分模块使用 Legacy 单 Skill 架构，部分使用 Multi-skill 架构
2. **国际化不完整**: 部分模块有中英文区分，部分只有中文
3. **元数据不规范**: 部分 Skill 缺少 `type` 等关键字段

本任务旨在统一所有资源加载机制，迁移到标准的 **Multi-skill with i18n** 架构。

## Acceptance Criteria

- [ ] 所有 Feature 统一使用 Multi-skill 架构（`resources/skills/{skill-name}/`）
- [ ] 所有 Skill 必须包含 `en` 和 `zh` 两种语言版本
- [ ] 所有 Skill 元数据必须包含 `type` 字段（standard/flow/workflow）
- [ ] 移除 `monoco/core/skills.py` 中的 Legacy 支持代码
- [ ] 更新资源分发逻辑，统一处理所有 Skill 类型
- [ ] 所有现有 Skill 完成迁移并通过验证

## Technical Tasks

### Phase 1: 补充缺失的语言版本

- [ ] 创建 `monoco/features/memo/resources/skills/monoco_memo/` 目录结构
- [ ] 将 `monoco/features/memo/resources/zh/SKILL.md` 移动到 `monoco_memo/zh/SKILL.md`
- [ ] 创建 `monoco_memo/en/SKILL.md`（翻译或创建英文版）
- [ ] 为 `agent` feature 的所有 flow skills 创建英文版
  - [ ] `flow_engineer/en/SKILL.md`
  - [ ] `flow_manager/en/SKILL.md`
  - [ ] `flow_planner/en/SKILL.md`
  - [ ] `flow_reviewer/en/SKILL.md`
- [ ] 为所有 Workflow Skills 创建英文版
  - [ ] `issue_create_workflow/en/SKILL.md`
  - [ ] `issue_develop_workflow/en/SKILL.md`
  - [ ] `issue_lifecycle_workflow/en/SKILL.md`
  - [ ] `issue_refine_workflow/en/SKILL.md`
  - [ ] `research_workflow/en/SKILL.md`
  - [ ] `i18n_scan_workflow/en/SKILL.md`
  - [ ] `note_processing_workflow/en/SKILL.md`

### Phase 2: 迁移 Legacy Skills 到 Multi-skill 架构

- [ ] **core**: 创建 `monoco/core/resources/skills/monoco_core/` 目录
- [ ] **core**: 移动 `resources/{lang}/SKILL.md` 到 `skills/monoco_core/{lang}/SKILL.md`
- [ ] **glossary**: 创建 `monoco/features/glossary/resources/skills/monoco_glossary/` 目录
- [ ] **glossary**: 移动 `resources/{lang}/SKILL.md` 到 `skills/monoco_glossary/{lang}/SKILL.md`
- [ ] **issue**: 创建 `monoco/features/issue/resources/skills/monoco_issue/` 目录
- [ ] **issue**: 移动 `resources/{lang}/SKILL.md` 到 `skills/monoco_issue/{lang}/SKILL.md`
- [ ] **spike**: 创建 `monoco/features/spike/resources/skills/monoco_spike/` 目录
- [ ] **spike**: 移动 `resources/{lang}/SKILL.md` 到 `skills/monoco_spike/{lang}/SKILL.md`
- [ ] **i18n**: 创建 `monoco/features/i18n/resources/skills/monoco_i18n/` 目录
- [ ] **i18n**: 移动 `resources/{lang}/SKILL.md` 到 `skills/monoco_i18n/{lang}/SKILL.md`

### Phase 3: 统一元数据

- [ ] 为所有 Legacy Skills 添加 `type: standard` 到元数据
- [ ] 为所有 Skill 添加 `version: 1.0.0` 到元数据
- [ ] 统一 `name` 字段格式为 kebab-case

### Phase 4: 重构代码

- [ ] 修改 `monoco/core/skills.py` 移除 `_discover_legacy_skill` 方法
- [ ] 修改 `_discover_skills_from_features` 只调用 `_discover_multi_skills`
- [ ] 修改 `_discover_core_skill` 使用 Multi-skill 架构
- [ ] 修改 `distribute` 方法统一处理所有 Skill 类型（按语言分发）
- [ ] 移除 `_distribute_standard_skill` 和 `_distribute_flow_skill` 的差异处理
- [ ] 更新 `Skill.get_languages()` 方法适配新架构

### Phase 5: 清理和验证

- [ ] 删除所有空的 `resources/{lang}/` 目录
- [ ] 运行 `monoco sync` 验证所有 Skill 正确分发
- [ ] 验证 `.claude/skills/` 目录结构正确
- [ ] 运行测试确保无回归

## 统一后的目录结构

```
monoco/
├── core/
│   └── resources/
│       └── skills/
│           └── monoco_core/
│               ├── en/SKILL.md
│               └── zh/SKILL.md
└── features/
    ├── agent/
    │   └── resources/
    │       ├── skills/
    │       │   ├── flow_engineer/
    │       │   │   ├── en/SKILL.md
    │       │   │   └── zh/SKILL.md
    │       │   ├── flow_manager/
    │       │   │   ├── en/SKILL.md
    │       │   │   └── zh/SKILL.md
    │       │   ├── flow_planner/
    │       │   │   ├── en/SKILL.md
    │       │   │   └── zh/SKILL.md
    │       │   └── flow_reviewer/
    │       │       ├── en/SKILL.md
    │       │       └── zh/SKILL.md
    │       └── roles/
    │           ├── engineer.yaml
    │           ├── manager.yaml
    │           ├── planner.yaml
    │           └── reviewer.yaml
    ├── glossary/
    │   └── resources/
    │       └── skills/
    │           └── monoco_glossary/
    │               ├── en/SKILL.md
    │               └── zh/SKILL.md
    ├── i18n/
    │   └── resources/
    │       └── skills/
    │           ├── monoco_i18n/
    │           │   ├── en/SKILL.md
    │           │   └── zh/SKILL.md
    │           └── i18n_scan_workflow/
    │               ├── en/SKILL.md
    │               └── zh/SKILL.md
    ├── issue/
    │   └── resources/
    │       └── skills/
    │           ├── monoco_issue/
    │           │   ├── en/SKILL.md
    │           │   └── zh/SKILL.md
    │           ├── issue_create_workflow/
    │           │   ├── en/SKILL.md
    │           │   └── zh/SKILL.md
    │           ├── issue_develop_workflow/
    │           │   ├── en/SKILL.md
    │           │   └── zh/SKILL.md
    │           ├── issue_lifecycle_workflow/
    │           │   ├── en/SKILL.md
    │           │   └── zh/SKILL.md
    │           └── issue_refine_workflow/
    │               ├── en/SKILL.md
    │               └── zh/SKILL.md
    ├── memo/
    │   └── resources/
    │       └── skills/
    │           ├── monoco_memo/
    │           │   ├── en/SKILL.md
    │           │   └── zh/SKILL.md
    │           └── note_processing_workflow/
    │               ├── en/SKILL.md
    │               └── zh/SKILL.md
    └── spike/
        └── resources/
            └── skills/
                ├── monoco_spike/
                │   ├── en/SKILL.md
                │   └── zh/SKILL.md
                └── research_workflow/
                    ├── en/SKILL.md
                    └── zh/SKILL.md
```

## Review Comments
