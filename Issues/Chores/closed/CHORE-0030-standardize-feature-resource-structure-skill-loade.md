---
id: CHORE-0030
uid: 86c2bd
type: chore
status: closed
stage: done
title: Standardize Feature Resource Structure & Skill Loader
created_at: '2026-02-02T09:59:50'
updated_at: '2026-02-02T10:23:20'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0030'
- '#EPIC-0000'
files:
- monoco/core/skills.py
- monoco/features/agent/resources/en/skills/monoco_atom_core/SKILL.md
- monoco/features/agent/resources/en/skills/monoco_workflow_agent_engineer/SKILL.md
- monoco/features/agent/resources/en/skills/monoco_workflow_agent_manager/SKILL.md
- monoco/features/agent/resources/en/skills/monoco_workflow_agent_planner/SKILL.md
- monoco/features/agent/resources/en/skills/monoco_workflow_agent_reviewer/SKILL.md
- monoco/features/issue/resources/en/skills/monoco_atom_issue/SKILL.md
- monoco/features/issue/resources/en/skills/monoco_workflow_issue_creation/SKILL.md
- monoco/features/issue/resources/en/skills/monoco_workflow_issue_development/SKILL.md
- monoco/features/issue/resources/en/skills/monoco_workflow_issue_management/SKILL.md
- monoco/features/issue/resources/en/skills/monoco_workflow_issue_refinement/SKILL.md
- monoco/features/memo/resources/en/skills/monoco_atom_memo/SKILL.md
- monoco/features/memo/resources/en/skills/monoco_workflow_note_processing/SKILL.md
- monoco/features/spike/resources/en/skills/monoco_atom_spike/SKILL.md
- monoco/features/spike/resources/en/skills/monoco_workflow_research/SKILL.md
- monoco/features/i18n/resources/en/skills/monoco_atom_i18n/SKILL.md
- monoco/features/i18n/resources/en/skills/monoco_workflow_i18n_scan/SKILL.md
- monoco/features/glossary/resources/en/skills/monoco_atom_glossary/SKILL.md
criticality: low
solution: implemented
opened_at: '2026-02-02T09:59:50'
closed_at: '2026-02-02T10:23:20'
---

## CHORE-0030: Standardize Feature Resource Structure & Skill Loader

## Objective
为了维护架构的清晰性和一致性，我们需要标准化 Monoco Toolkit 的资源文件结构。核心原则是：**Core 仅作为框架，只有 Feature 才是价值交付原子**。因此，所有的 Skill、Role 和 System Prompts 必须由 Feature 承载，严禁直接存放于 Core 模块中。同时，加载器需要升级以严格遵循这一规范。

## Acceptance Criteria
- [x] **Core 纯净**: `monoco/core/resources` 目录被彻底移除，无残留。
- [x] **Feature 为主**: 所有资源 (Skill/Role/Prompt) 均位于 `monoco/features/{feature}/resources/{lang}/{type}/` 标准路径下。
- [x] **单一来源**: `SkillManager` 仅通过扫描 Feature 目录来发现资源，移除对 Core 目录的硬编码扫描。
- [x] **命名规范**: 所有 Skill/Role 均遵循 `monoco_{type}_{name}` 命名规范，且元数据与目录名一致。
- [x] **同步正常**: `monoco sync` 能正确识别并分发所有已知的 Skill (23 个) 到 Agent 环境。

## Technical Tasks
- [x] **资源迁移**:
    - [x] 检查并移动所有剩余的 `monoco/core/resources/*` 内容到 `monoco/features/agent/resources/*` 或其他合适特征下。
    - [x] 确保所有 Feature 的资源目录结构统一为 `resources/{lang}/{skills|roles}/`。
- [x] **元数据校准**:
    - [x] 遍历所有 `SKILL.md` 和 `.yaml` 角色文件，确保 `name` 字段与文件夹名称 (`monoco_{type}_{name}`) 严格一致。
    - [x] 确保 `type` 字段正确 (atom, workflow, role)。
- [x] **Loader 重构**:
    - [x] 修改 `monoco/core/skills.py`，彻底删除 `_discover_core_skills` 方法。
    - [x] 优化 `_discover_skills_from_features` 和 `_discover_three_level_skills`，使其仅在标准路径下查找。
- [x] **验证**:
    - [x] 运行 `monoco sync` 验证分发结果。

## Review Comments

### 变更摘要

1. **目录结构标准化**:
   - 重命名了所有不符合 `monoco_{type}_{name}` 规范的英文技能目录
   - 统一了所有 SKILL.md 的元数据，确保 `name` 和 `type` 字段与目录名一致

2. **SkillManager 重构**:
   - 移除了 `flow_skill_prefix` 参数和 `FLOW_SKILL_PREFIX` 常量
   - 更新了 `_discover_skills_in_resources` 方法，仅接受 `monoco_` 前缀的技能
   - 更新了 `_discover_three_level_skills` 方法，现在从以下路径发现技能：
     - `resources/atoms/*.yaml` → Atom Skills
     - `resources/workflows/*.yaml` → Workflow Skills  
     - `resources/{lang}/roles/*.yaml` → Role Skills
   - 更新了文档字符串，明确说明 Core 仅作为框架，所有技能由 Feature 承载

3. **验证结果**:
   - `monoco sync` 成功分发 23 个技能到所有 Agent 环境
   - 所有技能均遵循 `monoco_{type}_{name}` 命名规范
