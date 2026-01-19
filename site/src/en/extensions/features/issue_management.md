# Issue Management

This module is responsible for visual management and editing support of project tasks.

## 2.1 Issue Explorer

- **View Interaction**
  - **Display Format**: Native TreeView based on VS Code API.
  - **Grouping Logic**: Group by Issue Type (Epic, Feature, etc.) or Status.
  - **Shortcuts**: Support creating sub-issues or transitioning state directly on tree nodes.
  - **Context Switching**: Automatically recognized by Workspace boundaries.

- **Data Sync**
  - **Read**: Fetch latest task list via LSP request.
  - **Write**: All CRUD operations directly manipulate Markdown files via File System API, synced by File Watcher.

- **Create Task**
  - **Entry**: "Create Issue" button in view title bar.
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
