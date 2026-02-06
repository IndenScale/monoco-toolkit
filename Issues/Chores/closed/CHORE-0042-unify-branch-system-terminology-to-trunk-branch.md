---
id: CHORE-0042
uid: 0535c3
type: chore
status: closed
stage: done
title: Unify branch system terminology to Trunk-Branch
created_at: '2026-02-05T09:13:43'
updated_at: 2026-02-05 09:38:25
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0042'
- '#EPIC-0000'
files:
- AGENTS.md
- CLAUDE.md
- GEMINI.md
- Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
- monoco/core/hooks/builtin/git_cleanup.py
- monoco/features/agent/resources/en/skills/monoco_role_engineer/SKILL.md
- monoco/features/agent/resources/zh/skills/monoco_role_engineer/SKILL.md
- site/src/en/reference/issue/01_structure.md
- site/src/en/reference/issue/02_lifecycle.md
- site/src/zh/reference/issue/02_lifecycle.md
criticality: low
solution: implemented
opened_at: '2026-02-05T09:13:43'
closed_at: '2026-02-05T09:38:24'
---

## CHORE-0042: Unify branch system terminology to Trunk-Branch

## 目标
将项目分支策略术语从 "Main/Working Branch" 统一为行业标准 "Trunk-Branch"（基于主干的开发模式）。

## 验收标准
- [x] 所有文档和系统提示使用 Trunk-Branch 术语。

## 技术任务
- [x] 在文档、资源和钩子中统一使用 Trunk-Branch 术语。
- [x] 使用 `monoco sync` 同步根目录 AGENTS.md 和 GEMINI.md 文件。

## Review Comments
已实现并验证。
