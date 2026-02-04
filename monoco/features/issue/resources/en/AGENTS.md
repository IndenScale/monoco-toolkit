# Issue Management

System for managing tasks using `monoco issue`.

- **Create**: `monoco issue create <type> -t "Title"`
- **Status**: `monoco issue open|close|backlog <id>`
- **Check**: `monoco issue lint`
- **Lifecycle**: `monoco issue start|submit|delete <id>`
- **Sync Context**: `monoco issue sync-files [id]`
- **Structure**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (e.g. `Issues/Features/open/`)

## Standard Workflow

1. **Create Issue**: `monoco issue create feature -t "Title"`
2. **Start Branch**: `monoco issue start FEAT-XXX --branch`
3. **Implement**: Normal coding and testing.
4. **Sync Files**: `monoco issue sync-files` (Update `files` field).
5. **Submit**: `monoco issue submit FEAT-XXX`.
6. **Close & Merge**: `monoco issue close FEAT-XXX --solution implemented` (The only way to merge).

## Git Merge Strategy

- **NO Manual Merge**: Strictly forbidden from using `git merge` or `git pull` into main.
- **Atomic Merge**: `monoco issue close` merges only the files listed in the `files` field.
- **Conflicts**: If conflicts occur, follow the instructions provided by the `close` command (usually manual cherry-pick).
- **Cleanup**: `monoco issue close` prunes the branch/worktree by default. Use `--no-prune` to keep it.
