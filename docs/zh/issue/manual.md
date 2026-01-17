# Monoco Issue System 用户手册

Monoco Issue System 是一个基于 **"Agent-Native Semantics"** (智能体原生语义) 构建的项目管理工具。

本文档专注于 **CLI 操作指南**。关于核心概念与架构，请参阅 **[核心概念 (Core Concepts)](concepts.md)**。关于配置自定义，请参阅 **[配置指南 (Configuration)](configuration.md)**。

---

## 1. 基础操作

### 1.1 创建 (Create)

```bash
monoco issue create <type> --title "标题" [options]
```

- **参数**:
  - `<type>`: `epic`, `feature`, `chore`, `fix` (或自定义类型)
  - `--title, -t`: 标题
  - `--parent, -p`: 父级 ID (e.g. EPIC-001)
  - `--backlog`: 直接创建在 Backlog
  - `--subdir, -s`: 指定子目录

### 1.2 查看 (View)

#### 列表视图 (List)

```bash
monoco issue list [-s open] [-t feature]
```

#### 看板视图 (Board)

在终端中渲染 Kanban 看板，直观展示当前各阶段的任务。

```bash
monoco issue board
```

#### 层级视图 (Scope)

查看 Issue 的树状归属关系。

```bash
monoco issue scope [--sprint SPRINT-ID] [--all]
```

#### 检查详情 (Inspect)

查看 Issue 的元数据、可执行动作及 AST 结构。

```bash
monoco issue inspect <ID>
```

---

## 2. 生命周期管理 (Workflow)

Monoco 的生命周期通过 **Transitions** (流转) 驱动。

### 2.1 开始工作 (Start)

将 Issue 从 `Draft` 移至 `Doing`。支持同时建立物理隔离环境。

```bash
# 基本启动
monoco issue start FEAT-101

# 启动并创建 Git 分支 (自动切换)
monoco issue start FEAT-101 --branch

# 启动并创建 Git Worktree (推荐用于并行开发)
monoco issue start FEAT-101 --worktree
```

### 2.2 提交与评审 (Submit & Review)

```bash
# 提交评审 (Doing -> Review)
monoco issue submit FEAT-101

# 提交并清理资源 (删除分支/Worktree)
monoco issue submit FEAT-101 --prune
```

### 2.3 关闭 (Close)

```bash
monoco issue close FEAT-101 --solution implemented
```

- **Solutions**: `implemented`, `wontfix`, `cancelled`, `duplicate` (可配置)

### 2.4 积压与恢复 (Backlog Operations)

```bash
# 推入积压 (Status: Open -> Backlog)
monoco issue backlog push FEAT-101

# 恢复开发 (Status: Backlog -> Open)
monoco issue backlog pull FEAT-101
```

---

## 3. 代码提交集成 (Atomic Commit)

Monoco 提供了 `commit` 命令来确保提交与 Issue 的关联性。

```bash
# 关联提交 (会自动在 Commit Msg 添加 Ref: ID)
monoco issue commit -m "实现核心逻辑" -i FEAT-101

# 自动推断 (如果暂存区变更仅涉及该 Issue 文件)
monoco issue commit -m "更新验收标准" -i FEAT-101

# 游离提交 (即不关联 Issue，需显式声明)
monoco issue commit -m "临时修复" --detached
```

---

## 4. 维护与排错

### Lint 检查

验证 `Issues/` 目录的完整性（死链、格式错误等）。

```bash
monoco issue lint [--fix]
```

### 物理移动

将 Issue 移动到另一个项目（保留历史，分配新 ID）。

```bash
monoco issue move FEAT-101 --to ../OtherProject
```
