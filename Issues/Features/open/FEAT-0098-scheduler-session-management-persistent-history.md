---
id: FEAT-0098
uid: 0715b6
type: feature
status: open
stage: doing
title: 'Scheduler: Session Management & Persistent History'
created_at: '2026-01-24T18:45:12'
opened_at: '2026-01-24T18:45:12'
updated_at: '2026-01-24T18:52:31'
isolation:
  type: branch
  ref: feat/feat-0098-scheduler-session-management-persistent-history
  created_at: '2026-01-24T18:51:34'
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0098'
files:
- Issues/Epics/open/EPIC-0019-implement-agent-scheduler-module.md
- Issues/Features/open/FEAT-0097-scheduler-worker-management-role-templates.md
- Issues/Features/open/FEAT-0098-scheduler-session-management-persistent-history.md
- Issues/Features/open/FEAT-0099-scheduler-core-scheduling-logic-cli.md
- Issues/Features/open/FEAT-0100-scheduler-reliability-engineering-apoptosis-recove.md
- monoco/features/scheduler/__init__.py
- monoco/features/scheduler/config.py
- monoco/features/scheduler/defaults.py
- monoco/features/scheduler/manager.py
- monoco/features/scheduler/models.py
- monoco/features/scheduler/session.py
- monoco/features/scheduler/worker.py
- tests/features/test_scheduler.py
- tests/features/test_session.py
---

## FEAT-0098: Scheduler: Session Management & Persistent History

## Objective
Implement the `Session` object and its lifecycle management. A Session represents a runtime instance of a Worker working on a Task. It must handle state transitions (Pending -> Running -> Suspended -> Terminated) and strictly persist context/history via Git commits where appropriate, ensuring "Ephemeral Sessions".

## Acceptance Criteria
- [x] **Session Model**: Class representing a session with state (Status, Worker, IssueID, Git Branch).
- [x] **Lifecycle**: Methods to Start, Suspend, Resume, and Terminate sessions.
- [x] **Git Integration**: Associate a unique git branch per session (or reuse existing feature branch).
- [x] **History**: Ability to read back session history (though strictly logs might be a separate concern, session metadata persistence is key).
- [x] **Persistence**: Session state should be recoverable (e.g., if the daemon restarts, we know what sessions were active). *Note: For MVP, in-memory with file-backed metadata is sufficient.*

## Technical Tasks
- [x] Define `Session` class (`monoco/features/scheduler/session.py`).
- [x] Implement `SessionManager` to track active sessions (`monoco/features/scheduler/manager.py`).
- [x] Implement Git context isolation (ensure worker runs in correct branch).
- [x] Implement state transitions:
    - [x] `start()`: checkout branch, spawn worker.
    - [x] `suspend()`: stop worker, save state (if any).
    - [x] `resume()`: restore state, restart worker.
    - [x] `terminate()`: clean up.
- [x] Add unit tests for session lifecycle.

## Review Comments
- Self-review: Implemented Session, RuntimeSession, and SessionManager. Added basic unit tests for lifecycle and management. Git integration is simulated via branch naming in MVP. Persistence currently in-memory/simulated, needs real persistence layer in future.
