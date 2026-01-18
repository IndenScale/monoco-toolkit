# Monoco Toolkit

[![Version](https://img.shields.io/pypi/v/monoco-toolkit)](https://pypi.org/project/monoco-toolkit/)
[![License](https://img.shields.io/github/license/IndenScale/Monoco)](LICENSE)

> **面向 Agentic Engineering (智能体工程) 的核心操作系统。**
>
> 将 AI Agent 锚定在确定性的工作流中。把模糊的“对话”转化为结构化、可验证、可交付的工程单元。

---

## ⚡️ 为什么选择 Monoco?

在 LLM 时代，瓶颈不再是**智能**，而是**控制**。

生成代码很容易，但要管理数以千计的 Agent 生成任务、验证其产出、并维护项目状态的一致性却非常困难。**Monoco** 是连接原始 AI 算力与严谨工程纪律之间的控制平面。

Monoco 掌管开发过程中的 **"BizOps 逻辑"**，让你在一个统一的、版本控制的环境中编排人类与 AI 的协作。

## 🌟 核心特性

### 1. Issue as Code (任务即代码)

像管理代码一样管理你的项目任务。

- **Markdown 原生**: 所有的任务 (Epic, Feature, Chore) 都以结构化的 Markdown 文件存储在仓库中。
- **Git 驱动**: 将你的路线图纳入版本控制。通过 Pull Request 审查需求变更。
- **统一上下文**: 为 AI Agent 提供标准化的、无幻觉的状态表达。

### 2. 智能体驾驶舱 (VS Code 扩展)

拒绝上下文切换。直接在编辑器中管理完整的 Agent 工作流。

- **原生看板 (Kanban)**: 无需离开 VS Code 即可可视化并拖拽流转任务。
- **层级树视图**: 从顶层的宏大叙事 (Epic) 逐级钻取至原子的实现任务 (Task)。
- **智能体绑定**: 将特定的 Agent Provider (Gemini, Claude 等) 绑定到具体的任务上下文中。

### 3. 可追溯的执行

- **确定性状态机**: 每个任务都遵循严格的生命周期 (提议 -> 批准 -> 进行中 -> 审查 -> 完成)。
- **审计追踪**: Agent 的行为与决策直接记录在任务文件中。
- **健全性检查**: 内置 Linter 确保任务定义在执行前是完整且合法的。

## 🚀 快速开始

### 安装

Monoco 作为一个 Python CLI 工具发布。

```bash
pip install monoco-toolkit
```

### 初始化

将任意目录转化为 Monoco 工作空间。

```bash
monoco init
```

### 基本工作流

1.  **计划**: 创建一个新的功能需求。
    ```bash
    monoco issue create feature -t "实现深色模式"
    ```
2.  **编辑**: 在生成的 Markdown 文件中细化需求。
3.  **可视化**: 通过 VS Code 或 CLI 打开看板。
    ```bash
    # 启动本地服务
    monoco serve
    ```

## 📦 VS Code 扩展

**Monoco VS Code Extension** 是工具套件的主要可视化界面。

- **市场安装**: 搜索 `Monoco`.
- **快捷键**: `Cmd+Shift+P` -> `Monoco: Open Kanban Board`.

## 🛠️ 技术栈与架构

- **核心**: Python (CLI & 逻辑层)
- **扩展**: TypeScript (VS Code 客户端 & LSP)
- **数据**: 本地文件系统 (Markdown/YAML)

## 🤝 贡献指南

Monoco 为社区而生。我们欢迎对核心 CLI 和 VS Code 扩展的贡献。

## 📄 开源协议

MIT © [IndenScale](https://github.com/IndenScale)
