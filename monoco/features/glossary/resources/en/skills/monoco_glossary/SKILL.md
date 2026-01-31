---
name: monoco-glossary
description: Official Monoco Glossary and Operational Laws
tags: [core, definition]
type: standard
version: 1.0.0
---

# Monoco Glossary

## Core Architecture Metaphor: "Linux Distro"

| Term             | Definition                                                                                          | Metaphor                            |
| :--------------- | :-------------------------------------------------------------------------------------------------- | :---------------------------------- |
| **Monoco**       | The Agent Operating System Distribution. Managed policy, workflow, and package system.              | **Distro** (e.g., Ubuntu, Arch)     |
| **Kimi CLI**     | The core runtime execution engine. Handles LLM interaction, tool execution, and process management. | **Kernel** (Linux Kernel)           |
| **Session**      | An initialized instance of the Agent Kernel, managed by Monoco. Has state and context.              | **Init System / Daemon** (systemd)  |
| **Issue**        | An atomic unit of work with state (Open/Done) and strict lifecycle.                                 | **Unit File** (systemd unit)        |
| **Skill**        | A package of capabilities (tools, prompts, flows) that extends the Agent.                           | **Package** (apt/pacman package)    |
| **Context File** | Configuration files (e.g., `GEMINI.md`, `AGENTS.md`) defining environment rules and preferences.    | **Config** (`/etc/config`)          |
| **Agent Client** | The user interface connecting to Monoco (CLI, VSCode, Zed).                                         | **Desktop Environment** (GNOME/KDE) |

## Key Concepts

### Context File

Files like `GEMINI.md` that provide the "Constitution" for the Agent. They define the role, scope, and behavioral policies of the Agent within a specific context (Root, Directory, Project).

### Headless

Monoco is designed to run without a native GUI. It exposes its capabilities via standard protocols (LSP, ACP) to be consumed by various Clients (IDEs, Terminals).

### Universal Shell

The concept that the CLI is the universal interface for all workflows. Monoco acts as an intelligent layer over the shell.
