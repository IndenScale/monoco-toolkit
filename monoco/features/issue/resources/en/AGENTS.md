### Issue Management

System for managing tasks using `monoco issue`.

- **Create**: `monoco issue create <type> -t "Title"` (types: epic, feature, chore, fix)
- **Status**: `monoco issue open|close|backlog <id>`
- **Check**: `monoco issue lint` (Must run after manual edits)
- **Lifecycle**: `monoco issue start|submit|delete <id>`
- **Structure**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (e.g. `Issues/Features/open/`). Do not deviate.
