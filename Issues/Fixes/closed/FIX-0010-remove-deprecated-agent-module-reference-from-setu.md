---
id: FIX-0010
uid: 0f8174
type: fix
status: closed
stage: done
title: Remove deprecated agent module reference from setup
created_at: '2026-01-19T00:37:20'
opened_at: '2026-01-19T00:37:20'
updated_at: '2026-01-19T00:38:05'
closed_at: '2026-01-19T00:38:05'
solution: implemented
dependencies: []
related: []
tags: []
---

## FIX-0010: Remove deprecated agent module reference from setup

## Objective

<!-- Describe the "Why" and "What" clearly. Focus on value. -->

## Acceptance Criteria

<!-- Define binary conditions for success. -->

- [x] Criteria: `monoco init` no longer warns about missing module

## Technical Tasks

- [x] Task: Remove import of `monoco.features.agent.core` from `monoco/core/setup.py`

## Review Comments

<!-- Required for Review/Done stage. Record review feedback here. -->
