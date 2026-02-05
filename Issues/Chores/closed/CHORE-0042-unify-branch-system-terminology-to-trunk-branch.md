---
id: CHORE-0042
uid: 0535c3
type: chore
status: closed
stage: done
title: Unify branch system terminology to Trunk-Branch
created_at: '2026-02-05T09:13:43'
updated_at: '2026-02-05T09:38:24'
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
isolation:
  type: branch
  ref: CHORE-0042-unify-branch-system-terminology-to-trunk-branch
  created_at: '2026-02-05T09:35:54'
---

## CHORE-0042: Unify branch system terminology to Trunk-Branch

## Objective
Standardize the terminology for the project's branching strategy, moving from "Main/Working Branch" to the industry-standard "Trunk-Branch" (Trunk-Based Development).

## Acceptance Criteria
- [x] All documentation and system prompts use Trunk-Branch terminology.

## Technical Tasks
- [x] Unify terminology to Trunk-Branch across documentation, resources, and hooks.
- [x] Synchronize root AGENTS.md and GEMINI.md files using `monoco sync`.

## Review Comments
Implemented and verified.
