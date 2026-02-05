# 生命周期循环 (The Lifecycle Loop)

Monoco 定义了一个严格的、闭环的生命周期，确保每个任务都有始有终。

## 宏观循环 (Macro Loop)

### 1. 起草与定义 (Drafting)

- **Actor**: Human
- **Action**: `create`
- **State**: `open/draft`
- **描述**: 这是一个模糊的意图。不需要写代码，只需要定义 "Why" 和 "What"。

### 2. 启动与分支 (Branching)

- **Actor**: Human / Agent
- **Action**: `start --branch`
- **State**: `open/doing`
- **关键变更**:
  - 状态变更为 `Doing`。
  - **物理隔离**: 自动创建 `feat/FEAT-XXX` 分支。
  - **环境策略**: 从此刻起，所有的代码修改必须发生在这个分支上。干线 (Trunk) 变为只读。

### 3. 执行与追踪 (Execution & Tracking)

- **Actor**: Agent
- **Action**: Coding...
- **Micro-Loop**:
  1.  Agent 修改代码。
  2.  **Sync**: 运行 `monoco issue sync-files`。
      - 系统对比 `Branch` vs `Trunk`。
      - 自动更新 Issue Front Matter 中的 `files: [...]` 列表。
  3.  Agent 勾选 Body 中的 `Technical Tasks` (`[ ]` -> `[x]`)。

### 4. 提交与校验 (Submission)

- **Actor**: Agent
- **Action**: `submit`
- **State**: `open/review`
- **描述**: Agent 认为自己完成了工作。`submit` 命令会运行 Lint 检查，清理临时文件，并提示创建 PR。

### 5. 验收与评审 (Review)

- **Actor**: Human
- **Action**: Review Code & Issue
- **描述**: 人类检查代码和 Issue 描述。
  - **通过**: 合并 PR。
  - **拒绝**: 在 Issue 中添加 `## Review Comments`，打回 `Doing` 状态。

### 6. 归档 (Archiving)

- **Actor**: System (via CI/CD or Manual)
- **Action**: `close`
- **State**: `closed/done`
- **描述**: Issue 文件被物理移动到 `closed/` 目录。它成为了项目永久知识库的一部分。

---

## 环境策略 (Environment Policy)

为了维护上述循环的完整性，Linter 强制执行以下策略：

- **Dirty Trunk Protection**: 严禁在 Trunk (`main`, `master`, `production`) 上直接修改代码。
  - 如果 Linter 发现你在 Trunk 上有未提交的修改，它会**报错并阻止操作**。
  - **解决方案**: 立即 `git stash` -> `monoco issue start --branch` -> `git stash pop`。

---

[上一章: 01. 构造](./01_structure.md) | **下一章**: [03. 实战: 工作流](./03_workflow.md)
