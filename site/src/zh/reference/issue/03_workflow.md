# 命令与工具 (Workflow Tools)

本指南涵盖了你在 Monoco 工作流中会用到的核心 CLI 命令。

> 💡 **Tip**: 所有的 CLI 操作都可以在 VS Code Extension 的看板界面通过可视化方式完成。

## 1. 仪表盘 (Dashboard)

### 看板 (Board)

```bash
monoco issue board
```

一个全功能的终端 TUI 看板。支持 Vim 键位导航，可以直接拖拽任务状态。

### 列表 (List)

```bash
monoco issue list --status open --type feature
```

适合在脚本中使用或快速检索。

### 范围 (Scope)

```bash
monoco issue scope
```

展示任务的层级关系树 (Epic -> Feature -> Start)。

## 2. 动作 (Actions)

### 创建 (Create)

```bash
monoco issue create feature -t "支持深色模式" --parent EPIC-001
```

### 启动 (Start)

```bash
monoco issue start FEAT-001 --branch
```

- **关键参数**: `--branch` (强烈推荐)。自动基于当前主分支创建 Feature 分支。

### 提交 (Submit)

```bash
monoco issue submit FEAT-001
```

标记为 Review 状态。

### 关闭 (Close)

```bash
monoco issue close FEAT-001 --solution implemented
```

归档任务。需要提供解决方案类型 (`implemented`, `wontfix` 等)。

## 3. 维护 (Maintenance)

### 上下文同步 (Context Sync) ✨

```bash
monoco issue sync-files [ID]
```

- **作用**: 自动检测当前分支修改了哪些文件，并更新到 Issue 的 `files` 列表。
- **场景**: 在每次 Commit 前或准备 Submit 时运行。

### 校验与修复 (Lint & Fix)

```bash
monoco issue lint --fix
```

- **作用**: 扫描所有 Issue 的格式错误、死链、环境违规。
- **--fix**: 尝试自动修复（例如修正错误的 Heading，补充缺失的 Front Matter）。

### 物理移动 (Move)

```bash
monoco issue move FEAT-001 --to ../OtherProject
```

跨项目迁移 Issue，且保留 Git 历史。

---

[上一章: 02. 循环](./02_lifecycle.md) | **下一章**: [04. 协议: 智能体](./04_agent_protocol.md)
