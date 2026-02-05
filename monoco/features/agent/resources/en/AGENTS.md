### Monoco Core

Core toolkit commands for project management. Follows the **Trunk Based Development (TBD)** pattern.

- **Init**: `monoco init` (Initialize a new Monoco project)
- **Config**: `monoco config get|set <key> [value]` (Manage configuration)
- **Sync**: `monoco sync` (Sync with agent environment)
- **Uninstall**: `monoco uninstall` (Clean up agent integration)

---

## ⚠️ Agent Must Read: Git Workflow Protocol (Trunk-Branch)

Before modifying any code, **must** follow these steps:

### Standard Process

1. **Create Issue**: `monoco issue create feature -t "Feature Title"`
2. **🔒 Start Branch**: `monoco issue start FEAT-XXX --branch`
   - ⚠️ **Isolation Required**: Use `--branch` or `--worktree` parameter
   - ❌ **Trunk Operation Prohibited**: Forbidden from directly modifying code on Trunk (`main`/`master`)
3. **Implement**: Normal coding and testing
4. **Sync Files**: `monoco issue sync-files` (must run before submitting)
5. **Submit for Review**: `monoco issue submit FEAT-XXX`
6. **Merge to Trunk**: `monoco issue close FEAT-XXX --solution implemented`

### Quality Gates

- Git Hooks automatically run `monoco issue lint` and tests
- Do not use `git commit --no-verify` to bypass checks
- Linter prevents direct modifications on protected Trunk branches

> 📖 See `monoco-issue` skill for complete workflow documentation.
