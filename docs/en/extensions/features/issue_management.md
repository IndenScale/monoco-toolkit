# Issue Management

This module is responsible for visual management and editing support of project tasks.

## 2.1 Kanban View (`monoco-kanban`)

- **View Interaction**
  - **Display Format**: Webview-based Kanban interface.
  - **Grouping Logic**: Group by Issue status (Open, In Progress, Done, etc.).
  - **Status Update**: Support updating Issue status via card dragging or right-click menu.
  - **Context Switching**: Read `.monoco` metadata, support switching between different projects.

- **Data Sync**
  - **Read**: Fetch latest task list via LSP request `monoco/getAllIssues`.
  - **Write**: Write changes back to file system via LSP request `monoco/updateIssue`.
  - **Real-time**: Listen to file change events and automatically refresh Kanban data.

- **Create Task**
  - **Entry**: "New Issue" button in Kanban interface.
  - **Generation Logic**: Automatically generate Markdown file containing Frontmatter metadata.
  - **Naming**: Follow `ID-Title.md` standard format.

## 2.2 Editor Support

- **Diagnostics**
  - **Trigger Timing**: On file open or save.
  - **Execution Logic**: Call `monoco issue lint` command.
  - **Validation Content**: Frontmatter format, required fields, field value validity.
  - **Feedback Form**: Show wavy line error hints in editor.

- **Completion**
  - **Trigger Scenario**: When typing text in Markdown file.
  - **Completion Content**: Existing Issue IDs.
  - **Hint Info**: Show Issue title, type, and stage.

- **Definition Jump**
  - **Operation**: Ctrl/Cmd + Click on Issue ID.
  - **Behavior**: Jump to corresponding Issue definition file.

- **Auxiliary Features**
  - **Hover**: Hover over Issue ID to show task details.
  - **CodeLens**: Provide shortcut operation entries like "Run Action" above Issue title.
