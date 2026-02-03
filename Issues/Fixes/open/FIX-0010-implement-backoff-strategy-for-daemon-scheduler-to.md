---
id: FIX-0010
uid: fb893d
type: fix
status: open
stage: draft
title: Implement backoff strategy for Daemon scheduler to prevent agent process storm
created_at: '2026-02-03T13:41:19'
updated_at: '2026-02-03T13:41:19'
parent: EPIC-0000
dependencies: []
related: []
domains: []
tags:
- '#EPIC-0000'
- '#FIX-0010'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T13:41:19'
---

## FIX-0010: Implement backoff strategy for Daemon scheduler to prevent agent process storm

## Objective
Daemon 调度器 Handover 策略引发无限 Agent 进程增殖，导致 OOM 崩溃。需增加冷却/退避机制。

## Acceptance Criteria
- [ ] Daemon 调度器在连续启动失败或频繁 Handover 时实施退避策略
- [ ] 包含最大重试次数或冷却时间配置
- [ ] OOM 风险得到缓解

## Technical Tasks
- [ ] 分析当前 Handover 逻辑 (Context: `Post-Mortem` [844f87])
- [ ] 实现指数退避 (Exponential Backoff) 或固定冷却时间
- [ ] 添加相关日志和监控指标

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->