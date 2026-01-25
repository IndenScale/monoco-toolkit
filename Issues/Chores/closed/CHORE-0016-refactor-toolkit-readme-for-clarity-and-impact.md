---
id: CHORE-0016
uid: 751c88
type: chore
status: closed
stage: done
title: Refactor Toolkit README for Clarity and Impact
created_at: '2026-01-26T01:01:01'
opened_at: '2026-01-26T01:01:01'
updated_at: '2026-01-26T01:02:38'
closed_at: '2026-01-26T01:02:38'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0016'
files: []
---

## CHORE-0016: Refactor Toolkit README for Clarity and Impact

## Objective
Improve the Toolkit documentation to clearly communicate the value proposition of "Agentic Engineering" vs "Chat", and properly document the `monoco init` and `monoco sync` commands to avoid ambiguity about their redundancy.

## Acceptance Criteria
- [x] README.md updated with clearer value prop.
- [x] README_ZH.md updated with clearer value prop.
- [x] `monoco init` and `monoco sync` documented in Quick Start with correct context.

## Technical Tasks
- [x] Analyze current README and Codebase to verify command usage.
- [x] Update `Toolkit/README.md`.
- [x] Update `Toolkit/README_ZH.md`.

## Review Comments
- Verified that `monoco init` bootstraps the workspace and `monoco sync` injects agent prompts/skills. They are distinct and necessary steps.
- Documentation now emphasizes the "Engineering" aspect over "Chat".
