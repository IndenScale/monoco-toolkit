---
id: CHORE-0017
uid: eb92ec
type: chore
status: closed
stage: done
title: Update README Workflow to Agent-First
created_at: '2026-01-26T01:05:52'
opened_at: '2026-01-26T01:05:52'
updated_at: '2026-01-26T01:06:42'
closed_at: '2026-01-26T01:06:42'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0017'
files: []
---

## CHORE-0017: Update README Workflow to Agent-First

## Objective
Update the "Engineering Loop" section in READMEs to reflect the Agent-First workflow (Chat -> Plan -> Build -> Ship) instead of manual CLI usage. The user shouldn't need to learn CLI APIs for daily work.

## Acceptance Criteria
- [x] README.md Step 4 simplified to Agent Interaction.
- [x] README_ZH.md Step 4 simplified to Agent Interaction.
- [x] CLI commands removed from the execution loop description.

## Technical Tasks
- [x] Rewrite "The Engineering Loop" in `Toolkit/README.md`.
- [x] Rewrite "工程闭环" in `Toolkit/README_ZH.md`.

## Review Comments
- Updated the documentation to emphasize that the Agent acts as the DevOps engineer, handling the underlying CLI commands.
- The flow is now: Chat -> Plan (Ticket) -> Review -> Build (Branch/Code) -> Ship (Merge/Close).
