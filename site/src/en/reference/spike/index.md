# Monoco Spike System

The **Monoco Spike System** is a tool for managing temporary, research-oriented code (Git Repo Spikes). It allows developers (and AI Agents) to easily import external open-source projects as references while keeping the main codebase clean.

## 📚 Contents

- **[User Manual](./manual.md)**: Detailed command reference and best practices.

## 💡 Key Features

- **Physical Isolation**: Reference code is stored in `.reference/`, which is ignored by Git by default.
- **Config-Driven**: Repositories are tracked in `.monoco/project.yaml`, not in your Git history.
- **Agent-Ready**: Agents can use the Spike system to "research" existing wheels before reinventing them.
