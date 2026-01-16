# Monoco for VS Code

[![Version](https://img.shields.io/visual-studio-marketplace/v/indenscale.monoco-vscode)](https://marketplace.visualstudio.com/items?itemName=indenscale.monoco-vscode)
[![Installs](https://img.shields.io/visual-studio-marketplace/i/indenscale.monoco-vscode)](https://marketplace.visualstudio.com/items?itemName=indenscale.monoco-vscode)
[![License](https://img.shields.io/github/license/IndenScale/Monoco)](https://github.com/IndenScale/Monoco)

**Monoco** is the official VS Code extension for the Monoco Toolkit. It transforms your editor into a powerful "Agent-Native" development cockpit, seamlessly integrating project management, Kanban visualization, and AI agent orchestration directly into your workflow.

> **Note**: This extension requires the [Monoco Toolkit](https://github.com/IndenScale/Monoco) to be installed on your system.

---

## ✨ Features

### 1. Visual Kanban Board
Manage your project's heartbeat without leaving VS Code. The **Monoco Cockpit** provides a real-time Kanban view of your issues.
- **Drag & Drop**: Move tasks between Todo, Doing, Review, and Done.
- **Filtering**: Quickly filter by Epics, Features, Chores, or Bugs.
- **One-Click Navigation**: Click any card to jump directly to the underlying Markdown file.

### 2. Intelligent Markdown Editing (LSP)
Monoco uses a dedicated **Language Server** to treat your Issue Markdown files as first-class citizens.
- **Diagnostics**: Get real-time error reporting for invalid frontmatter, lifecycle violations (e.g., closing an issue without completing it), and schema errors.
- **Auto-Completion**: Type `#` to trigger intelligent suggestions for Issue IDs, referencing other tasks instantly.
- **Go to Definition**: `Ctrl+Click` (or `Cmd+Click`) on any Issue ID to navigate to its definition.

### 3. Seamless Agent Orchestration
Execute Monoco Agent skills and SOPs directly from the editor.
- **Action Discovery**: Browses available actions defined in your project.
- **Context-Aware**: Agents are aware of your current workspace context.

### 4. Zero-Config Runtime
- **Auto-Daemon**: The extension automatically detects and launches the `monoco serve` daemon if it's not running.
- **Project Detection**: Automatically identifies Monoco projects based on `.monoco` configuration.

---

## 🚀 Getting Started

1.  **Install the Extension**: Search for "Monoco" in the VS Code Marketplace and install it.
2.  **Open a Monoco Project**: Open a folder containing a `.monoco` directory.
3.  **Launch the Cockpit**: Click the Monoco icon in the Activity Bar (sidebar).
4.  **Start Managing**: You should see your issues populate the board.

## ⚙️ Configuration

You can customize the extension via VS Code Settings (`Ctrl+,`):

| Setting | Default | Description |
| :--- | :--- | :--- |
| `monoco.apiBaseUrl` | `http://127.0.0.1:8642/api/v1` | URL for the Monoco Daemon API. |
| `monoco.webUrl` | `http://127.0.0.1:8642` | URL for the full Web UI. |
| `monoco.executablePath` | `monoco` | Path to the `monoco` CLI executable. |

## 📦 Requirements

- **VS Code**: v1.90.0 or higher.
- **Monoco Toolkit**: Python-based toolkit installed (`pip install monoco-toolkit` or equivalent).

---

## 🌏 中文说明 (Chinese)

**Monoco VS Code 扩展** 为您的开发工作流带来原生的看板管理与 AI 智能体编排体验。

### 主要功能
- **可视化看板**: 在侧边栏直接管理 Epic、Feature 和 Bug，支持拖拽流转状态。
- **智能编辑 (LSP)**: 提供 Markdown 文件的语法检查、生命周期校验和 ID 自动补全。
- **一键跳转**: 点击 Issue ID 即可跳转到对应文件。
- **零配置**: 自动启动后台守护进程，开箱即用。

### 快速开始
1. 安装本插件。
2. 打开包含 `.monoco` 目录的项目文件夹。
3. 点击侧边栏的 Monoco 图标即可开启看板。

---

## 🔗 Links

- [GitHub Repository](https://github.com/IndenScale/Monoco)
- [Report Issues](https://github.com/IndenScale/Monoco/issues)

**Enjoying Monoco?** Please leave a review! ⭐⭐⭐⭐⭐
