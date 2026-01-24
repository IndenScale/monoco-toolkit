---
id: FEAT-0097
uid: 73e66e
type: feature
status: open
stage: review
title: 'Scheduler: Worker Management & Role Templates'
created_at: '2026-01-24T18:45:11'
opened_at: '2026-01-24T18:45:11'
updated_at: '2026-01-24T18:50:53'
isolation:
  type: branch
  ref: feat/feat-0097-scheduler-worker-management-role-templates
  created_at: '2026-01-24T18:48:41'
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0097'
files: []
---

## FEAT-0097: Scheduler: Worker Management & Role Templates

## Objective
Implement the foundation of Agent Scheduler: Worker definitions and Role Templates. This allows the system to define different types of agents (Crafter, Builder, Auditor) with specific triggers, goals, and tools, as defined in `RFC/agent-scheduler-design.md`.

## Acceptance Criteria
- [x] **Config Loading**: Support loading role configurations from `.monoco/scheduler.yaml`.
- [x] **Default Roles**: Define default roles (Crafter, Builder, Auditor) if config is missing or as defaults.
- [x] **Worker Model**: Implement `Worker` class in Python (`monoco.features.scheduler.worker`) that encapsulates the role and runtime state.
- [x] **Validation**: Ensure role templates are validated (tools must exist, triggers must be valid).

## Technical Tasks
- [x] Define `RoleTemplate` Pydantic model (`monoco/features/scheduler/models.py`).
- [x] Implement configuration loader allowing overrides from `.monoco/scheduler.yaml` (`monoco/features/scheduler/config.py`).
- [x] Create `Worker` class that instantiates based on a `RoleTemplate` (`monoco/features/scheduler/worker.py`).
- [x] Create default configuration file or constants.
- [x] Add unit tests for loading and worker instantiation.

## Review Comments
- Self-review: Implemented core models, config loader, and basic worker class. Tests passed. Ready for review.
