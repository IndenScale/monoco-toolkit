# Monoco

[![Version](https://img.shields.io/pypi/v/monoco-toolkit)](https://pypi.org/project/monoco-toolkit/)
[![License](https://img.shields.io/github/license/IndenScale/Monoco)](LICENSE)

> **The First L3 Agentic Orchestration Platform.**
>
> Monoco is a **Headless Operating System** designed to shift AI development from **L2 (Agents/Chatbots)** to **L3 (Autonomous Engineering Systems)**. It provides the governance, state management, and environment isolation required to turn raw LLM capabilities into a reliable, verifiable, and autonomous workforce.

---

## 🚀 Beyond the "Chat" Paradigm: The L3 Leap

While traditional AI tools (L2) focus on turn-based chat and "helpful assistants," Monoco orchestrates **Autonomous Sessions**.

| Feature         | L2: AI Agents (e.g. Cursor, Claude Code)   | L3: Autonomous Systems (Monoco)              | Value                |
| :-------------- | :----------------------------------------- | :------------------------------------------- | :------------------- |
| **Interaction** | **HITL**: Human-In-The-Loop (Step-by-step) | **HOTL**: Human-On-The-Loop (Batch/Async)    | **10x Productivity** |
| **Quality**     | Subjective satisfaction (Chat-based)       | **Objective DoD** (Tests, Lints, Invariants) | **Reliability**      |
| **State**       | Ephemeral context (Chat History)           | **Persistent Identity** (Issue Tickets)      | **Traceability**     |
| **Environment** | Shared / Volatile                          | **Isolated / Sandboxed** (Worktrees)         | **Non-Interference** |

---

## 🌩️ The "Distro" Metaphor

Monoco acts as a **Distribution**, bridging the gap between raw intelligence and industrial-grade engineering.

- **LLM Kernel**: The raw reasoning engine (Kimi, Gemini, Claude).
- **Monoco Distro**: The orchestration layer providing the **Init System** (Issue Lifecycle), **Package Manager** (Skills), and **Security Policy** (Guardrails).
- **Client/DE**: Your IDE (VSCode, Zed) interacting via standard protocols (**LSP**, **ACP**).

---

## 🛡️ Core Pillars

### 1. Objective Definition of Done (DoD)

In Monoco, a task is not "finished" when the AI says so. It is finished when the **System Invariants** are met: all tests pass, the linter is silent, and the implementation matches the Issue's acceptance criteria.

### 2. Issue-Driven Development (TDD for Agents)

Monoco treats **Issues as Units of Work**. Just as `systemd` manages system units, Monoco manages the lifecycle of an engineering task—from `open` to `close`, ensuring no "freelancing" and absolute traceability.

### 3. Isolated Sovereignty

Monoco creates dedicated, isolated environments (Branches/Worktrees) for every task. This ensures the AI never pollutes your local state or clashes with human developers.

### 4. Governance as Code

Policies are not just prompts; they are **governed by code**. Monoco enforces Git hooks, CI/CD gates, and automated audits to ensure the workforce adheres to your project's technical standards.

---

## 🏁 Quick Start

### 1. Install the Distro

```bash
pip install monoco-toolkit
```

### 2. Initialize Workspace

Transform any repository into a Monoco-managed autonomous engineering environment.

```bash
monoco init
```

### 3. Sync Policies

Inject your project's governance and standards into the Agent's constitution.

```bash
monoco sync
```

### 4. Orchestrate

Start the daemon to monitor the collaboration bus and schedule agent tasks.

```bash
monoco session start
```

---

## 🛠️ Architecture

- **State Engine**: Markdown/YAML-based persistence (No heavy DB required).
- **Communication**: Event-driven architecture via local file system events.
- **Protocols**: Native support for **LSP** (Language Server) and **ACP** (Agent Client Protocol).

## 📄 License

MIT © [IndenScale](https://github.com/IndenScale)
