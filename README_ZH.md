# Monoco Distro

[![Version](https://img.shields.io/pypi/v/monoco-toolkit)](https://pypi.org/project/monoco-toolkit/)
[![License](https://img.shields.io/github/license/IndenScale/Monoco)](LICENSE)

> **面向 Agentic Engineering 的无头化操作系统 (Headless OS)。**
>
> Monoco 是 AI Agent 的 **类 Linux 发行版 (Distro)**。
> 它提供了 **包管理器**、**Init 系统** 和 **策略套件**，将原始的 LLM 内核转化为生产级的工程劳动力。

---

## 🐧 "Distro" 隐喻

Monoco 建立在清晰的关注点分离之上，灵感来源于 Linux 生态系统：

| 组件                | Linux 对应物  | Monoco 中             | 职责                                                                        |
| :------------------ | :------------ | :-------------------- | :-------------------------------------------------------------------------- |
| **Kernel (内核)**   | Linux Kernel  | **Kimi CLI / Kosong** | 原始执行引擎。处理 LLM 交互、工具执行和进程隔离。                           |
| **Distro (发行版)** | Ubuntu / Arch | **Monoco**            | 系统管理者。编排工作流、强制执行策略、管理状态 (Issue) 并安装能力 (Skill)。 |
| **Desktop (桌面)**  | GNOME / KDE   | **VSCode / Zed**      | 用户界面。通过标准协议 (LSP, ACP) 连接到 Monoco 以提供可视化体验。          |

## 🌟 核心理念

### 1. 无头化与协议优先 (Headless & Protocol-First)

Monoco 设计为在后台静默运行。它不会用聊天窗口争夺你的注意力，而是通过 **LSP (Language Server Protocol)** 和 **ACP (Agent Client Protocol)** 暴露状态，让您最喜欢的 IDE 原生具备 Agent 能力。

### 2. Issue 是工作单元 (Unit of Work)

正如 `systemd` 管理 Unit 一样，Monoco 管理 **Issue**。
Issue 不仅仅是一个文本文件；它是一个定义任务生命周期的有状态对象。Agent 不能“打零工 (Freelance)”——它必须被分配到一个活跃的 Issue 上。

### 3. 治理即代码 (Governance as Code)

Monoco 充当您的 AI 劳动力的 "Policy Kit" (策略套件)。

- **护栏 (Guardrails)**: 防止破坏性操作。
- **验证 (Verification)**: 在提交前强制执行 Lint 和测试。
- **审计 (Audit)**: 记录每一个决策和工具调用。

## 🚀 快速开始

### 1. 安装

通过 pip 安装 Monoco 发行版：

```bash
pip install monoco-toolkit
```

### 2. 初始化系统

将您的项目转化为 Monoco 管理的工作空间：

```bash
monoco init
```

### 3. 同步内核 (Sync Kernel)

将 Monoco 的策略注入到您的 Agent 内核配置中 (如 Kimi CLI 配置)：

```bash
monoco sync
```

### 4. 启动会话

启动 Monoco 守护进程以开始编排工作：

```bash
monoco session start
```

## 🛠️ 技术栈与架构

- **内核接口**: Python (对接 Kimi/Kosong)
- **发行版逻辑**: Python (状态管理, Issue 追踪)
- **协议层**: LSP / ACP (用于 IDE 集成)
- **存储层**: 本地文件系统 (Markdown/YAML)

## 🤝 贡献

Monoco 是开源的。我们正在构建 Agent 时代的标准发行版。

## 📄 协议

MIT © [IndenScale](https://github.com/IndenScale)
