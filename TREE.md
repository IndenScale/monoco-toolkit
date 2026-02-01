# Monoco Toolkit Directory Structure

This document outlines the root structure of the Monoco Toolkit repository and the purpose of each key directory.

> **The "Distro" Architecture**: Monoco separates **State** (Issues), **Config** (.monoco), and **Logic** (monoco), reflecting the Linux distribution model where the Kernel (Kimi CLI) executes, the Distro (Monoco) manages, and the Desktop (IDE) presents.

---

## Core Directories

| Directory | Purpose |
| :--- | :--- |
| **`.monoco/`** | **System Configuration**. Stores project identity (`project.yaml`), workspace environment (`workspace.yaml`), execution state (`execution/`), sessions (`sessions/`), and roles (`roles/`). Managed by Monoco. |
| **`Issues/`** | **Work Units**. The database of all tasks (Epics, Features, Chores, Fixes, Domains), stored as Markdown files. The "Source of Truth" for project management. Organized by type and status. |
| **`monoco/`** | **Source Code**. The Python source code for the Monoco Toolkit, including the CLI (`cli/`), Core Logic (`core/`), Feature Modules (`features/`), and Daemon (`daemon/`). |
| **`tests/`** | **Verification**. Pytest suite for unit and integration tests. |
| **`.references/`** | **External Knowledge (Spikes)**. Read-only copies of external repositories or documentation, managed by `monoco spike`. |

---

## Agent Configuration Directories

| Directory | Purpose |
| :--- | :--- |
| **`.agent/`** | **Agent Skills & Workflows** (Kimi). Definitions of skills (`skills/`) and workflows (`workflows/`) available to the Kimi AI Agent. |
| **`.claude/`** | **Agent Skills** (Claude). Skill definitions for the Claude AI Agent. |
| **`.gemini/`** | **Agent Skills** (Gemini). Skill definitions for the Gemini AI Agent. |
| **`.qwen/`** | **Agent Skills** (Qwen). Skill definitions for the Qwen AI Agent. |

---

## Auxiliary Directories

| Directory | Purpose |
| :--- | :--- |
| **`docs/`** | **Documentation**. Source files for project documentation (MkDocs). |
| **`site/`** | **Documentation Site**. The frontend code (VitePress) for the documentation website. |
| **`scripts/`** | **Automation**. Helper scripts for build, release, and maintenance tasks. |
| **`extensions/`** | **IDE Extensions**. Source code for VSCode/Zed extensions. |
| **`Memos/`** | **Fleeting Notes**. Temporary storage for ideas and quick notes (`monoco memo`). |
| **`Kanban/`** | **Visualization**. Web-based Kanban board application. |
| **`.archives/`** | **Issue Archives**. Closed/completed issues moved here for historical reference. |
| **`assets/`** | **Static Assets**. Images, logos, and other static files. |
| **`build/`** | **Build Artifacts**. Temporary build output (PyInstaller, etc.). |
| **`dist/`** | **Distribution**. Packaged releases and distribution files. |

---

## Configuration Files

### Project Configuration
- **`pyproject.toml`**: Python build and dependency configuration.
- **`package.json`**: Node.js dependencies (for documentation site and tools).
- **`package-lock.json`**: Locked Node.js dependency versions.
- **`uv.lock`**: Locked Python dependency versions (UV package manager).

### Agent Constitution (Context Files)
- **`AGENTS.md`**: Universal agent guidelines and project overview.
- **`GEMINI.md`**: Agent Constitution for Gemini.
- **`CLAUDE.md`**: Agent Constitution for Claude.
- **`QWEN.md`**: Agent Constitution for Qwen.

### Build & Packaging
- **`monoco.spec`**: PyInstaller specification for building binary distributions.
- **`mkdocs.yml`**: MkDocs configuration for documentation generation.

### Development Tools
- **`.pre-commit-config.yaml`**: Pre-commit hooks configuration.
- **`.prettierrc`**: Prettier code formatter configuration.
- **`.prettierignore`**: Files excluded from Prettier formatting.
- **`.gitignore`**: Git ignore patterns.

### Project Metadata
- **`LICENSE`**: MIT License.
- **`CHANGELOG.md`**: Version history and changes.
- **`CONTRIBUTING.md`**: Contribution guidelines.
- **`CODE_OF_CONDUCT.md`**: Community standards.
- **`README.md`**: Project overview (this file).
- **`README_ZH.md`**: Chinese version of README.
- **`TREE.md`**: This file - directory structure documentation.

---

## Directory Tree Visualization

```
Monoco-Toolkit/
├── .monoco/                    # System Configuration
│   ├── project.yaml            # Project identity (name, key)
│   ├── workspace.yaml          # Environment configuration
│   ├── state.json              # Runtime state
│   ├── execution/              # Execution tracking
│   ├── sessions/               # Active sessions
│   └── roles/                  # Role definitions
│
├── Issues/                     # Work Units Database
│   ├── Epics/                  # Epic issues
│   ├── Features/               # Feature issues
│   │   ├── open/
│   │   ├── doing/
│   │   ├── review/
│   │   └── done/
│   ├── Chores/                 # Chore issues
│   ├── Fixes/                  # Bug fix issues
│   └── Domains/                # Domain-specific issues
│
├── monoco/                     # Source Code
│   ├── cli/                    # Command-line interface
│   ├── core/                   # Core logic
│   │   ├── setup.py            # Initialization logic
│   │   ├── issue.py            # Issue management
│   │   └── ...
│   ├── features/               # Feature modules
│   ├── daemon/                 # Daemon process
│   └── main.py                 # Entry point
│
├── tests/                      # Test Suite
├── .references/                # External Knowledge (Spikes)
│
├── .agent/                     # Kimi Agent Skills & Workflows
├── .claude/                    # Claude Agent Skills
├── .gemini/                    # Gemini Agent Skills
├── .qwen/                      # Qwen Agent Skills
│
├── docs/                       # Documentation Source
├── site/                       # Documentation Site (VitePress)
├── scripts/                    # Automation Scripts
├── extensions/                 # IDE Extensions
├── Memos/                      # Fleeting Notes
├── Kanban/                     # Kanban Board App
├── .archives/                  # Issue Archives
├── assets/                     # Static Assets
├── build/                      # Build Artifacts
└── dist/                       # Distribution Packages
```

---

## Initialization Alignment

The `monoco init` command (via `monoco/core/setup.py`) creates and manages the following structure:

1. **Global Config** (`~/.monoco/config.yaml`): User identity and telemetry settings
2. **Project Config** (`.monoco/project.yaml`): Project name and key
3. **Workspace Config** (`.monoco/workspace.yaml`): Paths and hooks
4. **Directories Created**:
   - `Issues/`: For work unit tracking
   - `.references/`: For external knowledge

This aligns with the "Distro" architecture where Monoco manages the environment while the Kernel (Kimi CLI) executes tasks.

---

*Last Updated: 2026-02-01*
