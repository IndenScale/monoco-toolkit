---
id: FEAT-0140
type: feature
status: open
stage: doing
title: Monoco Daemon Orchestrator
owner: IndenScale
parent: EPIC-0025
priority: high
created_at: '2026-02-01'
tags:
- daemon
- orchestrator
- scheduler
---

## FEAT-0140: Monoco Daemon Orchestrator

> Implement the core Daemon Orchestration Layer as defined in EPIC-0025.

## Context
The Monoco Daemon needs to evolve from a passive service to an active orchestrator that manages the lifecycle of Agents ("Kernel Workers"). This involves monitoring inputs (Inbox), scheduling workers (Engineers, Architects), and handling failures (Autopsy).

## Goals
- **Inbox Watcher**: Monitor `Memos/inbox.md` and trigger Architect when content accumulates.
- **Agent Scheduler**: Manage lifecycle of Agent Sessions (spawn, monitor, kill).
- **Autopsy Protocol**: Automatically analyze failed sessions.
- **Feedback Loop**: Chain execution (Engineer -> Reviewer).

## Implementation Plan
1.  **Enhance Scheduler**: Update `monoco/daemon/scheduler.py` to support more robust polling and state management.
2.  **Implement Policies**: Refine `MemoAccumulationPolicy` and add triggers for other states.
3.  **Refine Apoptosis**: Update `monoco/features/agent/apoptosis.py` to pass context to the Coroner agent.
4.  **Integration**: Ensure `monoco/daemon/app.py` correctly starts and exposes the orchestrator.

## Checklist
- [ ] Refactor `SchedulerService` for better extensibility.
- [ ] Implement `check_inbox_trigger` in Scheduler.
- [ ] Implement `check_handover_trigger` in Scheduler.
- [ ] Enhance `ApoptosisManager` to provide context.
- [ ] Add unit tests for Scheduler logic.

## Review Comments
*No comments yet.*
