---
name: monoco-core
description: Core skill for Monoco Toolkit. Provides essential commands for project initialization, configuration, and workspace management.
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

1. **Use CLI commands** instead of manual file editing when possible
2. **Run `monoco sync`** after configuration changes to update agent environments
3. **Commit `.monoco/config.yaml`** to version control for team consistency
4. **Keep global config minimal** - most settings should be project-specific
