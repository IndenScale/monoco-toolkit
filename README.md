# Monoco Distro

[![Version](https://img.shields.io/pypi/v/monoco-toolkit)](https://pypi.org/project/monoco-toolkit/)
[![License](https://img.shields.io/github/license/IndenScale/Monoco)](LICENSE)

> **The Headless Operating System for Agentic Engineering.**
>
> Monoco is a **Linux-like Distribution** for AI Agents.
> It provides the **Package Manager**, **Init System**, and **Policy Kit** that turns a raw LLM Kernel into a production-ready engineering workforce.

---

## 🐧 The "Distro" Metaphor

Monoco is built on a clear separation of concerns, inspired by the Linux ecosystem:

| Component   | In Linux      | In Monoco             | Responsibility                                                                                                             |
| :---------- | :------------ | :-------------------- | :------------------------------------------------------------------------------------------------------------------------- |
| **Kernel**  | Linux Kernel  | **Kimi CLI / Kosong** | The raw execution engine. Handles LLM prompts, tool execution, and process isolation.                                      |
| **Distro**  | Ubuntu / Arch | **Monoco**            | The system manager. Orchestrates workflows, enforces policies, manages state (Issues), and installs capabilities (Skills). |
| **Desktop** | GNOME / KDE   | **VSCode / Zed**      | The user interface. Connects to Monoco via standard protocols (LSP, ACP) to provide a visual experience.                   |

## 🌟 Core Philosophy

### 1. Headless & Protocol-First

Monoco is designed to run silently in the background. It doesn't fight for your attention with a chat window. Instead, it exposes its state via **LSP (Language Server Protocol)** and **ACP (Agent Client Protocol)**, allowing your favorite IDEs to become "Agent-Native".

### 2. Issue is the Unit of Work

Just as `systemd` manages Units, Monoco manages **Issues**.
An Issue is not just a text file; it is a stateful object that defines the lifecycle of a task. The Agent cannot "freelance"—it must be assigned to an active Issue.

### 3. Governance as Code

Monoco acts as the "Policy Kit" for your AI workforce.

- **Guardrails**: Prevent destructive actions.
- **Verification**: Enforce linting and tests before submission.
- **Audit**: Log every decision and tool call.

## 🚀 Quick Start

### 1. Installation

Install the Monoco Distro via pip:

```bash
pip install monoco-toolkit
```

### 2. Initialize System

Turn your project into a Monoco-managed workspace:

```bash
monoco init
```

### 3. Sync Kernel

Inject Monoco's policies into your Agent Kernel (e.g., Kimi CLI configuration):

```bash
monoco sync
```

### 4. Start a Session

Launch the Monoco Daemon to begin orchestrating work:

```bash
monoco session start
```

## 🛠️ Tech Stack & Architecture

- **Kernel Interface**: Python (Interfacing with Kimi/Kosong)
- **Distro Logic**: Python (State Management, Issue Tracking)
- **Protocols**: LSP / ACP (for IDE integration)
- **Storage**: Local Filesystem (Markdown/YAML)

## 📁 Project Structure

Monoco follows a "Distro" architecture that separates **State** (`Issues/`), **Config** (`.monoco/`), and **Logic** (`monoco/`).

For a detailed breakdown of the directory structure, see **[TREE.md](./TREE.md)**.

## 🤝 Contributing

Monoco is open-source. We are building the standard distribution for the Agentic era.

## 📄 License

MIT © [IndenScale](https://github.com/IndenScale)
