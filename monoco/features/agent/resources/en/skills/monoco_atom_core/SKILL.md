---
name: monoco_atom_core
description: Core skill of Monoco Toolkit. Provides foundational commands for project initialization, configuration management, and workspace management.
type: atom
version: 1.0.0
---

# Monoco Core

Core features and commands of Monoco Toolkit.

## Overview

Monoco is a developer productivity toolkit providing:

- **Project Initialization**: Standardized project structure
- **Configuration Management**: Global and project-level configuration
- **Workspace Management**: Multi-project setup

## Core Commands

### Project Setup

- **`monoco init`**: Initialize a new Monoco project
  - Creates `.monoco/` directory with default configuration
  - Sets up project structure (Issues/, .references/, etc.)
  - Generates initial documentation

### Configuration Management

- **`monoco config`**: Manage configuration
  - `monoco config get <key>`: View configuration value
  - `monoco config set <key> <value>`: Update configuration
  - Supports global (`~/.monoco/config.yaml`) and project (`.monoco/config.yaml`) scopes

### Agent Integration

- **`monoco sync`**: Sync with agent environment
  - Injects system prompts into agent configuration files (GEMINI.md, CLAUDE.md, etc.)
  - Distributes skills to agent framework directories
  - Follows `i18n.source_lang` language configuration

- **`monoco uninstall`**: Clean up agent integration
  - Removes managed blocks from agent configuration files
  - Cleans up distributed skills

### Git Workflow Integration

Monoco enforces **Feature Branch Workflow** to ensure code isolation and quality:

- **`monoco init`**: Automatically installs Git Hooks
  - **pre-commit**: Runs Issue Linter and code format checks
  - **pre-push**: Executes test suite and integrity validation
  - All Hooks can be configured via `.monoco/config.yaml`

- **Branch Isolation Strategy**:
  - ⚠️ **Mandatory**: Use `monoco issue start <ID> --branch` to create isolated environment
  - Automatically creates standardized branch name: `feat/<id>-<slug>`
  - **Main Branch Protection**: Linter prevents direct code modifications on `main`/`master` branches

- **File Tracking**: `monoco issue sync-files` automatically syncs Git changes to Issue metadata

> 📖 **Detailed Workflow**: See `monoco-issue` skill for complete Issue lifecycle management guide.

## Configuration Structure

Configuration is stored in YAML format at:

- **Global**: `~/.monoco/config.yaml`
- **Project**: `.monoco/config.yaml`

Key configuration sections:

- `core`: Editor, log level, author
- `paths`: Directory paths (issues, spikes, specs)
- `project`: Project metadata, spike repos, workspace members
- `i18n`: Internationalization settings
- `agent`: Agent framework integration settings

## Best Practices

### Basic Operations

1. **Prioritize CLI commands** over manual file editing
2. **Run `monoco sync` after configuration changes** to update agent environment
3. **Commit `.monoco/config.yaml` to version control** to maintain team consistency
4. **Keep global configuration minimal** - most settings should be project-specific

### Git Workflow (⚠️ CRITICAL for Agents)

5. **Strictly follow branch isolation**:
   - ✅ Always use: `monoco issue start <ID> --branch`
   - ❌ Prohibited from directly modifying code on `main`/`master` branches
   - 📝 Before committing run: `monoco issue sync-files` to update file tracking

6. **Quality Gates**:
   - Git Hooks automatically run checks, do not attempt to bypass (`--no-verify`)
   - Ensure `monoco issue lint` passes before committing
   - Use `monoco issue submit` to generate delivery report
