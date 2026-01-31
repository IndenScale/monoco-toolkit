---
id: FEAT-0125
uid: 45f412
type: feature
status: closed
stage: done
title: Agent Logic Timeout
created_at: '2026-01-31T10:45:26'
updated_at: '2026-01-31T16:14:12'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0125'
files:
- monoco/core/config.py
- monoco/features/agent/models.py
- monoco/features/agent/worker.py
- monoco/features/agent/manager.py
- .monoco/workspace.yaml
criticality: medium
opened_at: '2026-01-31T10:45:26'
closed_at: '2026-01-31T16:14:12'
solution: implemented
isolation:
  type: branch
  ref: feat/feat-0125-agent-logic-timeout
  created_at: '2026-01-31T10:52:38'
---

## FEAT-0125: Agent Logic Timeout

## Objective
为 Agent Session 实现应用层级的超时控制机制。针对不支持 `timeout` 参数的后端引擎（如 Gemini, Claude, Kimi CLI），在 Python 进程层面实施监控，防止自动化任务无限期挂起。

## Acceptance Criteria
- [x] `monoco-config` 中增加 `agent.timeout_seconds` 配置项，默认 900秒。
- [x] `RuntimeSession` 或 `Worker` 实现超时监控。
- [x] 超时发生时，能够优雅地终止子进程（SIGTERM/SIGKILL）。
- [x] 超时后 `session.status` 应标记为 `timeout` 或 `failed`。

## Technical Tasks
- [x] **Config**: Update `AgentConfig` model and `workspace.yaml`.
- [x] **Worker Logic**: Implement timeout check in `poll()` and process termination in `stop()`.
- [x] **Verification**: Create a test case to verify timeout behavior (Verified with MockAdapter).

## Review Comments
- Timeout configuration added to core schema and workspace default.
- Worker implementation now tracks `start_at` and checks elapsed time during `poll()`.
- Detached sessions currently rely on the foreground watcher to enforce timeouts (Limitation: detached sessions without a watcher may run until natural exit).
