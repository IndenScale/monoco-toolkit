---
id: FEAT-0138
uid: 5d2c5f
type: feature
status: open
stage: doing
title: Implement Agent Session Persistence
created_at: '2026-02-01T20:44:08'
updated_at: '2026-02-01T20:49:44'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FEAT-0138'
files: []
criticality: medium
opened_at: '2026-02-01T20:44:08'
---

## FEAT-0138: Implement Agent Session Persistence

## 背景与目标

实现代理会话持久化功能，确保会话状态在系统重启后不会丢失。当前会话信息仅保存在内存中，当守护进程或系统重启时，所有进行中的会话状态都会丢失。本功能需要扩展 Session 模型，添加进程 ID 字段，实现 SessionManager 的持久化存储（加载/保存到 `.monoco/sessions/*.json`），并支持本地（所有者）与远程（观察者）两种模式，确保 Daemon 能够列出由 CLI 子任务创建的会话。

## Objective
<!-- Describe the "Why" and "What" clearly. Focus on value. -->

## Acceptance Criteria
<!-- Define binary conditions for success. -->
- [ ] Criteria 1

## Technical Tasks
<!-- Breakdown into atomic steps. Use nested lists for sub-tasks. -->

- [ ] Update `Session` model to include `pid` field
- [ ] Implement `SessionManager` persistence (Load/Save to `.monoco/sessions/*.json`)
- [ ] Update `RuntimeSession` to support Local (Owner) vs Remote (Observer) modes
- [ ] Ensure `Worker` updates `pid` in Session model
- [ ] Verify Daemon can list sessions created by CLI Sub Task

- [ ] Task 1

## Review Comments


