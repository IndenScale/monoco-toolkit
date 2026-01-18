# Monoco VS Code Extension

Monoco VS Code Extension (`monoco-vscode`) is the official editor integration for Monoco Toolkit, aiming to provide a seamless "Agent Native" development experience.

It adopts **Language Server Protocol (LSP)** architecture, decoupling intelligence from IDE while retaining visual Cockpit interface for high-level management.

## Core Features

### 1. LSP Intelligence

Powered by built-in Node.js Language Server, specifically for semantic analysis of Monoco task files (`.md`).

- **Diagnostics**:
  - **Frontmatter Validation**: Check correctness of YAML header syntax.
  - **Lifecycle Logic Check**: Enforce business rules (e.g., when `status: closed`, `stage` must be `done`) to prevent invalid state transitions.
- **Auto-Completion**:
  - Auto-complete Issue ID references based on workspace index.
  - Hint info includes Issue title, type, and stage.
- **Go to Definition**:
  - Support `Ctrl+Click` (macOS `Cmd+Click`) on Issue ID to jump directly to corresponding Markdown file location.

### 2. Visual Interface

Integrated management interface in VS Code Activity Bar.

- **Issue Explorer**: Provides a tree view displaying all Issues within the Workspace.
- **Shortcuts**:
  - Create new Issue.
  - Click node to open corresponding Markdown file.

### 3. Runtime Management

Extension is responsible for maintaining Monoco background services, ensuring "Out of the Box" experience.

- **Daemon Auto-start**:
  - Extension automatically detects local `8642` port on startup.
  - If service is not running, automatically executes `uv run monoco serve` in background terminal to start daemon process.
- **Bootstrap**:
  - Automatically checks and initializes necessary `.monoco` environment configuration.

## Architecture

The extension adopts a standard Client-Server architecture:

- **Client (`/client`)**:
  - Responsible for VS Code UI integration and command registration.
  - Manages Language Client lifecycle.
  - Responsible for HTTP/SSE communication with Monoco Daemon (Python).
- **Server (`/server`)**:
  - Standard LSP implementation (Node.js).
  - Independently maintains workspace file index (Indexer).
  - Provides text analysis services, running basic intelligent features **without** Python environment dependency.

## Configuration

- `monoco.apiBaseUrl`: Monoco Daemon API address (Default: `http://127.0.0.1:8642/api/v1`)
