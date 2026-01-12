# Monoco Toolkit

> **The Agent-Native Development Experience.**

Monoco Toolkit is a specialized toolchain designed to bridge the gap between Human intention and Agent execution. It solves the "Bootstrap Paradox" by providing a standardized, deterministic interface for Agents to interact with the codebase, manageable tasks, and external knowledge.

## Vision

To build a **Symbiotic Development Environment** where:

- **Humans** focus on Strategy, Value Definition, and Review (via Kanban UI).
- **Agents** handle Execution, Maintenance, and Validation (via CLI Toolkit).

## Components

The Toolkit consists of two primary interfaces:

### 1. The Toolkit CLI (`monoco`)

_The Sensory Extension for Agents._
A Python-based CLI that provides structured, deterministic access to the project's state. It treats **"Task as Code"**, managing issues, research spikes, and quality checks as structured files on the filesystem.

### 2. The Kanban UI

_The Cockpit for Humans._
A Next.js-based web application that visualizes the project status, providing a "Linear-like" experience for managing Epics, Stories, and Tasks defined by the toolkit.

## Quick Start

### 1. Install the CLI

```bash
cd Toolkit
pip install -e .
```

### 2. Run the Daemon & UI

```bash
# Start the backend daemon
monoco serve

# In a separate terminal, start the UI
cd Toolkit/Kanban
npm run dev
```

## Documentation

- **Architecture**: [Design Philosophy & Standards](docs/en/architecture.md)
- **Issue System**: [Manual](docs/en/issue/manual.md)
- **Spike System**: [Manual](docs/en/spike/manual.md)
