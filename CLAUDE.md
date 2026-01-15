## Monoco Toolkit

> **Auto-Generated**: This section is managed by Monoco. Do not edit manually.

### Issue Management

System for managing tasks using `monoco issue`.

- **Create**: `monoco issue create <type> -t "Title"` (types: epic, feature, chore, fix)
- **Status**: `monoco issue open|close|backlog <id>`
- **Check**: `monoco issue lint` (Must run after manual edits)
- **Lifecycle**: `monoco issue start|submit|delete <id>`
- **Structure**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (e.g. `Issues/Features/open/`). Do not deviate.

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
