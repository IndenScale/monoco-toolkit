---
id: CHORE-0047
uid: '697782'
type: chore
status: open
stage: doing
title: 角色重命名：收缩为三角色模型 (Principal/Engineer/Reviewer)
created_at: '2026-02-06T09:43:50'
updated_at: '2026-02-06T09:58:33'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0047'
- '#EPIC-0000'
files:
- .monoco/roles/engineer.yaml
- .monoco/roles/principal.yaml
- .monoco/roles/reviewer.yaml
- .monoco/roles/role-manager.yaml
- .monoco/roles/role-planner.yaml
- AGENTS.md
- GEMINI.md
- Issues/Chores/closed/CHORE-0042-unify-branch-system-terminology-to-trunk-branch.md
- Issues/Chores/closed/CHORE-0045-refactor-project-structure-to-src-layout.md
- Issues/Chores/closed/CHORE-0048-配置更新-默认-agent-provider-修改为-claude-p.md
- Issues/Chores/open/CHORE-0043-重构-open-和-close-命令以支持完整的生命周期钩子.md
- Issues/Chores/open/CHORE-0046-架构重构-agent-session-职责拆分与生命周期管理.md
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Features/closed/FEAT-0184-document-principles-of-agentic-system.md
- Issues/Features/open/FEAT-0187-govern-references-directory-structure-and-implemen.md
- Memos/2026-02-06_Monoco_Daemon_Architecture_Evaluation.md
- src/monoco/core/automation/handlers.py
- src/monoco/core/scheduler/base.py
- src/monoco/core/scheduler/engines.py
- src/monoco/core/skill_framework.py
- src/monoco/features/agent/models.py
- src/monoco/features/agent/resources/en/skills/engineer/SKILL.md
- src/monoco/features/agent/resources/en/skills/monoco_role_manager/SKILL.md
- src/monoco/features/agent/resources/en/skills/monoco_role_planner/SKILL.md
- src/monoco/features/agent/resources/en/skills/reviewer/SKILL.md
- src/monoco/features/agent/resources/zh/skills/engineer/SKILL.md
- src/monoco/features/agent/resources/zh/skills/monoco_role_manager/SKILL.md
- src/monoco/features/agent/resources/zh/skills/monoco_role_planner/SKILL.md
- src/monoco/features/agent/resources/zh/skills/principal/SKILL.md
- src/monoco/features/agent/resources/zh/skills/reviewer/SKILL.md
- src/monoco/features/agent/worker.py
- src/monoco/features/im/core.py
criticality: low
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-06T09:43:50'
isolation:
  type: branch
  ref: CHORE-0047-角色重命名-收缩为三角色模型-principal-engineer-reviewer
  created_at: '2026-02-06T09:55:45'
---

## CHORE-0047: 角色重命名：收缩为三角色模型 (Principal/Engineer/Reviewer)

## Objective

将 Monoco 角色模型正式收缩为三角色制（Principal, Engineer, Reviewer），消除旧架构中 `Planner` 和 `Manager` 的残留引用，确保角色注入链路的语意一致性。

## Acceptance Criteria

- [ ] 全局源代码搜索不再出现 `Planner` 和 `Manager` 作为角色逻辑关键字。
- [ ] `worker.py` 中针对 `Planner` 的硬编码特殊分支被移除或重构至 `Principal`。
- [ ] `defaults.py` 中的内置角色定义已更新为三角色模型。
- [ ] `.monoco/roles/` 目录下的文件名及其内部 `name` 字段已去重 `role-` 前缀。
- [ ] `skills/` 目录下的文件夹已去重 `monoco_role_` 前缀，命名为 `principal`, `engineer`, `reviewer`。
- [ ] 角色技能 (Skills) 与代码中的角色名称完全匹配。

## Technical Tasks

- [ ] **代码清理**:
  - [ ] 替换 `src/monoco/features/agent/worker.py` 中的 `Planner` 引用。
  - [ ] 替换 `src/monoco/features/agent/models.py` 中的示例与字段描述。
  - [ ] 更新 `src/monoco/features/agent/defaults.py` 为新角色模型。
- [ ] **配置目录清理**:
  - [ ] 重命名 `.monoco/roles/` 目录下的文件，移除 `role-` 前缀。
  - [ ] 移除旧的 `manager.yaml` 和 `planner.yaml`，合并为 `principal.yaml`。
  - [ ] 更新 YAML 内部的 `name` 字段，去除 `role-` 前缀。
- [ ] **技能目录清理**:
  - [ ] 将 `src/monoco/features/agent/resources/*/skills/` 下的文件夹由 `monoco_role_xxx` 重命名为 `xxx`。
- [ ] **自动化逻辑同步**:
  - [ ] 检查 `src/monoco/core/automation/handlers.py` 确保角色字符串正确。
- [ ] **文档与示例更新**:
  - [ ] 更新 `AGENTS.md` 等文档中的角色描述。

## Review Comments

<!-- Required for Review/Done stage. Record review feedback here. -->
