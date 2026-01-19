### Monoco Core

Core toolkit commands for project management.

- **Init**: `monoco init` (Initialize new Monoco project)
- **Config**: `monoco config get|set <key> [value]` (Manage configuration)
- **Sync**: `monoco sync` (Synchronize with agent environments)
- **Uninstall**: `monoco uninstall` (Clean up agent integrations)

---

## ⚠️ Agent Must-Read: Git Workflow

Before modifying any code, **MUST** follow these steps:

### Standard Process

1. **Create Issue**: `monoco issue create feature -t "Feature Title"`
2. **🔒 Start Isolation**: `monoco issue start FEAT-XXX --branch`
   - ⚠️ **Required** `--branch` flag
   - ❌ Never modify code directly on `main`/`master` branches
3. **Implement**: Code and test normally
4. **Sync Files**: `monoco issue sync-files` (must run before commit)
5. **Submit Review**: `monoco issue submit FEAT-XXX`
6. **Close Issue**: `monoco issue close FEAT-XXX --solution implemented`

### Quality Gates

- Git Hooks auto-run `monoco issue lint` and tests
- Don't bypass with `git commit --no-verify`
- Linter blocks direct modifications on protected branches

> 📖 See `monoco-issue` skill for complete workflow documentation.
