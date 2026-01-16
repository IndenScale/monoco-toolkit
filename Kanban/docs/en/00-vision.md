# Product Vision

## 1. Background & Pain Points

Monoco has implemented a powerful **"Consensus as Code"** infrastructure (Typedown, Chassis, Toolkit) at the bottom layer. However, current user interaction relies mainly on CLI (`monoco issue`) and plain text editing. This brings the following problems:

- **High Barrier to Entry**: For non-technical personnel (PM, Designer), managing tasks via CLI is unrealistic.
- **Lack of Big Picture**: Plain text is difficult to visually display Kanban, Gantt charts, or Burn-down charts.
- **Delayed Feedback**: The chain of Modify Markdown -> Commit Git -> Wait for CI Feedback is too long, lacking the instant responsiveness of modern applications.

## 2. Core Positioning

Kanban is not just a UI; it is a **bridge connecting human intuition and code truth**.

- **For Humans**: It is a modern project management tool similar to [Linear](https://linear.app/) or [Jira](https://www.atlassian.com/software/jira).
- **For Machines**: It is a **Git-based Headless CMS**. All drag-and-drop and click operations are ultimately converted into standard file system changes and Git Commits.

## 3. Key Features

### 3.1 Speed

- **Optimistic UI**: All operations (such as dragging cards) take effect immediately on the UI, while file reading/writing and Git synchronization are handled asynchronously in the background.
- **Local First**: Data is read from the local file system with no network latency.

### 3.2 Consensus Visualization

- **Structured Parsing**: Automatically parses metadata in Typedown (`.td`, `.md`) and displays it as structured fields rather than plain text.
- **Bi-directional Linking**: Utilizes Typedown's reference mechanism to visualize the dependency graph between tasks.

### 3.3 Hybrid Intelligence

- **Agent Collaboration**: Converse with AI Agents in the comments section. AI responses are not just text, but direct code submissions or task status modifications (manifested as Git Commits).

## 4. Target Users

1. **Geek Developers**: Enjoy the control of CLI but also need a Kanban view for a project overview.
2. **Technical Product Managers (TPM)**: Need to be deeply involved in codebase management but hope to reduce cognitive load through a graphical interface.
3. **Agile Teams**: Use Scrum/Kanban methodologies and need a collaboration platform based on Git as the single source of truth.
