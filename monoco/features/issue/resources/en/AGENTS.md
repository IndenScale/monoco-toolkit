# Issue Management (Agent Guidance)

## Issue Management

System for managing tasks using `monoco issue`.

- **Create**: `monoco issue create <type> -t "Title"` (types: epic, feature, chore, fix)
- **Status**: `monoco issue open|close|backlog <id>`
- **Check**: `monoco issue lint` (Must run after manual edits)
- **Lifecycle**: `monoco issue start|submit|delete <id>`
- **Sync Context**: `monoco issue sync-files [id]` (Update file tracking)
- **Structure**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (e.g. `Issues/Features/open/`). Do not deviate.
- **Rules**:
  1. **Heading**: Must have `## {ID}: {Title}` (matches metadata).
  2. **Checkboxes**: Min 2 using `- [ ]`, `- [x]`, `- [-]`, `- [/]`.
  3. **Review**: `## Review Comments` section required for Review/Done stages.
  4. **Environment Policies**:
     - Must use `monoco issue start --branch`.
     - 🛑 **NO** direct coding on `main`/`master` (Linter will fail).
     - Must update `files` field after coding (via `sync-files` or manual).
