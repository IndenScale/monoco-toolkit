# Monoco Toolkit

[![Version](https://img.shields.io/pypi/v/monoco-toolkit)](https://pypi.org/project/monoco-toolkit/)
[![License](https://img.shields.io/github/license/IndenScale/Monoco)](LICENSE)

> **面向 Agentic Engineering (智能体工程) 的操作系统。**
>
> 拒绝空谈，开始构建。
> Monoco 将模糊的 AI 聊天锚定为确定性、可验证、可交付的工程工作流。

---

## ⚡️ 核心痛点：聊天 (Chat) ≠ 工程 (Engineering)

生成代码很简单。但**工程**——管理依赖、维护状态、质量验证、版本控制——很难。

当今大多数 Agent 工作流都停留在脆弱的“聊天”层面。Monoco 将其转化为严谨的**软件工程流程**。它是 AI Agent 的 "BizOps" 层，确保生成的每一行代码都可追踪、可审查，并与其所属的 Roadmap 保持一致。

## 🌟 核心理念

### 1. 辅助驾驶 (Co-pilot)

**恰到好处的自动化。**
Monoco 旨在屏蔽繁琐的工程细节（如 Git 操作、文件追踪），通过 VS Code 插件提供直观的控制平面。但**控制权永远在用户手中**——Agent 可以建议，但只有你能决定是否合并。

### 2. 工程化实践 (Best Practices)

**植根于 SWE 的硬核规范。**
Monoco 强迫 Agent 遵循 **Issue Driven Development (IDD)** 和标准的 **Git Workflow**。它将资深工程师的经验内化为 Agent 的直觉，确保从需求 (Issue) 到交付 (PR) 的每一步都是合规的。

### 3. 深度自用 (Dogfooding)

**开源决策与过程。**
Monoco 本身就是由 Monoco 构建的。我们相信 "过程即产品" (Process as Product)。因此，我们不仅开源代码，更开源所有的设计决策、Issue 讨论和交互细节，供开发者参考与复盘。

## 🚀 快速开始

### 1. 安装

Monoco 作为一个 Python CLI 工具发布。

```bash
pip install monoco-toolkit
```

### 2. 工作空间初始化

将任意目录转化为 Monoco 工作空间。这将建立 `.monoco` 配置与 `Issues/` 目录结构。

```bash
monoco init
```

### 3. 智能体同步 (关键步骤)

注入 "Monoco 系统神经网络" (System Prompts & Skills) 到你的 Agent 配置文件 (如 `GEMINI.md`, `CLAUDE.md`)。

```bash
monoco sync
```

### 4. 工程闭环 (Agent 协作模式)

在 Monoco 中，不需要你手动运行繁琐的命令。**Agent 就是你的 DevOps 工程师。**

1.  **指令 (Chat)**: 在对话框中告诉 Agent (e.g., _"实现深色模式"_).
2.  **规划 (Plan)**: Agent 进行调查，并创建 Issue Ticket 供你审查。
3.  **构建 (Build)**: 确认后，Agent 自动创建分支、编写代码并提交。
4.  **交付 (Ship)**: 你验收成果。Agent 负责关闭 Issue 并合并分支。

---

## 📦 VS Code 扩展

**Monoco VS Code Extension** 是工具套件的主要可视化界面。

- **快捷键**: `Cmd+Shift+P` -> `Monoco: Open Kanban Board`.

## 🛠️ 技术栈与架构

- **核心**: Python (CLI & 逻辑层)
- **扩展**: TypeScript (VS Code 客户端 & LSP)
- **数据**: 本地文件系统 (Markdown/YAML)

## 🤝 贡献指南

Monoco 为社区而生。我们欢迎对核心 CLI 和 VS Code 扩展的贡献。

## 📄 开源协议

MIT © [IndenScale](https://github.com/IndenScale)
