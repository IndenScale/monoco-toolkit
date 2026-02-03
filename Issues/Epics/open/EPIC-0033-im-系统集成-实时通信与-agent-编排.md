---
id: EPIC-0033
uid: 3feda2
type: epic
status: open
stage: draft
title: IM 系统集成：实时通信与 Agent 编排
created_at: '2026-02-03T23:23:28'
updated_at: '2026-02-03T23:23:28'
parent: EPIC-0000
dependencies: []
related:
- FEAT-0167
- FEAT-0168
- FEAT-0169
- FEAT-0170
- FEAT-0171
domains:
- CollaborationBus
- AgentEmpowerment
tags:
- '#EPIC-0000'
- '#EPIC-0033'
- '#FEAT-0167'
- '#FEAT-0168'
- '#FEAT-0169'
- '#FEAT-0170'
- '#FEAT-0171'
files: []
criticality: high
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-03T23:23:28'
---

## EPIC-0033: IM 系统集成：实时通信与 Agent 编排

## Objective
构建与飞书、钉钉等 IM 平台的原生集成，实现 IM 作为独立一级抽象（与 Memo 平级），支持双向实时通信和 Agent 流式对话。

### 核心原则
1. **独立抽象**: IM 是与 Issue、Memo、Artifact 平行的一级概念
2. **双向实时**: 支持接收消息和主动回复，区别于 Memo 的单向记录
3. **流式交互**: Agent 可以通过 IM 进行多轮实时对话
4. **平台无关**: 统一抽象层，支持多平台接入

### 与现有系统的关系
```
┌─────────────────────────────────────────────────────────────┐
│                     Monoco System                            │
├───────────────┬───────────────┬───────────────┬─────────────┤
│    Issue      │     Memo      │     IM        │   Artifact  │
│  (工作单元)    │  (个人笔记)    │  (外部通信)    │   (产物)     │
├───────────────┼───────────────┼───────────────┼─────────────┤
│ • 有生命周期  │ • 无生命周期  │ • 会话驱动    │ • 内容寻址   │
│ • 严格结构    │ • 自由格式    │ • 双向实时    │ • 不可变     │
│ • 状态流转    │ • 草稿性质    │ • 流式对话    │ • 多模态     │
└───────────────┴───────────────┴───────────────┴─────────────┘
```

## Acceptance Criteria
- [ ] IM 系统作为独立 Feature 存在，与 Memo 无继承关系
- [ ] 支持飞书、钉钉至少两个平台的接入
- [ ] 实现 IM 消息与 Agent 的实时双向通信
- [ ] 提供 CLI 工具管理 IM 频道和平台连接
- [ ] 支持将 IM 消息显式归档到 Memo 或提升为 Issue

## Technical Tasks
- [ ] FEAT-0167: IM 基础设施 - 核心数据模型与存储
- [ ] FEAT-0168: 飞书平台适配器 - 事件接收与消息发送
- [ ] FEAT-0169: 钉钉平台适配器 - Webhook 与卡片消息
- [ ] FEAT-0170: IM Agent 工作流 - 实时会话与流式响应
- [ ] FEAT-0171: IM CLI 与配置 - 频道管理与平台连接

## Review Comments
