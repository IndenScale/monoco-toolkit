---
id: CHORE-0044
uid: 4ca429
type: chore
status: open
stage: review
title: Rebrand documentation from 'Monoco Toolkit' to 'Monoco'
created_at: '2026-02-05T19:30:29'
updated_at: '2026-02-05T19:34:29'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0044'
- '#EPIC-0000'
files:
- AGENTS.md
- CLAUDE.md
- CONTRIBUTING.md
- GEMINI.md
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- monoco/core/injection.py
- monoco/features/agent/resources/en/AGENTS.md
- monoco/features/agent/resources/en/skills/monoco_role_engineer/SKILL.md
- monoco/features/agent/resources/en/skills/monoco_role_manager/SKILL.md
- monoco/features/agent/resources/en/skills/monoco_role_planner/SKILL.md
- monoco/features/agent/resources/en/skills/monoco_role_reviewer/SKILL.md
- monoco/features/agent/resources/zh/AGENTS.md
- monoco/features/agent/resources/zh/skills/monoco_role_engineer/SKILL.md
- monoco/features/agent/resources/zh/skills/monoco_role_manager/SKILL.md
- monoco/features/agent/resources/zh/skills/monoco_role_planner/SKILL.md
- monoco/features/agent/resources/zh/skills/monoco_role_reviewer/SKILL.md
- monoco/main.py
- pyproject.toml
criticality: low
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-05T19:30:29'
isolation:
  type: branch
  ref: CHORE-0044-rebrand-documentation-from-monoco-toolkit-to-monoc
  created_at: '2026-02-05T19:30:49'
---

## CHORE-0044: Rebrand documentation from 'Monoco Toolkit' to 'Monoco'

## 目标 (Objective)
使系统的命名与 L3 智能体系统定义对齐。移除“Toolkit”后缀，将“Monoco”作为自主发行版/操作系统的正式称呼。

## 验收标准 (Acceptance Criteria)
- [x] `monoco --help` 显示 "Monoco" 而非 "Monoco Toolkit"。
- [x] 核心宪法文件 (`GEMINI.md`, `AGENTS.md`) 使用 "Monoco" 作为主要系统名称。
- [x] `README.md` 和 `CHANGELOG.md` 与品牌保持一致。
- [x] `pyproject.toml` 中的包名 `monoco-toolkit` 保持不变，以避免 CI/CD 失效。

## 技术任务 (Technical Tasks)
- [x] 更新核心宪法：`GEMINI.md`, `CLAUDE.md`, `AGENTS.md`。
- [x] 更新 `monoco/main.py` 中的 CLI 品牌字符串。
- [x] 更新顶层文档：`README.md`, `CONTRIBUTING.md`。
- [x] 更新 `pyproject.toml` 中的 `description` 字段。
- [x] 更新 `monoco/core/injection.py` 中的 `MANAGED_HEADER` 为 `## Monoco`。

## 评审意见 (Review Comments)
无。已完成初步品牌重塑工作。
