---
id: CHORE-0015
uid: df018a
type: chore
status: open
stage: doing
title: Sync Issue Best Practices to Agent Prompts
created_at: '2026-01-26T00:51:15'
opened_at: '2026-01-26T00:51:15'
updated_at: '2026-01-26T00:52:00'
isolation:
  type: branch
  ref: feat/chore-0015-sync-issue-best-practices-to-agent-prompts
  created_at: '2026-01-26T00:51:25'
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0015'
files:
- Issues/Chores/open/CHORE-0015-sync-issue-best-practices-to-agent-prompts.md
- monoco/features/issue/resources/en/AGENTS.md
- monoco/features/issue/resources/zh/AGENTS.md
---

## CHORE-0015: Sync Issue Best Practices to Agent Prompts

## Objective
Ensure that the Agent Guidance (AGENTS.md) in both English and Chinese accurately reflects the strict Issue Driven Development best practices, specifically the "Issue First" rule and the precise timing for environment cleanup.

## Acceptance Criteria
- [x] English AGENTS.md includes "Issue First" rule.
- [x] English AGENTS.md includes correct prune timing (close only).
- [x] Chinese AGENTS.md includes "Issue First" rule.
- [x] Chinese AGENTS.md includes correct prune timing (close only).

## Technical Tasks

- [x] Update `monoco/features/issue/resources/en/AGENTS.md`
- [x] Update `monoco/features/issue/resources/zh/AGENTS.md`

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
Self-reviewed. Changes align with GEMINI.md core principles.
