# Issue 管理 (Agent 指引)

## Issue 管理

使用 `monoco issue` 管理任务的系统。

- **创建**: `monoco issue create <type> -t "标题"` (类型: epic, feature, chore, fix)
- **状态**: `monoco issue open|close|backlog <id>`
- **检查**: `monoco issue lint` (手动编辑后必须运行)
- **生命周期**: `monoco issue start|submit|delete <id>`
- **结构**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (如 `Issues/Features/open/`)。
- **强制规则**:
  1. **标题**: 必须包含 `## {ID}: {Title}` 标题（与 Front Matter 一致）。
  2. **内容**: 至少 2 个 Checkbox，使用 `- [ ]`, `- [x]`, `- [-]`, `- [/]`。
  3. **评审**: `review`/`done` 阶段必须包含 `## Review Comments` 章节且内容不为空。
