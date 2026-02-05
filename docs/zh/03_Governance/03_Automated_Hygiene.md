# 自动化卫生治理 (Automated Hygiene)

在一个长周期的项目中，"数字垃圾"（废弃分支、过时文档、未使用的锁文件）会迅速积累。Monoco 提供了一套自动化机制来维持项目的卫生。

## 1. 分支管理 (Branch Hygiene)

Git 分支是轻量级的，但不是免费的。过多的 stale branch 会干扰视线。

Monoco 的 `issue close` 命令执行**激进的清理策略**：
- 当一个 Issue 被关闭时，其关联的 Feature Branch 会被强制删除（本地和远程）。
- 这种策略基于一个假设：**Trunk 包含了一切。** 只要代码合并到了主干，分支就没有存在的价值了。

## 2. 依赖与锁文件同步

在 Python/Node 项目中，`package.json` 与 `package-lock.json` (或 `pyproject.toml` 与 `uv.lock`) 的不一致是常见痛点。

Monoco 建议在 `pre-commit` hook 中集成依赖检查：
- 确保 Lock 文件始终与配置文件同步。
- 确保 CI 环境使用的依赖版本与本地一致。

## 3. 影子文件清理

在 `monoco issue start` 过程中，系统可能会生成一些临时文件（如 `.monoco/context_cache/`）。
系统会在每次 `monoco issue close` 或 `monoco clean` 时自动清理这些缓存，防止它们占用磁盘空间或污染搜索结果。

## 4. 归档策略

随着时间推移，`Issues/Features/closed` 目录可能会积累成千上万个文件。
Monoco 提供了 `monoco archive` 命令：
- 将一年前的 Closed Issues 移动到 `.archives/` 目录。
- 或将其打包为 `zip` 存档。
- 保持活跃目录 (`Issues/`) 的索引速度和可读性。

通过这些自动化手段，Monoco 确保项目随着时间推移，依然能保持"第一天"般的整洁与轻快。
