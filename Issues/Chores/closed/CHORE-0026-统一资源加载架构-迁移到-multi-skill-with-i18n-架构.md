---
id: CHORE-0026
uid: d47049
type: chore
status: closed
stage: done
title: 统一资源加载架构：迁移到 Multi-skill with i18n 架构
created_at: '2026-01-31T20:44:47'
updated_at: '2026-01-31T21:03:33'
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
closed_at: '2026-01-31T21:03:33'
solution: implemented
---

## CHORE-0026: 统一资源加载架构：迁移到 Multi-skill with i18n 架构

## Objective

当前项目资源加载存在架构混乱：
1. **架构不一致**: 部分模块使用 `resources/{lang}/SKILL.md`（大而无当），部分使用 `resources/skills/{name}/SKILL.md`（无国际化）
2. **国际化不完整**: 部分模块有中英文区分，部分只有中文
3. **元数据不规范**: 部分 Skill 缺少 `type` 等关键字段

**核心规则**:
- ❌ **禁止**在 `resources/{lang}/` 下放 `SKILL.md`（大而无当的 skill）
- ✅ **必须**使用 `resources/{lang}/skills/{skill-name}/SKILL.md` 结构
- ✅ `resources/{lang}/AGENTS.md` 用于注入项目上下文

## Acceptance Criteria

- [x] 所有 Feature 统一使用 `resources/{lang}/skills/{name}/SKILL.md` 架构
- [x] 所有 Skill 必须包含 `en` 和 `zh` 两种语言版本
- [x] 删除所有 `resources/{lang}/SKILL.md`（迁移或删除）
- [x] 所有 Skill 元数据必须包含 `type` 字段（standard/flow/workflow）
- [x] 重构 `monoco/core/skills.py` 支持新的目录结构
- [x] 所有现有 Skill 完成迁移并通过验证

## 统一后的目录结构

```
monoco/features/{feature}/
└── resources/
    ├── en/
    │   ├── AGENTS.md              # 项目上下文（可选）
    │   └── skills/
    │       ├── {skill-name}/
    │       │   └── SKILL.md
    │       └── ...
    ├── zh/
    │   ├── AGENTS.md              # 项目上下文（可选）
    │   └── skills/
    │       ├── {skill-name}/
    │       │   └── SKILL.md
    │       └── ...
    └── roles/                     # 仅 agent feature
        └── {role}.yaml
```

## Technical Tasks

### Phase 1: 重构 Skill 发现机制

- [x] 修改 `monoco/core/skills.py`:
  - [x] 统一从 `resources/{lang}/skills/{name}/SKILL.md` 发现 Skills
  - [x] 移除对 `resources/{lang}/SKILL.md` 的支持
  - [x] 修改 `Skill` 类支持按语言加载
  - [x] 统一 `distribute` 逻辑，所有 Skill 按语言分发

### Phase 2: 迁移现有 Skills

**需要迁移的 Legacy Skills（当前在 `resources/{lang}/SKILL.md`）**:

| Feature | 当前位置 | 处理方式 | 目标位置 |
|---------|----------|----------|----------|
| core | `core/resources/{lang}/SKILL.md` | 迁移 | `core/resources/{lang}/skills/monoco_core/SKILL.md` |
| glossary | `glossary/resources/{lang}/SKILL.md` | 迁移 | `glossary/resources/{lang}/skills/monoco_glossary/SKILL.md` |
| issue | `issue/resources/{lang}/SKILL.md` | 迁移 | `issue/resources/{lang}/skills/monoco_issue/SKILL.md` |
| spike | `spike/resources/{lang}/SKILL.md` | 迁移 | `spike/resources/{lang}/skills/monoco_spike/SKILL.md` |
| i18n | `i18n/resources/{lang}/SKILL.md` | 迁移 | `i18n/resources/{lang}/skills/monoco_i18n/SKILL.md` |
| memo | `memo/resources/zh/SKILL.md` | 迁移 + 创建 en | `memo/resources/{lang}/skills/monoco_memo/SKILL.md` |

**需要补充国际化的 Multi-skills（当前在 `resources/skills/{name}/SKILL.md`）**:

| Feature | Skill | 操作 |
|---------|-------|------|
| agent | flow_engineer | 创建 `en/skills/flow_engineer/SKILL.md` 和 `zh/skills/flow_engineer/SKILL.md` |
| agent | flow_manager | 创建 `en/skills/flow_manager/SKILL.md` 和 `zh/skills/flow_manager/SKILL.md` |
| agent | flow_planner | 创建 `en/skills/flow_planner/SKILL.md` 和 `zh/skills/flow_planner/SKILL.md` |
| agent | flow_reviewer | 创建 `en/skills/flow_reviewer/SKILL.md` 和 `zh/skills/flow_reviewer/SKILL.md` |
| issue | issue_create_workflow | 创建 `en/skills/issue_create_workflow/SKILL.md` 和 `zh/skills/issue_create_workflow/SKILL.md` |
| issue | issue_develop_workflow | 创建 `en/skills/issue_develop_workflow/SKILL.md` 和 `zh/skills/issue_develop_workflow/SKILL.md` |
| issue | issue_lifecycle_workflow | 创建 `en/skills/issue_lifecycle_workflow/SKILL.md` 和 `zh/skills/issue_lifecycle_workflow/SKILL.md` |
| issue | issue_refine_workflow | 创建 `en/skills/issue_refine_workflow/SKILL.md` 和 `zh/skills/issue_refine_workflow/SKILL.md` |
| spike | research_workflow | 创建 `en/skills/research_workflow/SKILL.md` 和 `zh/skills/research_workflow/SKILL.md` |
| i18n | i18n_scan_workflow | 创建 `en/skills/i18n_scan_workflow/SKILL.md` 和 `zh/skills/i18n_scan_workflow/SKILL.md` |
| memo | note_processing_workflow | 创建 `en/skills/note_processing_workflow/SKILL.md` 和 `zh/skills/note_processing_workflow/SKILL.md` |

### Phase 3: 统一元数据

- [x] 为所有 Skills 添加 `type` 字段 (standard/flow/workflow)
- [x] 为所有 Skills 添加 `version: 1.0.0`
- [x] 统一 `name` 字段为 kebab-case

### Phase 4: 清理和验证

- [x] 删除所有 `resources/{lang}/SKILL.md`（已迁移）
- [x] 删除空的 `resources/skills/` 目录（已迁移）
- [x] 运行 `monoco sync` 验证所有 Skill 正确分发
- [x] 验证 `.claude/skills/` 目录结构正确
- [x] 运行测试确保无回归

## Review Comments

## Review Comments

### 架构变更总结

1. **统一目录结构**: 所有 Skills 现在使用 `resources/{lang}/skills/{name}/SKILL.md` 结构
2. **完整国际化**: 所有 17 个 Skills 都包含 `en` 和 `zh` 两种语言版本
3. **元数据标准化**: 所有 Skills 都包含 `type` 和 `version` 字段
4. **代码重构**: `monoco/core/skills.py` 完全重写，移除 Legacy 支持

### 测试验证

- 所有 312 个单元测试通过
- `monoco sync` 成功分发所有 Skills 到各个 Agent 框架
- 验证了 `.claude/skills/`、`.gemini/skills/` 等目录结构正确

### 破坏性变更

- 移除了对 `resources/{lang}/SKILL.md`（根目录下）的支持
- 旧版 Multi-skill 架构（`resources/skills/{name}/SKILL.md` 无语言子目录）不再支持
