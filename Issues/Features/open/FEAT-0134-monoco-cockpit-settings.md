---
type: Feature
title: Monoco Cockpit - Settings Page Implementation
status: open
priority: high
owner: IndenScale
labels: [vscode-extension, ui, configuration, cockpit]
---

## FEAT-0134: Monoco Cockpit - Settings Page Implementation

## FEAT-0134: Monoco Cockpit - 设置页面实现

### 背景

目前的 Monoco VS Code 扩展缺乏集中的配置界面。用户必须通过 JSON 或 CLI 参数手动配置设置。为了改善用户体验并符合 "Monoco Cockpit"（Monoco 驾驶舱）的愿景，我们需要一个专门的设置 Webview，作为智能体团队的 "任务控制中心"。

### 目标

为 Monoco VS Code 扩展实现一个全面的设置 Webview（驾驶舱），用于管理 Agent 运行配置、上下文与知识以及文化设置。该界面将作为 `monoco run` 参数和环境变量的可视化构建器。

### 功能需求

#### 1. 运行配置 (Runtime Profile) - 执行层
管理标准的 `monoco run` CLI 参数：
- **模型选择 (Model Selection)**：允许指定 LLM 模型 ID（如 `moonshot-v1-128k`, `claude-3-5-sonnet`）。
- **思考模式 (Thinking Mode)**：开启深度思考（思维链）的开关。
- **Agent 人设 (Agent Persona)**：选择内置或自定义的 Agent 人设（如 `default`, `architect`）。
- **安全限制 (Safety Limits)**：
  - **批准模式**：在手动批准和 YOLO 模式（自动批准）之间切换。
  - **步数限制**：配置 `--max-steps-per-turn`。
  - **重试限制**：配置 `--max-retries-per-step`。

#### 2. 上下文与知识 (Context & Knowledge) - 策略层
管理资源路径和知识注入：
- **技能策略 (Skills Strategy)**：配置 `--skills-dir` 以指向本地自定义技能目录。
- **MCP 集成 (MCP Integration)**：配置 `--mcp-config-file` 以连接外部工具。
- **上下文管理 (Context Management)**：可视化选择器，用于切换哪些 `.monoco/*.md` 上下文文件被注入到 Agent 的上下文窗口中。

#### 3. 文化设置 (Cultural Settings) - 文化层
管理语言和行为策略（通过环境变量）：
- **思考语言 (Thinking Language)**：Agent 内部推理使用的语言（建议使用英语）。
- **沟通语言 (Communication Language)**：Agent 与用户交互使用的语言（如中文）。
- **角色定义 (Role Definition)**：覆盖特定角色的 System Prompt。

### 技术实现

- **UI 框架**：使用 React 配合 VS Code Webview UI Toolkit，以保持一致的视觉体验。
- **状态管理**：将配置持久化到工作区设置 (`.vscode/settings.json`) 或专用的 `.monoco/config.yaml`。
- **集成**：扩展的命令注册表需要在生成 `monoco` CLI 命令时读取这些设置。

### 检查清单

- [ ] 设计设置 Webview 布局（标签页或分栏视图）。
- [ ] 实现 **Intelligence (运行配置)** 部分的 UI 和逻辑。
- [ ] 实现 **Strategy (上下文与知识)** 部分的 UI 和逻辑。
- [ ] 实现 **Culture (语言与角色)** 部分的 UI 和逻辑。
- [ ] 实现设置的持久化存储/加载层。
- [ ] 更新 `runMonoco` 工具函数以响应该新配置。

## Review Comments

*No comments yet.*
