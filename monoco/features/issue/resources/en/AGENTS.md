# Issue Management (Agent Guidance)

## Issue Management

System for managing tasks using `monoco issue`.

- **Create**: `monoco issue create <type> -t "Title"` (types: epic, feature, chore, fix)
- **Status**: `monoco issue open|close|backlog <id>`
- **Check**: `monoco issue lint` (Must run after manual edits)
- **Lifecycle**: `monoco issue start|submit|delete <id>`
- **Structure**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (e.g. `Issues/Features/open/`). Do not deviate.
- **Rules**:
  1. **Heading**: Must have `## {ID}: {Title}` (matches metadata).
  2. **Checkboxes**: Min 2 using `- [ ]`, `- [x]`, `- [-]`, `- [/]`.
  3. **Review**: `## Review Comments` section required for Review/Done stages.
