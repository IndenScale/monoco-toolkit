# Monoco: Harnessing AI Agents

> **The control interface between raw AI velocity and human information bandwidth.**

Production in the LLM era is exploding along a vertical curve. A single AI agent can work 24/7, generating massive amounts of intermediate data that far exceeds the biological information bandwidth of a human supervisor. When one agent becomes a hundred, the bottleneck is no longer "intelligence"—it is "command and control."

**Monoco is the Cockpit.**

It doesn't just "run" agents; it "encapsulates" them. It provides a deterministic barrier between the chaotic, raw execution power of LLMs and the rigorous, finite decision bandwidth of human engineers. It ensures that every agentic action eventually collapses into the outcome you intended.

## Workflow: Plan - Execute - Review - Archive

Monoco channels agent execution into a clear cycle:

1. **Plan**: Decompose complex missions through **Project → Epic → Feature** hierarchies into executable atomic units.
2. **Execute**: Agents work autonomously based on acceptance criteria defined in Issues, with all intermediate states persisted as structured files.
3. **Review**: Humans monitor progress through the Kanban dashboard, intervening only at critical decision points.
4. **Archive**: Completed tasks automatically transition to archived states, forming a traceable project history.

## The Control Matrix

- **Task Anchors (Issues)**: Define missions via structured files, setting clear boundaries and acceptance criteria for agents.
- **Deterministic Interface (CLI)**: Acts as a sensory extension for LLMs, providing them with structured perception of project state and eliminating hallucinated guesses.
- **Mission Dashboard (Kanban)**: A high-fidelity visual console that allows humans to audit tasks and transition states with minimal cognitive load.

## Quick Start

### 1. Install the Control Suite

```bash
pip install monoco-toolkit
```

### 2. Initialize the Workflow

```bash
monoco init
```

### 3. Take Control

Start the backend control hub:

```bash
monoco serve
```

Then, launch the visual mission dashboard from anywhere:

```bash
npx @monoco-io/kanban
```

Visit `http://localhost:3123` (or the URL displayed in your terminal) to enter your cockpit.

---

_"Cars are made to drive, not to fix."_
