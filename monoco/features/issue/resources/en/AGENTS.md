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
     - **Prune Timing**: ONLY prune environment (branch/worktree) during `monoco issue close `. NEVER prune at `submit` stage.
     - Must update `files` field after coding (via `sync-files` or manual).

## Git Merge Strategy

### Core Principles

To ensure safe merging of Feature branches into the mainline and prevent "stale state pollution", the following merge strategy must be followed:

#### 1. No Manual Merge

- **🛑 STRICTLY FORBIDDEN**: Agents must NOT manually execute `git merge` to merge Feature branches
- **🛑 STRICTLY FORBIDDEN**: Using `git pull origin main` followed by direct commits
- **✅ ONLY AUTHORITATIVE PATH**: Must use `monoco issue close` for closing the loop

#### 2. Safe Merge Flow

The correct Issue closing workflow is as follows:

```bash
# 1. Ensure you're on main/master branch and code is merged
$ git checkout main
$ git pull origin main

# 2. Confirm Feature branch changes are merged to mainline
#    (via PR/MR or other code review process)

# 3. Use monoco issue close to close Issue (prune by default)
$ monoco issue close FEAT-XXXX --solution implemented

# 4. To keep branch, use --no-prune
$ monoco issue close FEAT-XXXX --solution implemented --no-prune
```

#### 3. Conflict Resolution Principles

When Feature branch conflicts with mainline:

1. **Auto-merge Stop**: If `touched files` (Issue `files` field) conflict with mainline, automation tools **MUST IMMEDIATELY STOP** merging and throw a clear error.

2. **Manual Cherry-Pick Mode**:
   - Error message will instruct Agent to switch to manual Cherry-Pick mode
   - **Core Principle**: Only pick valid changes belonging to this Feature, STRICTLY FORBIDDEN from overwriting updates to unrelated Issues on mainline
   - Use `git cherry-pick <commit>` to apply valid commits one by one

3. **Fallback Strategy**:

   ```bash
   # 1. Create temporary branch for conflict resolution
   $ git checkout main
   $ git checkout -b temp/FEAT-XXXX-resolve

   # 2. Cherry-pick valid commits one by one
   $ git cherry-pick <commit-hash-1>
   $ git cherry-pick <commit-hash-2>

   # 3. If conflicts occur, only keep changes from this Feature
   #    Discard any modifications that would overwrite other Issue updates on mainline

   # 4. Merge temporary branch when done
   $ git checkout main
   $ git merge temp/FEAT-XXXX-resolve

   # 5. Close Issue
   $ monoco issue close FEAT-XXXX --solution implemented
   ```

#### 4. Smart Atomic Merge Based on files Field

The Issue's `files` field records the Actual Impact Scope of the Feature branch:

- **Generation**: `monoco issue sync-files` uses `git diff --name-only base...target` logic
- **Purpose**: Serves as a merge whitelist, only merging files in the list, filtering out implicit overwrites caused by "stale baseline"
- **Limitation**: Cannot defend against explicit accidental modifications (e.g., inadvertently formatting other Issue files)

**Future Enhancement**: Implement selective merge logic based on `files` list:

```bash
# Selective merge (planned)
$ git checkout main
$ git checkout feature/FEAT-XXXX -- <files...>
```

#### 5. Cleanup Strategy

- **Default Cleanup**: `monoco issue close` executes `` by default, deleting Feature branch/worktree
- **Keep Branch**: To preserve branch, explicitly use `--no-prune`
- **Force Cleanup**: Use `--force` to force delete unmerged branches (use with caution)

```bash
# Default branch cleanup
$ monoco issue close FEAT-XXXX --solution implemented
# ✔ Cleaned up: branch:FEAT-XXXX-xxx

# Keep branch
$ monoco issue close FEAT-XXXX --solution implemented --no-prune

# Force cleanup (caution)
$ monoco issue close FEAT-XXXX --solution implemented --force
```

### Summary

| Operation         | Command                                               | Description                     |
| ----------------- | ----------------------------------------------------- | ------------------------------- |
| Create Issue      | `monoco issue create feature -t "Title"`              | Create Issue before development |
| Start Development | `monoco issue start FEAT-XXXX --branch`               | Create Feature branch           |
| Sync Files        | `monoco issue sync-files`                             | Update files field              |
| Submit Review     | `monoco issue submit FEAT-XXXX`                       | Enter Review stage              |
| Close Issue       | `monoco issue close FEAT-XXXX --solution implemented` | Only merge path                 |
| Keep Branch       | `monoco issue close ... --no-prune`                   | Close without deleting branch   |

> ⚠️ **WARNING**: Any manual merge operation bypassing `monoco issue close` may cause mainline state pollution and violate workflow compliance requirements.
