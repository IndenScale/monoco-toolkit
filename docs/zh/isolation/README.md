# 隔离方案 (Isolation Schemes)

Monoco 的 **Trunk Based Development (TBD)** 要求在隔离的开发环境中实现 Issue。隔离不仅能保护干线（Trunk）的安全，还能为智能体（Agent）提供一个纯净的上下文。

目前 Monoco 支持两种主要的隔离方案：**Branch (分支)** 和 **Worktree (工作树)**。

## 方案对比

### 1. Branch 方案 (默认推荐)

这是最常用的隔离方案，通过本地 Git 分支实现。

- **实现方式**: 在当前工作目录下切换（Checkout）到一个新的分支。
- **优点**:
  - **低成本**: 无需额外的存储空间。
  - **心智负担小**: 符合大多数开发者的 Git习惯。
  - **快速切换**: 在同一目录下快速切换不同 Issue。
- **缺点**:
  - **上下文丢失**: 切换分支时需要暂存（Stash）当前未提交的变更。
  - **构建副作用**: `node_modules` 或编译产物可能会在切换分支时产生冲突或需要重构。

### 2. Worktree 方案

基于 `git worktree` 实现，每个 Issue 拥有一个独立的物理目录。

- **实现方式**: 在项目根目录外的特定位置（如 `.monoco/worktrees/`）克隆一份完整的代码目录。
- **优点**:
  - **完美隔离**: 物理目录级别的隔离，不同 Issue 的构建产物互不干扰。
  - **并行工作**: 可以同时打开多个编辑器窗口处理不同 Issue，互不阻塞。
  - **无感切换**: 无需 `git stash`，直接进入对应目录即可。
- **缺点**:
  - **存储开销**: 每一个隔离环境都会占用一份项目拷贝的空间（通常不包括 `.git` 目录，因为它共享）。
  - **环境管理**: 需要管理多个 `node_modules` 或环境变量。

## 推荐选择

**默认推荐使用 Branch 方案。**

对于大多数 Agent 辅助开发场景，Branch 方案配合 Monoco 的 `monoco issue start --branch` 指令已经足够高效。

### 什么时候使用 Worktree？

- 你需要同时处理两个相互依赖或冲突的 Issue。
- 项目构建耗时极长，且在不同分支间切换会导致大量的重新编译。
- 你需要进行跨分支的长时间后台测试。

## 指令参考

### 启动隔离环境

```bash
# 使用 Branch 方案 (推荐)
monoco issue start FEAT-XXX --branch

# 使用 Worktree 方案
monoco issue start FEAT-XXX --worktree
```

### 退出与清理

当运行 `monoco issue close` 时，Monoco 会自动识别隔离类型并执行相应的清理操作：

- **Branch**: 删除本地分支并回到 Trunk。
- **Worktree**: 移除 worktree 物理目录并清理 Git 引用。
