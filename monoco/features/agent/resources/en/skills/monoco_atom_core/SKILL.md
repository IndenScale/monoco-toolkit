---
name: monoco_atom_core
description: Core skill for Monoco Toolkit. Provides essential commands for project initialization, configuration, and workspace management.
type: atom
version: 1.0.0
---

# Monoco Core

Core functionality and commands for the Monoco Toolkit.

## Overview

Monoco is a developer productivity toolkit that provides:

- **Project initialization** with standardized structure
- **Configuration management** at global and project levels
- **Workspace management** for multi-project setups

## Key Commands

### Project Setup

- **`monoco init`**: Initialize a new Monoco project
  - Creates `.monoco/` directory with default configuration
  - Sets up project structure (Issues/, .references/, etc.)
  - Generates initial documentation

### Configuration

- **`monoco config`**: Manage configuration
  - `monoco config get <key>`: View configuration value
  - `monoco config set <key> <value>`: Update configuration
  - Supports both global (`~/.monoco/config.yaml`) and project (`.monoco/config.yaml`) scopes

### Agent Integration

- **`monoco sync`**: Synchronize with agent environments
  - Injects system prompts into agent configuration files (GEMINI.md, CLAUDE.md, etc.)
  - Distributes skills to agent framework directories
  - Respects language configuration from `i18n.source_lang`

- **`monoco uninstall`**: Clean up agent integrations
  - Removes managed blocks from agent configuration files
  - Cleans up distributed skills

### Git Workflow Integration

Monoco enforces a **Feature Branch Workflow** to ensure code isolation and quality:

- **`monoco init`**: Automatically installs Git Hooks
  - **pre-commit**: Runs Issue Linter and code formatting checks
  - **pre-push**: Executes test suite and integrity validation
  - All hooks configurable via `.monoco/config.yaml`

- **Branch Isolation Strategy**:
  - ⚠️ **Required**: Use `monoco issue start <ID> --branch` to create isolated environment
  - Auto-generates normalized branch names: `feat/<id>-<slug>`
  - **Main Protection**: Linter blocks direct code modifications on `main`/`master` branches

- **File Tracking**: `monoco issue sync-files` auto-syncs Git changes to Issue metadata

> 📖 **Detailed Workflow**: See `monoco-issue` skill for complete Issue lifecycle management guide.

## Configuration Structure

Configuration is stored in YAML format at:

- **Global**: `~/.monoco/config.yaml`
- **Project**: `.monoco/config.yaml`

Key configuration sections:

- `core`: Log level, author
- `paths`: Directory paths (issues, spikes, specs)
- `project`: Project metadata, spike repos, workspace members
- `i18n`: Internationalization settings
- `agent`: Agent framework integration settings

## Best Practices

### Basic Operations

1. **Use CLI commands** instead of manual file editing when possible
2. **Run `monoco sync`** after configuration changes to update agent environments
3. **Commit `.monoco/config.yaml`** to version control for team consistency
4. **Keep global config minimal** - most settings should be project-specific

### Git Workflow (⚠️ CRITICAL for Agents)

5. **Strictly follow branch isolation**:
   - ✅ Always use: `monoco issue start <ID> --branch`
   - ❌ Never modify code directly on `main`/`master` branches
   - 📝 Before commit: Run `monoco issue sync-files` to update file tracking

6. **Quality Gates**:
   - Git Hooks will auto-run checks, don't bypass (`--no-verify`)
   - Ensure `monoco issue lint` passes before committing
   - Use `monoco issue submit` to generate delivery reports
