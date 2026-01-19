# Monoco Toolkit

> **The Agent-Native Development Experience.**

Monoco Toolkit is a specialized toolchain designed to bridge the gap between Human intention and Agent execution. It solves the "Bootstrap Paradox" in AI-assisted development by providing a standardized, deterministic interface for Agents to interact with your codebase, manageable tasks, and external knowledge.

## Why Monoco?

In the era of AI coding assistants, we often face a disconnect: Humans think in **Strategy**, but Agents work in **Operations**.

Monoco aligns these worlds:

- **For Humans**: A Linear-style Kanban board to manage Epics, Features, and Bugs without getting lost in code details.
- **For Agents**: A structured CLI (`monoco`) that treats "Task as Code", allowing agents to discover, understand, and update project status deterministically.

## Key Features

- **Task as Code**: Issues are stored as structured Markdown/YAML files in your repository. No external DB lock-in.
- **Agent-First CLI**: Commands optimized for LLM consumption (structured output, deterministic behavior).
- **Kanban UI**: A modern Next.js web interface for human project management.
- **Research Spikes**: Dedicated management for external knowledge and research tasks.
- **I18n Native**: Built-in support for multilingual documentation and issue tracking.

## Getting Started

See [Setup Guide](setup/) or check out our [Git Workflow Best Practices](workflow.md).
