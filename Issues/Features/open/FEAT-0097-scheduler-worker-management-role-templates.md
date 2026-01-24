---
id: FEAT-0097
uid: 73e66e
type: feature
status: open
stage: doing
title: 'Scheduler: Worker Management & Role Templates'
created_at: '2026-01-24T18:45:11'
opened_at: '2026-01-24T18:45:11'
updated_at: 2026-01-24 18:48:41
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0097'
files: []
isolation:
  type: branch
  ref: feat/feat-0097-scheduler-worker-management-role-templates
  path: null
  created_at: '2026-01-24T18:48:41'
---

## FEAT-0097: Scheduler: Worker Management & Role Templates

## Objective
Implement the foundation of Agent Scheduler: Worker definitions and Role Templates. This allows the system to define different types of agents (Crafter, Builder, Auditor) with specific triggers, goals, and tools, as defined in `RFC/agent-scheduler-design.md`.

## Acceptance Criteria
- [ ] **Config Loading**: Support loading role configurations from `.monoco/scheduler.yaml`.
- [ ] **Default Roles**: Define default roles (Crafter, Builder, Auditor) if config is missing or as defaults.
- [ ] **Worker Model**: Implement `Worker` class in Python (`monoco.features.scheduler.worker`) that encapsulates the role and runtime state.
- [ ] **Validation**: Ensure role templates are validated (tools must exist, triggers must be valid).

## Technical Tasks
- [ ] Define `RoleTemplate` Pydantic model (`monoco/features/scheduler/models.py`).
- [ ] Implement configuration loader allowing overrides from `.monoco/scheduler.yaml` (`monoco/features/scheduler/config.py`).
- [ ] Create `Worker` class that instantiates based on a `RoleTemplate` (`monoco/features/scheduler/worker.py`).
- [ ] Create default configuration file or constants.
- [ ] Add unit tests for loading and worker instantiation.

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
