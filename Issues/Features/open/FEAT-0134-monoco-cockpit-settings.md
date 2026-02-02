---
id: FEAT-0134
uid: f0e1d2
type: feature
status: open
stage: doing
title: Monoco Cockpit - Settings Page Implementation
created_at: '2026-02-01T00:59:12'
updated_at: '2026-02-02T11:19:24'
priority: high
parent: EPIC-0032
dependencies: []
related: []
domains:
- CollaborationBus
tags:
- vscode-extension
- ui
- configuration
- cockpit
- '#EPIC-0032'
- '#FEAT-0134'
files: []
criticality: medium
solution: null # implemented, cancelled, wontfix, duplicate
opened_at: '2026-02-01T00:59:12'
owner: IndenScale
---

## FEAT-0134: Monoco Cockpit - Settings Page Implementation

## FEAT-0134: Monoco Cockpit - 设置页面实现

### 背景

目前的 Monoco VS Code 扩展缺乏集中的配置界面。用户必须通过 JSON 或 CLI 参数手动配置设置。为了改善用户体验并符合 "Monoco Cockpit"（Monoco 驾驶舱）的愿景，我们需要一个专门的设置 Webview，作为智能体团队的 "任务控制中心"。

### 目标

为 Monoco VS Code 扩展实现一个全面的设置 Webview（驾驶舱），用于配置 Agent 运行时、上下文策略以及文化偏好。该界面将屏蔽底层模型细节，通过 "Agent Native" 的概念体系（如 Kernel, Persona, Capability）来管理智能体行为。

### 功能需求

#### 1. 智能体运行时 (Agent Runtime)
管理 Agent 身份与核心能力：
- **Agent Provider (服务商)**：选择驱动 Agent 的后端服务（如 `Kimi`, `Vertex AI` 等），而非底层的 "Model ID"。
- **Agent Role (角色)**：选择 Agent 的岗位（如 `Principal Architect`, `Senior Engineer`, `QA Specialist`）。
- **Autonomy (自主性)**：
  - **Human-in-the-loop**：默认 YOLO 模式（自动批准）。支持切换为 Step-by-step 审批。
  - **Persistence**：默认设置为 **Unlimited (无限)**。Agent 应已被赋予最高权限与最长执行时间。

#### 2. 工具与能力 (Tools & Capabilities)
管理 Agent 可用的工具与环境：
- **Skill Sets (技能组)**：可视化管理 `--skills-dir`，启用/禁用特定技能包（Skills）。
- **System Access (系统访问)**：强调 **Bash-as-Tool** 理念。不使用 MCP (Model Context Protocol)。Agent 直接通过 Shell 访问系统 CLI、文件系统与网络，以实现真正的全能操作。


### 技术实现

- **UI 框架**：使用 React 配合 VS Code Webview UI Toolkit。
- **配置层**：屏蔽 `.vscode/settings.json` 的复杂性，提供语义化的图形配置。
- **抽象层**：在 `monoco-vscode` 端即时转换 "Agent Config" -> "CLI Args"，对用户隐藏底层参数（如 `temperature`, `model_id`）。

### 检查清单

- [ ] 设计 Cockpit 布局，强调 "Agent-First" 的视觉层级。
- [ ] 实现 **Runtime (Kernel/Persona)** 配置面板。
- [ ] 实现 **Capabilities (Skills/MCP)** 配置面板。
- [ ] 实现 **Culture (Language/Tone)** 配置面板。
- [ ] 开发配置转换适配器 (Adapter)，将 UI 选项映射为 CLI 参数。
- [ ] 实现配置持久化。

## Review Comments

*No comments yet.*
