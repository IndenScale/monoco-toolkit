---
id: FEAT-0130
uid: a1b2c3
type: feature
status: open
stage: draft
title: "Daemon Core: Conditional Scheduling Strategy"
parent: EPIC-0025
dependencies: []
related: []
domains:
  - AgentScheduling
files:
  - monoco/daemon/scheduler.py
  - monoco/daemon/triggers.py
  - monoco/features/agent/worker.py
tags:
  - "#FEAT-0130"
  - "#scheduling"
  - "#lifecycle"
  - "#autopsy"
criticality: medium
---

## FEAT-0130: Daemon Core: Conditional Scheduling Strategy

## Objective
细化 Daemon Core 的调度与生命周期管理策略，实现从 "基于事件" 到 "基于条件/阈值" 的智能触发逻辑。
该 Feature 将定义 Architect、Engineer、Reviewer 在不同触发条件下的启动、休眠、销毁以及 "尸检" 流程，确保资源（Token/算力）的高效利用和风险控制。

## Acceptance Criteria
- [ ] **Trigger-Strategy-Architect**: 实现基于 "Memo 堆积量 / 严重性阈值 / CRON" 的 Architect 唤醒机制。
- [ ] **Trigger-Strategy-Engineer**: 实现基于 "Architect 产出 + 严重性分级 + (可选) HITP 确认" 的 Engineer 启动链。
- [ ] **Trigger-Strategy-Reviewer**: 实现 Engineer 完成后的自动 Reviewer 介入。
- [ ] **Trigger-Strategy-MergePush**: 实现基于 HITP 信号的 Merge 和 Push 动作。
- [ ] **Lifecycle-Autopsy**: 实现 Agent 结束后的自动 "尸检" 逻辑，生成报告并回写。

## Technical Tasks

### 1. Trigger Policies (Daemon 唤醒逻辑)
- [ ] **Policy: Memo Accumulation**: 
    - 监听 `Memos/inbox.md`。
    - 规则：当未处理 Memo Count > N (e.g., 5) OR Criticality Score > X 时，唤醒 Architect。
    - 规则：CRON 每日定时唤醒（兜底）。
- [ ] **Policy: Handover**: 
    - 监听 `monoco issue create` 事件。
    - 规则：当 Architect 将 Issue 状态置为 `open` 且 `stage=doing` (需 HITP 确认?) -> 唤醒 Engineer。
    - *注：这里的 HITP 逻辑：Architect 只能 Draft，Human 确认为 Open 后才触发 Engineer*。

### 2. Lifecycle Management (Worker 状态机)
- [ ] **Supervisor**: 实现一个 Daemon 内部的 Supervisor 线程，维护 Worker 状态表。
- [ ] **Auto-Shutdown**:
    - 规则：Worker 闲置超时 (Idle Timeout) -> Suspend/Kill。
    - 规则：Worker 任务超时 (Hard Limit) -> Kill + Autopsy。
- [ ] **Chained Execution**:
    - 实现 `Engineer` -> `Reviewer` 的自动接力。Reviewer 发现问题 -> 重启 Engineer -> 循环 (设置最大重试次数)。

### 3. Autopsy Protocol (尸检协议)
- [ ] Implement `AutopsyService`:
    - 在 Worker 结束 (Exit Code != 0 或 Timeout) 时触发。
    - 收集：最后 N 条 Log，Prompt 快照，Diff 状态。
    - 动作：调用 LLM (Architect Role) 分析死因。
    - 输出：生成一个 `FIX` 类型的 Draft Issue 或更新原 Memo，打上 `#autopsy` 标签。

### 4. Human Gates (HITP Integration)
- [ ] 定义状态流转中的 HITP 锚点：
    - `Draft` -> `Open` (Confirm Plan)
    - `Review` -> `Done` (Confirm Merge)
    - `Done` -> `Released` (Confirm Push)

