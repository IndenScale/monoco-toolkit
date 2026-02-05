# Issue 管理 & Trunk Based Development

Monoco 遵循 **Trunk Based Development (TBD)** 模式。所有的开发工作都在短平快的分支（Branch）中进行，并最终合并回干线（Trunk）。

使用 `monoco issue` 管理任务生命周期。

- **创建**: `monoco issue create <type> -t "标题"`
- **状态**: `monoco issue open|close|backlog <id>`
- **检查**: `monoco issue lint`
- **生命周期**: `monoco issue start|submit|delete <id>`
- **上下文同步**: `monoco issue sync-files [id]`
- **结构**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (如 `Issues/Features/open/`)

## 标准工作流 (Trunk-Branch)

1. **创建 Issue**: `monoco issue create feature -t "标题"`
2. **开启 Branch**: `monoco issue start FEAT-XXX --branch` (隔离环境)
3. **实现功能**: 正常编码与测试。
4. **同步变更**: `monoco issue sync-files` (更新 `files` 字段)。
5. **提交审查**: `monoco issue submit FEAT-XXX`。
6. **合并至 Trunk**: `monoco issue close FEAT-XXX --solution implemented` (进入 Trunk 的唯一途径)。

## Git 合并策略

- **禁止手动操作 Trunk**: 严禁在 Trunk (`main`/`master`) 分支直接执行 `git merge` 或 `git pull`。
- **原子合并**: `monoco issue close` 仅根据 Issue 的 `files` 列表将变更从 Branch 合并至 Trunk。
- **冲突处理**: 若产生冲突，请遵循 `close` 命令产生的指引进行手动 Cherry-Pick。
- **清理策略**: `monoco issue close` 默认执行清理（删除 Branch/Worktree）。
