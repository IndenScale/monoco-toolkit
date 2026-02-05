# Issue Management & Trunk Based Development

Monoco follows the **Trunk Based Development (TBD)** pattern. All development occurs in short-lived branches (Branch) and is eventually merged back into the main line (Trunk).

System for managing task lifecycles using `monoco issue`.

- **Create**: `monoco issue create <type> -t "Title"`
- **Status**: `monoco issue open|close|backlog <id>`
- **Check**: `monoco issue lint`
- **Lifecycle**: `monoco issue start|submit|delete <id>`
- **Sync Context**: `monoco issue sync-files [id]`
- **Structure**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (e.g. `Issues/Features/open/`)

## Standard Workflow (Trunk-Branch)

1. **Create Issue**: `monoco issue create feature -t "Title"`
2. **Start Branch**: `monoco issue start FEAT-XXX --branch` (Isolation)
3. **Implement**: Normal coding and testing.
4. **Sync Files**: `monoco issue sync-files` (Update `files` field).
5. **Submit**: `monoco issue submit FEAT-XXX`.
6. **Merge to Trunk**: `monoco issue close FEAT-XXX --solution implemented` (The only way to reach Trunk).

## Git Merge Strategy

- **NO Manual Trunk Operation**: Strictly forbidden from using `git merge` or `git pull` directly on Trunk (`main`/`master`).
- **Atomic Merge**: `monoco issue close` merges changes from Branch to Trunk only for the files listed in the `files` field.
- **Conflicts**: If conflicts occur, follow the instructions provided by the `close` command (usually manual cherry-pick).
- **Cleanup**: `monoco issue close` prunes the Branch/Worktree by default.
