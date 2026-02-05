---
id: CHORE-0044
uid: 4ca429
type: chore
status: open
stage: doing
title: Rebrand documentation from 'Monoco Toolkit' to 'Monoco'
created_at: '2026-02-05T19:30:29'
updated_at: '2026-02-05T19:30:48'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#CHORE-0044'
- '#EPIC-0000'
files: []
criticality: low
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-05T19:30:29'
---

## CHORE-0044: Rebrand documentation from 'Monoco Toolkit' to 'Monoco'

## Objective
Align the system's naming with its L3 Agentic System definition. The term "Toolkit" implies a passive role, whereas "Monoco" represents the autonomous distribution/OS itself.

## Acceptance Criteria
- [ ] `monoco --help` shows "Monoco" instead of "Monoco Toolkit".
- [ ] Core constitution files (`GEMINI.md`, `AGENTS.md`) use "Monoco" as the primary system name.
- [ ] `README.md` and `CHANGELOG.md` are consistent with the branding.
- [ ] Package name `monoco-toolkit` is preserved in `pyproject.toml` to avoid CI/CD breakage.

## Technical Tasks
- [ ] Update constitutions: `GEMINI.md`, `CLAUDE.md`, `AGENTS.md`.
- [ ] Update CLI branding in `monoco/main.py`.
- [ ] Update high-level docs: `README.md`, `CONTRIBUTING.md`.
- [ ] Update `pyproject.toml` description field.
- [ ] Verify `monoco info` output.

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
