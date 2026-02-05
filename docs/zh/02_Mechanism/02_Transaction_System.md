# 事务系统 (Transaction System)

Monoco 并不只是一个静态的文档规范，它提供了一套强大的 CLI 工具链 (`monoco issue`)，将复杂的工程操作封装为**原子事务 (Atomic Transactions)**。

这不仅仅是“快捷键”，而是为了**强制执行最佳实践**。

## 1. `start`: 环境初始化事务

当你运行 `monoco issue start FEAT-123 --branch` 时，系统不仅是改了个状态，它执行了一系列初始化操作：

1.  **分支隔离**:
    - 自动基于 Trunk 创建新的 Feature 分支 `feat/FEAT-123-description`。
    - 确保工作区是干净的 (Git Clean Check)。
2.  **上下文加载**:
    - 读取 Issue 中的 `files` 列表。
    - 验证这些文件是否存在。
    - (可选) 将这些文件预加载到 Agent 的上下文窗口中。
3.  **状态锁定**:
    - 将 Issue stage 更新为 `doing`。
    - 在本地 `.monoco/state.json` 中记录当前活跃任务，防止任务并发冲突。

**目的**: 确保开发者（或 Agent）在开始写代码的第一秒，环境就是正确、隔离且一致的。

## 2. `sync-files`: 上下文追踪事务

在开发过程中，Monoco 会自动或手动追踪变更。

运行 `monoco issue sync-files`：
1.  **Diff 分析**: 扫描当前 Git 分支相对于 Trunk 的所有变更文件。
2.  **自动注入**: 将这些文件自动追加到 Issue 的 `files` 列表中。
3.  **去重与排序**: 保持列表整洁。

**目的**: 开发者不需要手动维护“我改了哪些文件”。系统自动记录案发现场，为后续的 Code Review 和 Merge 提供精确的范围清单。

## 3. `close`: 交付结项事务

`monoco issue close FEAT-123` 是最复杂的事务，它负责将成果安全地交付回主干：

1.  **质量门禁 (Quality Gate)**:
    - 运行 `monoco issue lint`，确保 Issue 信息完整。
    - (可选) 运行项目测试。
2.  **原子合并 (Atomic Merge)**:
    - 切换回 Trunk 分支。
    - 执行 `git merge --squash` (通常策略)，将 Feature 分支的变更压缩为一个 Commit。
    - Commit Message 自动关联 Issue ID。
3.  **环境清理**:
    - 删除本地 Feature 分支。
    - 将 Issue 文件物理移动到 `Issues/Features/closed/`。
    - 更新 Front Matter 为 `stage: done`。

**目的**: 实现 **"Leave No Trace"**。开发完成后，除了主干上新增的代码和归档的文档，开发环境应自动恢复到初始的干净状态。

## 4. 事务的幂等性与安全性

Monoco 的 CLI 设计遵循**幂等性 (Idempotency)** 原则。
- 如果你重复运行 `monoco issue start`，它会检测到分支已存在并自动切换，而不会报错或覆盖。
- 如果 `close` 过程中发生合并冲突，事务会**暂停**并保留现场，提示用户手动解决冲突后继续，而不会破坏代码库。
