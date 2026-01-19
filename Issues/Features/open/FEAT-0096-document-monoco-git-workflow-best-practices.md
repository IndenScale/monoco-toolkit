---
id: FEAT-0096
uid: 382b6b
type: feature
status: open
stage: doing
title: Document Monoco Git Workflow Best Practices
created_at: "2026-01-19T15:46:24"
opened_at: "2026-01-19T15:46:24"
updated_at: 2026-01-19 15:46:28
dependencies: []
related: []
domains: []
tags:
  - "#FEAT-0096"
files: []
isolation:
  type: branch
  ref: feat/feat-0096-document-monoco-git-workflow-best-practices
  path: null
  created_at: "2026-01-19T15:46:28"
---

## FEAT-0096: Document Monoco Git Workflow Best Practices

## Objective

Establish a standard operating procedure (SOP) for integrating Monoco Issue Tracking with Git Workflows. This guide will define the canonical lifecycle: Creation -> Branching -> Implementation -> Validation -> Merging -> Release.

## Acceptance Criteria

- [ ] A new guide `site/src/zh/guide/workflow.md` (and en) is created.
- [ ] The guide covers:
  - Branching strategy (Feature Branch Workflow).
  - Lifecycle mapping (Open -> Doing -> Review -> Closed).
  - Quality Gates (Linting, Tests before commit/push).
- [ ] `site/src/zh/guide/index.md` links to this new workflow guide.

## Technical Tasks

- [ ] Draft `site/src/zh/guide/workflow.md` with "Best Practices" content.
- [ ] Translate to `site/src/en/guide/workflow.md`.
- [ ] Update `site/.vitepress/config.mts` sidebar to include the new page.
- [ ] Add navigation links in `guide/index.md`.

## Review Comments

<!-- Required for Review/Done stage. Record review feedback here. -->
