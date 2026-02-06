# Monoco for VS Code

**Monoco** is the official navigation and control extension for the **Monoco**, the operating system for Agentic Engineering.

It brings "Issue as Code" and native Kanban management directly into your IDE, allowing you to orchestrate human and AI workflows without context switching.

![Monoco Kanban](media/screenshot-kanban.png)

## ✨ Features

### 1. Native Kanban Board

Visualize your project status at a glance.

- **Drag & Drop**: Move tasks between states (Doing -> Review -> Done) effortlessly.
- **Real-time Sync**: Changes in the board are immediately reflected in your Markdown files.

### 2. Issue Tree View

Navigate your project hierarchy with precision.

- **Structured View**: See your Epics, Features, and Tasks organized by their relationships.
- **Quick Access**: Click to open issue files or reveal them in the board.

### 3. Agent Integration (LSP Powered)

Monoco acts as the bridge between your code and your agents.

- **Context Awareness**: The extension understands the semantic structure of your issues.
- **Validation**: Real-time diagnostics for your issue files to ensure they meet the "Definition of Ready".

## 🚀 Getting Started

### Prerequisites

You need the `monoco-toolkit` installed on your system.

```bash
pip install monoco-toolkit
```

### Setup

1. Open a folder that contains a Monoco project (or run `monoco init` to start one).
2. The extension will automatically detect the `.monoco` configuration.
3. Open the Kanban board via the Command Palette: `Monoco: Open Kanban Board`.

## ⚙️ Extension Settings

This extension contributes the following settings:

- `monoco.executablePath`: Path to the `monoco` CLI executable (default: `monoco`).
- `monoco.useNativeTree`: Enable the native TreeView for issues (default: `true`).
- `monoco.webUrl`: URL for the web-based cockpit if running remotely.

## 🔗 Links

- **Documentation**: [https://github.com/IndenScale/Monoco](https://github.com/IndenScale/Monoco)
- **Repository**: [https://github.com/IndenScale/Monoco](https://github.com/IndenScale/Monoco)
- **Issues**: [https://github.com/IndenScale/Monoco/issues](https://github.com/IndenScale/Monoco/issues)

---

**Monoco** — _Don't just chat with AI, engineer with it._
