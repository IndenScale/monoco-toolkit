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
progress: 5/8
files_count: 0
---

## EPIC-0025: Monoco Daemon Orchestrator

> **Narrative Epic**: Agent 调度与编排的长期叙事

## 目标 (Objective)
构建 Monoco 的守护进程（Daemon）与编排层（Orchestration Layer），使其从被动工具集进化为主动运行的 Agent 操作系统内核。
本 Epic 将实现 "Mailroom -> Daemon Loop -> HITP" 的完整自动化闭环，支持非阻塞的轻量级二进制解析、基于生命周期的 Agent 调度、以及明确的人机协作（HITP）关卡。

## 验收标准 (Acceptance Criteria)
- [ ] **Mailroom Pipeline**: 能够通过环境感知的适配器处理二进制文件（Office/PDF），利用“截图 + 多模态 API”将其转换为标准格式并投递给 Agent。
- [ ] **Daemon Core**: 实现 "监听 -> 调度 -> 销毁 -> 尸检" 的 Agent 生命周期闭环。
- [ ] **Notification Connectors**: 集成 CI/CD (GitHub Actions) 实现非阻塞的外部通知（Email/IM）。
- [ ] **HITP Gateways**: 在通过 IDE/WebUI 提供明确的三段式人工确认（Confirm Plan -> Merge Code -> Push Remote）。

## 技术任务 (Technical Tasks)

### Phase 1: The Artifact Ecosystem & Mailroom (Ingestion Layer)
> 建立产物管理基础设施与轻量化文档接入。
> Mindset: Infrastructure First -> Skill Empowerment -> Automated Implementation.

- [ ] **FEAT-0151**: Monoco Artifact Core - 实现全局 CAS 存储与项目元数据注册表 (`manifest.jsonl`)。
- [ ] **FEAT-0152**: Monoco Artifact Skills - 定义多模态文档处理的 Agent SOP 与环境自适应指南。
- [ ] **FEAT-0153**: Monoco Mailroom Automation - 实现自动化工具链探测与非阻塞式 Binary Ingestion。
- [ ] **FEAT-VLM-Protocol**: 标准化 Mailroom 输出与 Kimi/Gemini CLI 多模态协议的对接。

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
