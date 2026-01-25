---
id: EPIC-0020
uid: gitea-idp-01
type: epic
status: open
stage: draft
title: Local IDP Integration (Gitea Container)
created_at: '2026-01-25T16:35:00'
updated_at: '2026-01-25T16:35:00'
solution: null
dependencies: []
related: []
domains:
  - backend.devops
  - infrastructure.container
tags:
  - '#EPIC-0020'
files: []
---

## EPIC-0020: [Internal] Establish Local IDP Workflow (Dogfooding)

## 目标

在 Monoco 项目自身的开发中，探索并建立基于本地 Gitea 的 **"Shadow Remote"** 工作流。
**注意**: 这目前是 Monoco 组织的内部开发规范实验，**暂不**作为 Toolkit 的 CLI 功能发布。待成熟验证后，再考虑下放至 Toolkit。

**核心价值**:
1.  **隔离噪音**: 避免 Agent 开发 Monoco 自身时产生的噪音污染 IndenScale/Monoco 主仓库。
2.  **流程验证**: 通过 Dogfooding 验证 "Dual-Remote" 架构在 Agent Native 开发中的可行性。

## 架构：Dual-Remote Strategy (Experiment)

- **Remote `origin`**: Github (Source of Truth).
- **Remote `sandbox`**: Localhost Gitea (Agent Playground).

## 验收标准

- [ ] 在项目根目录提供一份 `infra/docker-compose.gitea.yml` 用于手动启动本地环境。
- [ ] 在 `CONTRIBUTING.md` 或 `GEMINI.md` 中记录 "Agent Session with Local IDP" 的操作规范。
- [ ] 验证 Agent 能否配置并推送到 `sandbox` remote。

## 初步任务分解

- [ ] **Infra**: 编写项目级 `docker-compose.yml` (不打包进 Python Package)。
- [ ] **Docs**: 撰写内部开发规范文档，定义如何连接本地 Gitea。
- [ ] **Pilot**: 进行一次模拟的 Agent 开发 Session，完全走 Local Remote 流程。

## Review Comments

- 这是一个 "Process" 类 Epic，不涉及 Toolkit 自身代码变更。
- 重点在于形成规范和文档。
