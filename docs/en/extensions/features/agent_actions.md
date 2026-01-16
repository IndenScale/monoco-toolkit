# Agent Actions

This module is responsible for integrating and executing Standard Operating Procedures (SOPs).

## 3.1 Action Discovery

- **Action Sources**
  - **Global Scope**: SOPs in `~/.monoco/execution` directory.
  - **Project Scope**: SOPs in `.monoco/execution` directory.
  - **Scan Mechanism**: Retrieved via LSP request `monoco/getExecutionProfiles`.

- **Display Interface**
  - **TreeView**: List all available actions in "Actions" sidebar tree.
  - **Template View**: Support viewing raw Prompt template of Action (`monoco.viewActionTemplate`).

## 3.2 Execution Control

- **Trigger Methods**
  - **Command Palette**: Run `Monoco: Run Action`.
  - **Context Menu**: Trigger via right-click in file explorer or editor.
  - **TreeView**: Click play icon in action list.

- **Context Awareness**
  - **Auto Match**: Recommend relevant Actions based on metadata (Type, Stage) of current file.
  - **Parameter Injection**: Automatically pass current file path as context to Agent.

- **Interactive Input**
  - **Instruction**: Allow user to input additional natural language instructions before execution (e.g., "Pay attention to code style").
