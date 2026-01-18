## Monoco Toolkit

> **Auto-Generated**: This section is managed by Monoco. Do not edit manually.

### Design Philosophy

Monoco CLI is designed as an **Agent-Native Interface**.

- **Strictly Non-Interactive**: Commands MUST NOT prompt for user input. If arguments are missing, the command MUST fail immediately. This ensures deterministic behavior for Agents.
- **Text as Interface**: We prefer structured text (Markdown/YAML) over complex UI states.
- **Explicit Context**: Agents must provide full context (e.g., explicit paths) to avoid ambiguity.

### Issue Management

System for managing tasks using `monoco issue`.

- **Create**: `monoco issue create <type> -t "Title"` (types: epic, feature, chore, fix)
- **Status**: `monoco issue open|close|backlog <id>`
- **Check**: `monoco issue lint` (Must run after manual edits)
- **Lifecycle**: `monoco issue start|submit|delete <id>`
- **Sync Context**: `monoco issue sync-files [id]` (Update file tracking)
- **Structure**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (e.g. `Issues/Features/open/`). Do not deviate.
- **Environment Policy**:
  - Must use `monoco issue start --branch`.
  - Protected Branches (main/master) are READ-ONLY.
  - Linter will block direct modifications on main.

### Spike (Research)

Manage external reference repositories.

- **Add Repo**: `monoco spike add <url>` (Available in `.reference/<name>` for reading)
- **Sync**: `monoco spike sync` (Run to download content)
- **Constraint**: Never edit files in `.reference/`. Treat them as read-only external knowledge.

### Documentation I18n

Manage internationalization.

- **Scan**: `monoco i18n scan` (Check for missing translations)
- **Structure**:
  - Root files: `FILE_ZH.md`
  - Subdirs: `folder/zh/file.md`
