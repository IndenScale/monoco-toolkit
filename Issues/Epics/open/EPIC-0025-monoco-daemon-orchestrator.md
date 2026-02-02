---
id: EPIC-0025
uid: d7a8f9
type: epic
status: open
stage: doing
title: Monoco Daemon Orchestrator
created_at: '2026-02-01T00:18:00'
updated_at: '2026-02-01T00:18:00'
opened_at: '2026-02-01T00:18:00'
priority: high
owner: IndenScale
parent: EPIC-0000
dependencies: []
related:
- FEAT-0149
domains:
- AgentEmpowerment
files: []
tags:
- '#EPIC-0000'
- '#EPIC-0025'
- '#FEAT-0149'
- '#orchestrator'
- '#daemon'
- narrative
criticality: high
progress: 2/8
files_count: 0
---

## EPIC-0025: Monoco Daemon Orchestrator

> **Narrative Epic**: Agent 调度与编排的长期叙事

## 目标 (Objective)
构建 Monoco 的守护进程（Daemon）与编排层（Orchestration Layer），使其从被动工具集进化为主动运行的 Agent 操作系统内核。
本 Epic 将实现 "Mailroom -> Daemon Loop -> HITP" 的完整自动化闭环，支持非阻塞的二进制解析、基于生命周期的 Agent 调度、以及明确的人机协作（HITP）关卡。

## 验收标准 (Acceptance Criteria)
- [ ] **Mailroom Pipeline**: 能够异步处理二进制文件（PDF/Image/Audio），将其转换为标准 Markdown + Assets 格式并投递到 Inbox。
- [ ] **Daemon Core**: 实现 "监听 -> 调度 -> 销毁 -> 尸检" 的 Agent 生命周期闭环。
- [ ] **Notification Connectors**: 集成 CI/CD (GitHub Actions) 实现非阻塞的外部通知（Email/IM）。
- [ ] **HITP Gateways**: 在通过 IDE/WebUI 提供明确的三段式人工确认（Confirm Plan -> Merge Code -> Push Remote）。

## 技术任务 (Technical Tasks)

### Phase 1: The Mailroom (Ingestion Layer)
> 解决 "非阻塞的二进制文件解析与处理管道"

- [ ] **FEAT-Mailroom-Service**: 设计独立的 Mailroom 服务/Watcher，监听 `Inbox/Dropzone`。
- [ ] **FEAT-Binary-Adapters**: 集成 MinerU (Docs), FFmpeg (Media) 等工具的转换适配器。
- [ ] **FEAT-Async-Pipeline**: 实现基于文件系统的异步队列机制，解析完成后回调 Daemon。

### Phase 2: Notification Connectors (Output Layer)
> 解决 "运行结束后对通知的集成"

- [ ] **FEAT-Notification-Actions**: 封装 GitHub Actions / CI Steps 用于发送通知。
- [ ] **FEAT-Event-Emitters**: 在 Monoco Daemon 中实现事件发射器，触发 CI Pipelines。

### Phase 3: Daemon Core (Orchestration Layer)
> 解决 "对 issue 和 memo 的监听、调度、尸检"

- [ ] **FEAT-Inbox-Watcher**: 监听 Memo Inbox 变更，触发 Architect Agent。
- [ ] **FEAT-Agent-Scheduler**: 实现 Agent 进程的生命周期管理（Spawn, Monitor, Timeout, Kill）。
- [ ] **FEAT-Autopsy-Protocol**: 在 Agent 会话结束（成功/失败/超时）后，自动收集 Logs/Context 并在 Memo 中生成 "尸检报告"。
- [ ] **FEAT-Feedback-Loop**: 将尸检结果回写到 Knowledge Base 或新的 Issue。
- [ ] **FEAT-Hook-System**: 实现 Monoco Native Hook System，支持事件总线和生命周期钩子 (详见 FEAT-0149)。

### Phase 4: HITP Protocols (Interaction Layer)
> 解决 "HITP: Issue 确认/微调 -> 合并修改 -> 推送远程"

- [ ] **FEAT-HITP-Interface**: 标准化 "Plan Review" 和 "Code Review" 的交互协议。
- [ ] **FEAT-Gateway-Confirm**: 实现 Issue/Plan 阶段的人工确认关卡 (Approve to Implement)。
- [ ] **FEAT-Gateway-Merge**: 实现 Code/PR 阶段的人工确认关卡 (Approve to Merge)。
- [ ] **FEAT-Gateway-Push**: 实现 Deployment 阶段的人工确认关卡 (Approve to Push)。
- [ ] **FEAT-UI-Integration**: 适配 VSCode Client 和 Web Console 支持上述 HITP 操作。

## Review Comments
*No comments yet.*
