---
id: FEAT-0134
uid: f0e1d2
type: feature
status: closed
stage: done
title: Monoco Cockpit - Settings Page Implementation
created_at: '2026-02-01T00:59:12'
updated_at: '2026-02-02T12:11:13'
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
files:
- Issues/Features/open/FEAT-0138-implement-agent-session-persistence.md
- extensions/vscode/client/src/cockpit/components/CapabilitiesPanel.tsx
- extensions/vscode/client/src/cockpit/components/CliPreview.tsx
- extensions/vscode/client/src/cockpit/components/CulturePanel.tsx
- extensions/vscode/client/src/cockpit/components/RuntimePanel.tsx
- extensions/vscode/client/src/cockpit/components/index.ts
- extensions/vscode/client/src/cockpit/hooks/index.ts
- extensions/vscode/client/src/cockpit/hooks/useCockpitSettings.ts
- extensions/vscode/client/src/cockpit/hooks/useVSCodeApi.ts
- extensions/vscode/client/src/cockpit/index.tsx
- extensions/vscode/client/src/cockpit/types/config.ts
- extensions/vscode/client/src/cockpit/types/index.ts
- extensions/vscode/client/src/cockpit/types/messages.ts
- extensions/vscode/client/src/cockpit/views/CockpitApp.tsx
- extensions/vscode/client/src/cockpit/views/index.ts
criticality: medium
opened_at: '2026-02-01T00:59:12'
closed_at: '2026-02-02T12:11:13'
solution: implemented
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

- [x] 设计 Cockpit 布局，强调 "Agent-First" 的视觉层级。
- [x] 实现 **Runtime (Kernel/Persona)** 配置面板。
- [x] 实现 **Capabilities (Skills/MCP)** 配置面板。
- [x] 实现 **Culture (Language/Tone)** 配置面板。
- [x] 开发配置转换适配器 (Adapter)，将 UI 选项映射为 CLI 参数。
- [x] 实现配置持久化。

### 实现详情

#### 文件结构
```
extensions/vscode/client/src/cockpit/
├── CockpitProvider.ts          # VS Code Webview Provider
├── index.tsx                   # React 应用入口
├── index.html                  # HTML 模板
├── components/
│   ├── RuntimePanel.tsx        # Agent Runtime 配置面板
│   ├── CapabilitiesPanel.tsx   # Capabilities 配置面板
│   ├── CulturePanel.tsx        # Culture 配置面板
│   ├── CliPreview.tsx          # CLI 参数预览
│   └── index.ts
├── hooks/
│   ├── useVSCodeApi.ts         # VS Code API Hook
│   ├── useCockpitSettings.ts   # 设置状态管理 Hook
│   └── index.ts
├── types/
│   ├── config.ts               # 配置类型定义
│   ├── messages.ts             # 消息类型定义
│   └── index.ts
├── styles/
│   └── cockpit.css             # 样式文件
└── views/
    ├── CockpitApp.tsx          # 主应用组件
    └── index.ts
```

#### 新增依赖
- `@vscode/webview-ui-toolkit`: VS Code Webview UI 组件库
- `react`: React 框架
- `react-dom`: React DOM 渲染
- `@types/react`: React TypeScript 类型
- `@types/react-dom`: React DOM TypeScript 类型
- `esbuild`: 构建工具

#### 新增命令
- `monoco.openCockpit`: 打开 Monoco Cockpit 设置面板

#### 新增配置项
- `monoco.cockpit.runtime.provider`: Agent Provider
- `monoco.cockpit.runtime.role`: Agent Role
- `monoco.cockpit.runtime.autonomy.level`: Autonomy Level
- `monoco.cockpit.runtime.autonomy.persistence`: Persistence Scope
- `monoco.cockpit.capabilities.skills.directory`: Skills Directory
- `monoco.cockpit.capabilities.skills.sets`: Enabled Skills
- `monoco.cockpit.capabilities.systemAccess.*`: System Access Settings
- `monoco.cockpit.culture.*`: Culture Settings

## Review Comments

*Implementation completed. Ready for review.*
