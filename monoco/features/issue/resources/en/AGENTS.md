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
  1. **Issue First**: You MUST create an Issue (`monoco issue create`) before starting any work (research, design, or drafting).
  2. **Heading**: Must have `## {ID}: {Title}` (matches metadata).
  3. **Checkboxes**: Min 2 using `- [ ]`, `- [x]`, `- [-]`, `- [/]`.
  4. **Review**: `## Review Comments` section required for Review/Done stages.
  5. **Environment Policies**:
     - Must use `monoco issue start --branch`.
     - 🛑 **NO** direct coding on `main`/`master` (Linter will fail).
     - **Prune Timing**: ONLY prune environment (branch/worktree) during `monoco issue close --prune`. NEVER prune at `submit` stage.
     - Must update `files` field after coding (via `sync-files` or manual).
