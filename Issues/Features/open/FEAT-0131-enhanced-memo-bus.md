---
id: FEAT-0131
uid: b2c3d4
type: feature
status: open
stage: review
title: Enhanced Memo Bus as Feedback Loop
created_at: '2026-02-01T00:56:00'
updated_at: '2026-02-01T01:01:15'
parent: EPIC-0025
dependencies: []
related:
- FEAT-0130
domains:
- IssueTracing
- AgentScheduling
tags:
- '#FEAT-0131'
- '#memo'
- '#feedback-loop'
- '#traceability'
- '#EPIC-0025'
- '#FEAT-0130'
files: []
criticality: high
isolation:
  type: branch
  ref: feat/feat-0131-enhanced-memo-bus-as-feedback-loop
  created_at: '2026-02-01T00:56:00'
---

## FEAT-0131: Enhanced Memo Bus as Feedback Loop

## Objective
将 Memo 系统从简单的 "文本便签" 升级为全功能的 **Agent-Human 反馈总线 (Feedback Bus)**。
Memo 必须具备结构化的元数据能力，准确记录 **谁 (Source)** 在 **什么时候 (Time)** 提出了 **什么 (Content)**，以及这条反馈目前 **被谁追踪 (Traceability)**。
这将成为 Architect Agent 工作的输入源，以及 Autopsy (尸检) 报告的输出地。

## Acceptance Criteria
- [x] **Schema Upgrade**: Memo 存储格式支持元数据：`Author` (提出者), `Source` (来源渠道), `Status` (状态), `Ref` (追踪的 Issue)。
- [x] **Identity Awareness**: CLI/API 在写入 Memo 时自动记录当前操作者身份 (User Name 或 Agent Role)。
- [x] **Traceability**: 支持将 Memo 链接到特定的 Issue (Status: `pending` -> `tracked #ISSUE-ID`)。
- [x] **Filtering**: 支持按作者、状态或关联 Issue 筛选 Memo (e.g., `monoco memo list --status pending`).

## Technical Tasks

### 1. Data Model & Storage Format
- [x] **Design Format**: 采用轻量级 Header 扩展 Markdown 格式。
    ```markdown
    ## [uid] 2026-02-01 12:00:00
    - **From**: IndenScale (User)
    - **Status**: [ ] Pending
    - **Ref**: null
    
    Memo content here...
    ```
- [x] **Refactor Parser**: 更新 `monoco.features.memo.core` 中的解析与序列化逻辑，支持读写这些元数据。

### 2. Traceability Operations
- [x] **Command: Link**: 实现 `monoco memo link <memo_id> <issue_id>`。
    - 动作：更新 Memo 状态为 `[x] Tracked`，记录 `Ref: #ISSUE-ID`。
    - 场景：Architect 将 Memo 转化为 Issue 后自动调用。
- [x] **Command: Resolve**: 实现 `monoco memo resolve <memo_id>` (标记为已处理/无需处理)。

### 3. Integrated Input Channels
- [x] **CLI Metadata**: `monoco memo add` 增加 `--type` (bug/feature/insight) 和 `--source` (默认为 current user) 参数。
- [x] **Agent API**: 供 `Daemon` 和 `Worker` 调用的 Python API，用于写入尸检报告或运行日志。


## Review Comments

- [x] Manual Verification:
  - `monoco memo add`: Verified with Chinese content and force flag.
  - `monoco memo list`: Verified listing with new columns.
  - `monoco memo link`: Verified linking to Issue.
  - `monoco memo resolve`: Verified resolution status.
  - Unit Tests: (Skipped, manual CLI test performed).

