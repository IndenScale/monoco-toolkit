---
id: FIX-0008
uid: afa8e7
type: fix
status: closed
stage: done
title: Enable Issue Creation for Orphans
created_at: '2026-01-14T16:57:42'
opened_at: '2026-01-14T16:57:42'
updated_at: '2026-01-14T16:57:47'
closed_at: '2026-01-14T16:57:47'
parent: FEAT-0063
solution: implemented
dependencies: []
related: []
tags: []
---

## FIX-0008: Enable Issue Creation for Orphans

## Objective

Ensure that issues can be created even when they are "orphans" (i.e., do not have a parent Epic).

## Acceptance Criteria

- [x] Orphan issues can be created successfully without errors.

## Technical Tasks

- [x] Allow `parent` to be null during issue creation.

## Review Comments

- [x] Self-Review
