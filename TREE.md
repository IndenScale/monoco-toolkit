# Monoco Toolkit Directory Structure

This document outlines the root structure of the Monoco Toolkit repository and the purpose of each key directory.

## Core Directories

| Directory | Purpose |
| :--- | :--- |
| **`.monoco/`** | **System Configuration**. Stores project identity (`project.yaml`) and workspace environment (`workspace.yaml`). Managed by Monoco. |
| **`Issues/`** | **Work Units**. The database of all tasks (Epics, Features, Chores, Fixes), stored as Markdown files. The "Source of Truth" for project management. |
| **`monoco/`** | **Source Code**. The Python source code for the Monoco Toolkit, including the CLI, Core Logic, and Feature Modules. |
| **`tests/`** | **Verification**. Pytest suite for unit and integration tests. |
| **`.references/`** | **External Knowledge (Spikes)**. Read-only copies of external repositories or documentation, managed by `monoco spike`. |

## Auxiliary Directories

| Directory | Purpose |
| :--- | :--- |
| **`.agent/`** | **Agent Skills**. Definitions of skills and workflows available to the AI Agent. |
| **`docs/`** | **Documentation**. Source files for project documentation (MkDocs/VitePress). |
| **`site/`** | **Documentation Site**. The frontend code (VitePress) for the documentation website. |
| **`scripts/`** | **Automation**. Helper scripts for build, release, and maintenance tasks. |
| **`extensions/`** | **IDE Extensions**. Source code for VSCode/Zed extensions. |
| **`Memos/`** | **Fleeting Notes**. Temporary storage for ideas and quick notes (`monoco memo`). |
| **`Kanban/`** | **Visualization**. Web-based Kanban board application. |

## Configuration Files

- **`pyproject.toml`**: Python build and dependency configuration.
- **`package.json`**: Node.js dependencies (for root tools).
- **`GEMINI.md`**: Agent Constitution (Context File) for Gemini.
- **`CLAUDE.md`**: Agent Constitution (Context File) for Claude.
- **`monoco.spec`**: PyInstaller specification for building binary distributions.

---

*This structure reflects the "Monoco Distro" architecture, separating State (Issues), Config (.monoco), and Logic (monoco).*
