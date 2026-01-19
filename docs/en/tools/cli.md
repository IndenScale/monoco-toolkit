# CLI Reference

Monoco CLI is the primary interface for both Humans and Agents.

## Global Options

- `--root`: Set the root directory for issues.
- `--json`: Output results in JSON format (recommended for Agents).

## Commands

### Issue Management

`monoco issue [COMMAND]`

- `create`: Create a new issue (epic, feature, chore, fix).
- `start`: Start working on an issue (creates branch/worktree).
- `submit`: Submit for review.
- `close`: Close an issue.
- `lint`: Check issue integrity.
- `list`: List all issues.

### Spike (Research)

`monoco spike [COMMAND]`

- `add`: Add a reference repository.
- `sync`: Synchronize reference data.

### Documentation I18n

`monoco i18n [COMMAND]`

- `scan`: Check for missing translations.
- `sync`: (Planned) Sync documentation states.

## Examples

```bash
# Create a new feature
monoco issue create feature -t "Implement amazing feature"

# Start working on it
monoco issue start FEAT-0001 --branch
```
