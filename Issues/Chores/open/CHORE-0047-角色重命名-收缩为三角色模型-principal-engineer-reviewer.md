---
id: CHORE-0047
uid: '697782'
type: chore
status: open
stage: review
title: 角色重命名：收缩为三角色模型 (Principal/Engineer/Reviewer)
created_at: '2026-02-06T09:43:50'
updated_at: '2026-02-06T10:25:01'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0047'
- '#EPIC-0000'
files:
- .github/workflows/publish-pypi.yml
- .monoco/project.yaml
- .monoco/roles/engineer.yaml
- .monoco/roles/principal.yaml
- .monoco/roles/reviewer.yaml
- .monoco/roles/role-manager.yaml
- .monoco/roles/role-planner.yaml
- AGENTS.md
- Archaeology/REPORT_2026_01_08_2026_01_26.md
- Archaeology/REPORT_2026_01_26_01_30.md
- Archaeology/REPORT_2026_01_31_02_01.md
- CHANGELOG.md
- CLAUDE.md
- GEMINI.md
- Issues/Arch/closed/ARCH-0001-hook-system-architecture-strategy.md
- Issues/Chores/closed/CHORE-0027-refactor-issue-architecture-consolidate-epics-and-.md
- Issues/Chores/closed/CHORE-0029-development-archaeology-2026-01-08-to-2026-01-26.md
- Issues/Chores/closed/CHORE-0030-standardize-feature-resource-structure-skill-loade.md
- Issues/Chores/closed/CHORE-0042-unify-branch-system-terminology-to-trunk-branch.md
- Issues/Chores/closed/CHORE-0044-rebrand-documentation-from-monoco-toolkit-to-monoc.md
- Issues/Chores/closed/CHORE-0045-refactor-project-structure-to-src-layout.md
- Issues/Chores/closed/CHORE-0048-配置更新-默认-agent-provider-修改为-claude-p.md
- Issues/Chores/open/CHORE-0043-重构-open-和-close-命令以支持完整的生命周期钩子.md
- Issues/Chores/open/CHORE-0046-架构重构-agent-session-职责拆分与生命周期管理.md
- Issues/Domains/DevEx.md
- Issues/Domains/Foundation.md
- Issues/Domains/IssueSystem.md
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- Issues/Epics/open/EPIC-0027-issue-governance-strategy-2026-q1-establish-govern.md
- Issues/Epics/open/EPIC-0030-developer-experience-tooling.md
- Issues/Features/closed/FEAT-0142-implement-monoco-toolkit-root-structure.md
- Issues/Features/closed/FEAT-0179-治理与简化-skill-体系-role-workflow-融合与-jit-劝导.md
- Issues/Features/closed/FEAT-0184-document-principles-of-agentic-system.md
- Issues/Features/open/FEAT-0187-govern-references-directory-structure-and-implemen.md
- Memos/2026-02-06_Monoco_Daemon_Architecture_Evaluation.md
- TREE.md
- docs/zh/90_Spikes/hooks-system/README.md
- extensions/vscode/README.md
- extensions/vscode/client/src/bootstrap.ts
- mkdocs.yml
- scripts/install.sh
- site/.vitepress/config.mts
- site/package.json
- site/src/en/guide/index.md
- site/src/en/guide/setup/index.md
- site/src/en/guide/workflow.md
- site/src/en/index.md
- site/src/en/meta/Manifesto.md
- site/src/en/meta/process/pypi-implementation-summary.md
- site/src/en/meta/process/pypi-trusted-publishing.md
- site/src/en/reference/architecture.md
- site/src/en/reference/extensions/index.md
- site/src/en/reference/i18n/manual.md
- site/src/en/reference/tools/vscode.md
- site/src/zh/guide/index.md
- site/src/zh/guide/setup/index.md
- site/src/zh/guide/workflow.md
- site/src/zh/index.md
- site/src/zh/meta/Manifesto.md
- site/src/zh/meta/process/pypi-implementation-summary.md
- site/src/zh/meta/process/pypi-trusted-publishing.md
- site/src/zh/reference/architecture.md
- site/src/zh/reference/i18n/manual.md
- site/src/zh/reference/tools/vscode.md
- src/monoco/core/automation/handlers.py
- src/monoco/core/daemon/pid.py
- src/monoco/core/githooks.py
- src/monoco/core/scheduler/base.py
- src/monoco/core/scheduler/engines.py
- src/monoco/core/skill_framework.py
- src/monoco/core/skills.py
- src/monoco/core/sync.py
- src/monoco/features/agent/models.py
- src/monoco/features/agent/resources/en/roles/engineer.yaml
- src/monoco/features/agent/resources/en/roles/principal.yaml
- src/monoco/features/agent/resources/en/roles/reviewer.yaml
- src/monoco/features/agent/resources/en/skills/engineer/SKILL.md
- src/monoco/features/agent/resources/en/skills/monoco_role_manager/SKILL.md
- src/monoco/features/agent/resources/en/skills/monoco_role_planner/SKILL.md
- src/monoco/features/agent/resources/en/skills/reviewer/SKILL.md
- src/monoco/features/agent/resources/zh/roles/engineer.yaml
- src/monoco/features/agent/resources/zh/roles/principal.yaml
- src/monoco/features/agent/resources/zh/roles/reviewer.yaml
- src/monoco/features/agent/resources/zh/skills/engineer/SKILL.md
- src/monoco/features/agent/resources/zh/skills/monoco_role_manager/SKILL.md
- src/monoco/features/agent/resources/zh/skills/monoco_role_planner/SKILL.md
- src/monoco/features/agent/resources/zh/skills/principal/SKILL.md
- src/monoco/features/agent/resources/zh/skills/reviewer/SKILL.md
- src/monoco/features/agent/worker.py
- src/monoco/features/hooks/dispatchers/git_dispatcher.py
- src/monoco/features/im/core.py
- tests/core/test_injector.py
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

- [x] 全局源代码搜索不再出现 `Planner` 和 `Manager` 作为角色逻辑关键字。
- [x] `worker.py` 中针对 `Planner` 的硬编码特殊分支被移除或重构至 `Principal`。
- [x] `defaults.py` 中的内置角色定义已更新为三角色模型。
- [x] `.monoco/roles/` 目录下的文件名及其内部 `name` 字段已去重 `role-` 前缀。
- [x] `skills/` 目录下的文件夹已去重 `monoco_role_` 前缀，命名为 `principal`, `engineer`, `reviewer`。
- [x] 角色技能 (Skills) 与代码中的角色名称完全匹配。

## Technical Tasks

- [x] **代码清理**:
  - [x] 替换 `src/monoco/features/agent/worker.py` 中的 `Planner` 引用。
  - [x] 替换 `src/monoco/features/agent/models.py` 中的示例与字段描述。
  - [x] 更新 `src/monoco/features/agent/defaults.py` 为新角色模型。
- [x] **配置目录清理**:
  - [x] 重命名 `.monoco/roles/` 目录下的文件，移除 `role-` 前缀。
  - [x] 移除旧的 `manager.yaml` 和 `planner.yaml`，合并为 `principal.yaml`。
  - [x] 更新 YAML 内部的 `name` 字段，去除 `role-` 前缀。
- [x] **技能目录清理**:
  - [x] 将 `src/monoco/features/agent/resources/*/skills/` 下的文件夹由 `monoco_role_xxx` 重命名为 `xxx`。
- [x] **自动化逻辑同步**:
  - [x] 检查 `src/monoco/core/automation/handlers.py` 确保角色字符串正确。
- [x] **文档与示例更新**:
  - [x] 更新 `AGENTS.md` 等文档中的角色描述。

## Review Comments

- 2026-02-06: 角色重命名为三角色模型完成（Principal/Engineer/Reviewer）
- Source 侧多语言支持已实现（en/zh）
- monoco sync 自动检测语言并覆盖 target 目录
