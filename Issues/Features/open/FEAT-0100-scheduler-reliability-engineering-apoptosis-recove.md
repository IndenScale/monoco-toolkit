---
id: FEAT-0100
uid: 87a085
type: feature
status: open
stage: draft
title: 'Scheduler: Reliability Engineering (Apoptosis & Recovery)'
created_at: '2026-01-24T18:45:12'
opened_at: '2026-01-24T18:45:12'
updated_at: '2026-01-24T18:45:12'
dependencies: []
related: []
domains: []
tags:
- '#FEAT-0100'
files: []
# parent: <EPIC-ID>   # Optional: Parent Issue ID
# solution: null      # Required for Closed state (implemented, cancelled, etc.)
---

## FEAT-0100: Scheduler: Reliability Engineering (Apoptosis & Recovery)

## Objective
实现“细胞凋亡” (Apoptosis) 和自动恢复机制，以确保 Agent 的可靠性。这是 ARE (Agent Reliability Engineering) 的核心，防止失控的 Agent 消耗过多资源或破坏环境。

## Acceptance Criteria
- [ ] **监控机制**: 实现 Heartbeat 和 Token 消耗监控。
- [ ] **强制终止**: 当检测到异常（如死循环、超时），能够强制 Kill Session。
- [ ] **尸检 (Autopsy)**: 在重置前，自动触发 Coroner Agent 分析失败原因。
- [ ] **自动恢复**: 基于重试策略（如最大3次）重启 Session。
- [ ] **环境回滚**: 每次 Session 结束（尤其是失败时），通过 Git reset 清理工作目录。

## Technical Tasks
- [ ] 在 `Worker` 或 `RuntimeSession` 中添加监控 Hook。
- [ ] 实现 `ApoptosisManager` 处理异常流程。
- [ ] 集成 `git reset --hard` 到恢复逻辑中。
- [ ] 定义 Coroner 的角色模板。
- [ ] 编写测试案例模拟 Agent 失控和恢复。

## Review Comments
<!-- Required for Review/Done stage. Record review feedback here. -->
