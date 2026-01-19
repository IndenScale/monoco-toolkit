# Core Architecture

The `monoco-vscode` extension adopts a strict Client-Server separation architecture, with all communication based on the LSP protocol.

- **Architecture Pattern**
  - **Protocol**: Language Server Protocol (LSP).
  - **Communication**: Inter-Process Communication (IPC).
  - **Dependency Change**: Dependency on legacy HTTP Server has been completely removed.

- **Client (VS Code Extension)**
  - **Responsibilities**:
    - Handle all UI interactions (Webview, TreeView, QuickPick).
    - Register VS Code commands and event listeners.
    - Manage lifecycle of Webview panels.
  - **Interaction**: Send requests to Server via `sendRequest` and receive notifications pushed by Server.

- **Server (Language Server)**
  - **Responsibilities**:
    - Maintain workspace index (Issue index, metadata cache).
    - Execute time-consuming background tasks (e.g., file scanning, CLI calls).
    - Provide language features (auto-completion, definition jump, diagnostics).
  - **Implementation**: Based on Node.js, executing actual business logic via `monoco` CLI.
