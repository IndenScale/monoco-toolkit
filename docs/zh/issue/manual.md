# Monoco Issue System 用户手册

Monoco Issue System 是一个基于 **"Agent-Native Semantics"** (智能体原生语义) 构建的项目管理工具。

本文档专注于 **CLI 操作指南**。关于 Issue 的分类、状态机和引用关系的详细定义，请参阅 **[核心概念 (Core Concepts)](concepts.md)**。

---

## 1. 命令行参考 (Command Reference)

Monoco Issue System 强烈推荐使用 CLI 工具来管理 Issue，以确保元数据与文件系统的同步。

### 1.1 创建 (Create)

创建新的 Issue。会自动分配下一个可用的 ID。

```bash
monoco issue create <type> --title "标题" [options]
```

- **参数**:
  - `<type>`: `epic`, `feature`, `chore`, `fix`
  - `--title, -t`: Issue 的标题。
  - `--parent, -p`: 父级 Issue ID。
  - `--dependency, -d`: 依赖的 Issue ID。
  - `--related, -r`: 关联的 Issue ID。
  - `--backlog`: 直接创建在 Backlog 状态。
  - `--subdir, -s`: 指定子目录（用于组织结构，例如 `Backend/Auth`）。

**示例**:

```bash
monoco issue create feature --title "实现用户登录" --parent EPIC-001
# 跨项目创建
monoco issue create feature --title "..." --parent monoco::EPIC-001
```

### 1.2 状态流转 (Transition)

#### 开启 & 搁置 (Open & Backlog)

```bash
# 激活 Issue (Status -> Open, Stage -> Todo)
monoco issue open <issue_id>

# 搁置 Issue (Status -> Backlog, Stage -> Freezed)
monoco issue backlog <issue_id>
```

#### 生命周期 (Lifecycle)

Issue 在 `Open` 状态下的推进：

```bash
# 开始工作 (Stage -> Doing)
monoco issue start <issue_id>

# 提交评审 (Stage -> Review)
monoco issue submit <issue_id>
```

#### 关闭 (Close)

完成或关闭 Issue。**注意**: 若 Solution 为 `implemented`，Issue 必须先处于 `Review` 阶段。

```bash
monoco issue close <issue_id> [--solution <type>]
```

- **--solution 可选值**: `implemented` (默认), `cancelled`, `wontfix`, `duplicate`.

### 1.3 提交代码 (Commit)

原子化提交 Issue 变更。此命令会自动进行 Lint 检查，并仅允许提交 `Issues/` 目录下的变更（除非使用 `--detached`）。

```bash
monoco issue commit [-m "message"]
```

### 1.4 查看与可视化 (Visualization)

#### 范围树 (Scope)

查看树状 Issue 结构。

```bash
monoco issue scope [options]
```

- **--all, -a**: 显示所有（含 Closed/Backlog）。
- **--workspace, -w**: **聚合显示 Workspace 成员项目的 Issue**。
- **--recursive, -r**: 递归扫描子目录。

#### 列表视图 (List)

```bash
monoco issue list [options]
```

- **--status, -s**: 筛选状态。
- **--type, -t**: 筛选类型。
- **--stage**: 筛选阶段。
- **--workspace, -w**: 包含 Workspace 成员项目。

### 1.5 查询与筛选 (Query)

使用高级语法进行检索。详细语法请见 [查询语法规范](query_syntax.md)。

```bash
monoco issue query "bug -ui"
```

### 1.6 维护 (Maintenance)

- **Lint**: 验证 `Issues/` 目录完整性。`monoco issue lint`
- **Delete**: 物理删除。`monoco issue delete <issue_id>`

---

## 2. 最佳实践 (Best Practices)

### 2.1 目录结构

Issue 系统采用 **"Type-first, Status-second"** (类型优先，状态次之) 的分层存储策略：

```text
Issues/
├── Epics/
│   ├── open/
│   └── closed/
├── Features/
│   ├── open/
│   └── ...
```

### 2.2 核心原则

1. **优先使用 CLI**: 避免手动移动文件，防止元数据不同步。
2. **强制校验**: 手动编辑后务必运行 `monoco issue lint`。
3. **原子性交付**: Feature 是最小交付单元，内部 Task 使用 Checklist (`- [ ]`) 管理，切勿拆分文件。
