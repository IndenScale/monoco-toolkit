# Changelog

All notable changes to Monoco Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.6] - 2026-01-18

### 🔧 Improvements

- Updated Agent Settings UI with better organization and section headers
- Improved Agent inheritance logic (Inherit from Default)
- Fixed Webview initialization and local storage data migration
- Enhanced Issue Validator with stricter "Technical Tasks" requirements
- Synced all components (CLI, VS Code Extension, Kanban) to v0.2.6

## [0.2.0] - 2026-01-16

### 🎯 Major Features

#### LSP Architecture & VS Code Integration

- **FEAT-0076**: Implemented Monoco Language Server with real-time diagnostics and intelligent completions
- **FEAT-0077**: Migrated VS Code Cockpit to LSP architecture, replacing legacy CodeLens providers
- **FEAT-0075**: Realigned VS Code extension with proxy pattern for better separation of concerns

#### Agent Execution Layer

- **FEAT-0078**: Implemented unified Agent Execution Layer with support for multiple AI providers (Claude, Gemini, Qwen)
- **FEAT-0079**: Integrated Agent state management in VS Code extension
- **FEAT-0080**: Added VS Code Execution UI with Sidebar and contextual CodeLens actions
- **FEAT-0081**: Introduced Prompty Action System for context-aware agent skills

#### Core Infrastructure

- **FEAT-0073**: Implemented Skill Manager and Distribution system
- **FEAT-0074**: Created Core Integration Registry for centralized agent framework management
- **EPIC-0013**: Unified CLI & Daemon architecture with formal state protocol

### 🔧 Improvements

- Enhanced workspace state management with `WorkspaceState` protocol
- Improved Git monitoring and issue lifecycle tracking
- Refactored daemon services for better modularity
- Added execution profile scanning and management

### 🐛 Bug Fixes

- Fixed extension server communication issues
- Resolved LSP module resolution errors
- Improved delivery report generation

### 🗑️ Deprecated

- Removed legacy built-in executions in favor of Prompty-based actions
- Deprecated hardcoded integration logic in `monoco/core/sync.py`

### 📚 Documentation

- Updated architecture documentation for LSP integration
- Enhanced skill system documentation

---

## [0.1.7] - 2026-01-15

### Features

- Fixed extension publish and lint issues

## [0.1.6] - 2026-01-15

### Features

- Agent environment integration
- Skill distribution system
- Issue stage renaming (todo → draft)

---

[0.2.0]: https://github.com/IndenScale/Monoco/compare/v0.1.7...v0.2.0
[0.1.7]: https://github.com/IndenScale/Monoco/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/IndenScale/Monoco/releases/tag/v0.1.6
