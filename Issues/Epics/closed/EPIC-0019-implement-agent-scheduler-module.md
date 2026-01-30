---
id: EPIC-0019
uid: '638912'
type: epic
status: closed
stage: done
title: Implement Agent Scheduler Module
created_at: '2026-01-24T18:45:05'
opened_at: '2026-01-24T18:45:05'
updated_at: '2026-01-24T18:45:05'
solution: implemented
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#EPIC-0019'
files: []
parent: EPIC-0000
progress: 2/2
files_count: 1
---

## EPIC-0019: Implement Agent Scheduler Module

## Objective
作为 ARE (智能体可靠性工程) 的“控制平面”，实现 Agent Scheduler 模块。
它作为一个轻量级的调度器，协调 Agent (计算资源) 与 Issue (任务单元)，在确保生命周期管理稳健的同时实现自主执行。
基于 `RFC/agent-scheduler-design.md` 设计。

## Acceptance Criteria
- [x] **Worker 模板**: 已实现，并重构为标准的 Role 系统 (Planner/Builder/Reviewer/Merger/Coroner/Manager)。
- [x] **Session 管理**: 已实现，分离为 `monoco agent session` 指令集。
- [x] **CLI 接口**: 已实现，并在 `FEAT-0118` 中完成了结构化重构。
- [x] **可靠性**: 已实现，Coroner 角色负责尸检 (Autopsy) 逻辑，整合入 Session 管理。

## Technical Tasks
- [x] FEAT-0097: Worker Management & Role Templates (Worker 管理与角色模板)
- [x] FEAT-0098: Session Management & Persistent History (Session 管理与持久化历史)
- [x] FEAT-0099: Scheduler Core Scheduling Logic & CLI (核心调度逻辑与 CLI)
- [x] FEAT-0100: Scheduler Reliability Engineering (Apoptosis & Recovery) (可靠性工程：凋亡与恢复)
- [x] FEAT-0118: Refactor Agent CLI to Role-Session Structured Mode (结构化重构)

## Review Comments
- 2026-01-30:
  - 该 Epic 的原始设计（基于早期 Scheduler 设计）在执行过程中发生了重要的架构演进。
  - 核心能力（Worker 模板、Session 管理、可靠性）已全部交付，但展现形式从单一的“调度器”精炼为更符合 Agent Native 哲学的 “Role-Session” 分离模式。
  - 通过 `FEAT-0118` 完成了最终的 CLI 结构化闭环，确立了以 `agent session` 和 `agent role` 为核心的新秩序。
  - 尽管实现路径与 RFC 初始草案略有出入，但业务价值已超额交付。标记为 `implemented` 并结项。

