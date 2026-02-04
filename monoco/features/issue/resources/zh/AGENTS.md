# Issue 管理

使用 `monoco issue` 管理任务。

- **创建**: `monoco issue create <type> -t "标题"`
- **状态**: `monoco issue open|close|backlog <id>`
- **检查**: `monoco issue lint`
- **生命周期**: `monoco issue start|submit|delete <id>`
- **上下文同步**: `monoco issue sync-files [id]`
- **结构**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (如 `Issues/Features/open/`)

## 标准工作流

1. **创建**: `monoco issue create feature -t "标题"`
2. **启动**: `monoco issue start FEAT-XXX --branch`
3. **实现**: 正常编码与测试。
4. **同步**: `monoco issue sync-files` (更新 `files` 字段)。
5. **提交**: `monoco issue submit FEAT-XXX`。
6. **合规合并**: `monoco issue close FEAT-XXX --solution implemented` (合并到主线的唯一途径)。

## Git 合并策略

- **禁止手动合并**: 严禁在 `main`/`master` 分支执行 `git merge` 或直接 `git pull`。
- **原子合并**: `monoco issue close` 仅根据 Issue 的 `files` 列表合并变更。
- **冲突处理**: 若产生冲突，请遵循 `close` 命令产生的指引进行手动 Cherry-Pick。
- **清理策略**: `monoco issue close` 默认执行清理（删除分支/Worktree）。需保留请指定 `--no-prune`。
