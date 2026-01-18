# Monoco Toolkit

[![Version](https://img.shields.io/pypi/v/monoco-toolkit)](https://pypi.org/project/monoco-toolkit/)
[![License](https://img.shields.io/github/license/IndenScale/Monoco)](LICENSE)

> **The Operating System for Agentic Engineering.**
>
> Ground your AI Agents into deterministic workflows. Turn vague "chats" into structured, validatable, and shippable engineering units.

---

## ⚡️ Why Monoco?

In the era of LLMs, the bottleneck isn't **intelligence**—it's **control**.

Generating code is easy. Managing the lifecycle of thousands of agent-generated tasks, validating their outputs, and maintaining a coherent project state is hard. **Monoco** is the missing control plane that bridges the gap between raw AI velocity and strict engineering rigor.

Monoco handles the **"BizOps Logic"** of your development process, allowing you to orchestrate human and AI labor within a unified, version-controlled environment.

## 🌟 Core Features

### 1. Issue as Code (IaaC)

Treat your project management like your code.

- **Markdown Native**: All tasks (Epics, Features, Chores) are stored as structured Markdown files in your repository.
- **Git Backed**: Version control your roadmap. Review changes to requirements via Pull Requests.
- **Universal Context**: Provides a standardized, hallucination-free state representation for AI Agents.

### 2. The Agent Cockpit (VS Code Extension)

Stop context switching. Manage your entire agentic workflow directly inside your editor.

- **Native Kanban Board**: Visualize and drag-and-drop tasks without leaving VS Code.
- **Hierarchical Tree View**: Drill down from high-level Epics to atomic Implementation Tasks.
- **Agent Integration**: Bind specific Agent Providers (Gemini, Claude, etc.) to specific tasks.

### 3. Traceable Execution

- **Deterministic State Machine**: Every task follows a strict lifecycle (Proposed -> Approved -> Doing -> Review -> Done).
- **Audit Trails**: Agents log their actions and decisions directly into the task file.
- **Sanity Checks**: Built-in linters ensure your task definitions are complete and valid before execution.

## 🚀 Quick Start

### Installation

Monoco is available as a Python CLI tool.

```bash
pip install monoco-toolkit
```

### Initialization

Turn any directory into a Monoco workspace.

```bash
monoco init
```

### Workflow

1.  **Plan**: Create a new feature request.
    ```bash
    monoco issue create feature -t "Implement Dark Mode"
    ```
2.  **Edit**: Refine the requirements in the generated markdown file.
3.  **Visualize**: Open the board in VS Code or via CLI.
    ```bash
    # Starts the local server
    monoco serve
    ```

## 📦 Extension for VS Code

The **Monoco VS Code Extension** is the primary visual interface for the toolkit.

- **Install from Marketplace**: Search for `Monoco`.
- **Keybinding**: `Cmd+Shift+P` -> `Monoco: Open Kanban Board`.

## 🛠️ Tech Stack & Architecture

- **Core**: Python (CLI & Logic Layer)
- **Extension**: TypeScript (VS Code Client & LSP)
- **Data**: Local Filesystem (Markdown/YAML)

## 🤝 Contributing

Monoco is designed for the community. We welcome contributions to both the core CLI and the VS Code extension.

## 📄 License

MIT © [IndenScale](https://github.com/IndenScale)
