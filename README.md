# Monoco Toolkit

[![Version](https://img.shields.io/pypi/v/monoco-toolkit)](https://pypi.org/project/monoco-toolkit/)
[![License](https://img.shields.io/github/license/IndenScale/Monoco)](LICENSE)

> **The Operating System for Agentic Engineering.**
>
> Stop chatting. Start building.
> Monoco grounds your AI Agents into deterministic, validatable, and shippable engineering workflows.

---

## ⚡️ The Gap: "Chat" is not Engineering.

Generating code is easy. **Engineering**—managing dependencies, maintaining state, validation, and version control—is hard.

Most Agent workflows today are fragile "chats". Monoco turns them into **Software Engineering Processes**. It acts as the "BizOps" layer for your Agents, ensuring that every line of code generated is tracked, reviewed, and aligned with the project roadmap.

## 🌟 Core Philosophy

### 1. Co-pilot by Design

**Just-enough Automation.**
Monoco abstracts away the tedious details (Git ops, state tracking) while keeping you securely in the driver's seat. Agents can suggest and build, but **you** always have the final say on what gets merged.

### 2. Battle-Tested Best Practices

**Senior Engineer Intuition.**
Monoco enforces **Issue Driven Development (IDD)** and standard **Git Workflows**. We bake the rigorous habits of effective software teams into the Agent's core loop, ensuring every line of code is traceable and reviewed.

### 3. Radical Transparency (Dogfooding)

**Process as Product.**
Monoco is built by Monoco. We believe in open-sourcing not just the code, but the engineering process itself. Every design decision, interaction log, and failure is public—providing a live blueprint for Agentic Engineering.

## 🚀 Quick Start

### 1. Installation

Monoco is available as a Python CLI tool.

```bash
pip install monoco-toolkit
```

### 2. Workspace Initialization

Turn any directory into a Monoco Workspace. This creates the `.monoco` config and the `Issues/` directory.

```bash
monoco init
```

### 3. Agent Synchronization

**Crucial Step**: This injects the "Monoco System Neural Network" (System Prompts & Skills) into your agent configuration files (e.g., `GEMINI.md`, `CLAUDE.md`).

```bash
monoco sync
```

### 4. The Engineering Loop (Agent-First)

In Monoco, you don't need to memorize CLI commands. **The Agent is your DevOps Engineer.**

1.  **Chat**: Tell your Agent in the chatbox (e.g., _"Implement Dark Mode"_).
2.  **Plan**: The Agent investigates and proposes an **Issue Ticket** for your review.
3.  **Build**: Once approved, the Agent creates a branch, writes code, and submits changes.
4.  **Ship**: You accept the results. The Agent handles the merge and closure.

---

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
