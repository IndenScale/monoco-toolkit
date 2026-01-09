---
name: toolkit-core
description: Monoco Toolkit core skill. Covers project initialization, environment detection, and Agent-Native interaction standards.
---

# Toolkit Core

The Monoco Toolkit is the sensory and motor system of the Agent. This skill defines the basic operations and interaction standards of the Toolkit.

## Core Philosophy

1. **Agent Native**: Prioritizes serving Agents. All commands must support `--json` output.
2. **Dual Mode**:
   - **Human Mode**: Default mode, outputting human-readable text, tables, and tree diagrams.
   - **Agent Mode**: Triggered by `--json` or setting the environment variable `AGENT_FLAG=true`, outputting compact JSON.

## Basic Commands

### 1. Initialization (Setup)

- `monoco init`: Initialize the Monoco environment.
  - **Global Setup**: Configure personal information (author name, etc.), stored in `~/.monoco/config.yaml`.
  - **Project Setup**: Initialize a project in the current directory, configuring project name, Key (ticket prefix), etc., stored in `.monoco/config.yaml`.
  - Parameters:
    - `--global`: Configure global settings only.
    - `--project`: Configure current project only.

### 2. Environment Detection (Info)

- `monoco info`: Display the current running status of the Toolkit.
  - Includes version information, current mode (Human/Agent), project root directory, and associated project information.
  - Recommended to run at the beginning of a session to confirm context alignment.

## Interaction Standards

### 1. Structured Output

When calling `monoco` commands, Agents should always pay attention to its JSON output (if provided).

### 2. Automatic Context Recognition

The Toolkit will automatically search upwards from the current directory for a `.monoco` folder or a `monoco.yaml` file to determine the project root directory. Agents do not need to specify paths manually.
