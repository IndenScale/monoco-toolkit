---
id: CHORE-0051
uid: f26a0a
type: chore
status: open
stage: doing
title: 废除项目级 IM，统一使用全局 Mailbox
created_at: '2026-02-10T14:26:12'
updated_at: '2026-02-10T14:45:00'
parent: EPIC-0000
dependencies: []
related:
  - FEAT-0167
  - FEAT-0170
domains:
  - Foundation
tags:
  - '#CHORE-0051'
  - '#EPIC-0000'
  - '#deprecated'
files:
  - Issues/Epics/open/EPIC-0000-Monoco-Toolkit-Root.md
  - Issues/Features/closed/FEAT-0167-im-基础设施-核心数据模型与存储.md
  - Issues/Features/closed/FEAT-0170-im-agent-工作流-实时会话与流式响应.md
  - src/monoco/core/scheduler/events.py
  - src/monoco/core/watcher/__init__.py
  - src/monoco/core/watcher/im.py
criticality: low
solution: implemented
opened_at: '2026-02-10T14:26:12'
isolation:
  type: branch
  ref: CHORE-0051-deprecate-project-level-im-consolidate-to-global-m
  created_at: '2026-02-10T14:26:32'
---

## CHORE-0051: 废除项目级 IM，统一使用全局 Mailbox

## 目标

废除项目级 IM 基础设施 (`.monoco/im/`)，统一使用全局 Mailbox 系统 (`~/.monoco/mailbox/`)。
项目级存储与 Monoco 的全局架构冲突，且功能与 Mailbox 重复。

## 验收标准

- [x] 删除 `src/monoco/core/watcher/im.py`
- [x] 从 `watcher/__init__.py` 移除 IM 导出
- [x] 将 `AgentEventType.IM_*` 替换为 `MAILBOX_*` 事件
- [x] 标记 FEAT-0167 为已废除
- [x] 标记 FEAT-0170 为已废除

## 技术任务

- [x] 删除 IMWatcher 及相关类
- [x] 更新事件类型定义
- [x] 更新文档和 Issue 标记

## 废除说明

### 替代方案

- **存储位置**: `~/.monoco/mailbox/inbound/` (全局)
- **Watcher**: `MailboxInboundWatcher` (计划中)
- **事件**: `MAILBOX_INBOUND_RECEIVED`, `MAILBOX_AGENT_TRIGGER`

### 影响范围

- FEAT-0167: 项目级 IM 基础设施 - 已废除
- FEAT-0170: IM Agent 工作流 - 已废除

## 审查记录
