# Issue 管理 (Agent 指引)

## Issue 管理

使用 `monoco issue` 管理任务的系统。

- **创建**: `monoco issue create <type> -t "标题"` (类型: epic, feature, chore, fix)
- **状态**: `monoco issue open|close|backlog <id>`
- **检查**: `monoco issue lint` (手动编辑后必须运行)
- **生命周期**: `monoco issue start|submit|delete <id>`
- **上下文同步**: `monoco issue sync-files [id]` (更新文件追踪)
- **结构**: `Issues/{CapitalizedPluralType}/{lowercase_status}/` (如 `Issues/Features/open/`)。
- **强制规则**:
  1. **先有 Issue**: 在进行任何调研、设计或 Draft 之前，必须先使用 `monoco issue create` 创建 Issue。
  2. **标题**: 必须包含 `## {ID}: {Title}` 标题（与 Front Matter 一致）。
  3. **内容**: 至少 2 个 Checkbox，使用 `- [ ]`, `- [x]`, `- [-]`, `- [/]`。
  4. **评审**: `review`/`done` 阶段必须包含 `## Review Comments` 章节且内容不为空。
  5. **环境策略**:
     - 必须使用 `monoco issue start --branch` 创建 Feature 分支。
     - 🛑 **禁止**直接在 `main`/`master` 分支修改代码 (Linter 会报错)。
     - **清理时机**: 环境清理仅应在 `close` 时执行。**禁止**在 `submit` 阶段清理环境。
     - 修改代码后**必须**更新 `files` 字段（通过 `sync-files` 或手动）。

## Git 合并策略 (Merge Strategy)

### 核心原则

为确保 Feature 分支安全合并到主线，避免"旧状态污染主线"问题，必须遵循以下合并策略：

#### 1. 禁止手动 Merge

- **🛑 严禁** Agent 手动执行 `git merge` 合并 Feature 分支
- **🛑 严禁** 使用 `git pull origin main` 后直接提交
- **✅ 唯一权威途径**: 必须使用 `monoco issue close` 进行闭环

#### 2. 安全合并流程 (Safe Merge Flow)

正确的 Issue 关闭流程如下：

```bash
# 1. 确保当前在 main/master 分支，且代码已合并
$ git checkout main
$ git pull origin main

# 2. 确认 Feature 分支的变更已合并到主线
#    (通过 PR/MR 或其他代码审查流程)

# 3. 使用 monoco issue close 关闭 Issue (默认执行 prune)
$ monoco issue close FEAT-XXXX --solution implemented

# 4. 如需保留分支，使用 --no-prune
$ monoco issue close FEAT-XXXX --solution implemented --no-prune
```

#### 3. 冲突处理原则

当 Feature 分支与主线产生冲突时：

1. **自动合并停止**: 如果 `touched files` (Issue `files` 字段) 与主线产生冲突，自动化工具**必须立即停止合并**，并抛出明确错误。

2. **手动 Cherry-Pick 模式**: 
   - 错误信息会指示 Agent 转入手动 Cherry-Pick 模式
   - **核心原则**: 仅挑选属于本 Feature 的有效变更，严禁覆盖主线上无关 Issue 的更新
   - 使用 `git cherry-pick <commit>` 逐个应用有效提交

3. **Fallback 策略**:
   ```bash
   # 1. 创建临时分支用于解决冲突
   $ git checkout main
   $ git checkout -b temp/FEAT-XXXX-resolve
   
   # 2. 逐个 Cherry-Pick 有效提交
   $ git cherry-pick <commit-hash-1>
   $ git cherry-pick <commit-hash-2>
   
   # 3. 如有冲突，仅保留本 Feature 的变更
   #    放弃任何会覆盖主线上其他 Issue 更新的修改
   
   # 4. 完成后合并临时分支
   $ git checkout main
   $ git merge temp/FEAT-XXXX-resolve
   
   # 5. 关闭 Issue
   $ monoco issue close FEAT-XXXX --solution implemented
   ```

#### 4. 基于 files 字段的智能合并 (Smart Atomic Merge)

Issue 的 `files` 字段记录了 Feature 分支的真实影响范围 (Actual Impact Scope)：

- **生成方式**: `monoco issue sync-files` 使用 `git diff --name-only base...target` 逻辑
- **作用**: 作为合并白名单，仅合并列表中的文件，过滤因"旧版本基线"导致的隐性覆盖
- **限制**: 无法防御显式的误操作修改（如无意中格式化其他 Issue 文件）

**未来增强**: 基于 `files` 列表实现选择性合并逻辑：
```bash
# 选择性合并（规划中）
$ git checkout main
$ git checkout feature/FEAT-XXXX -- <files...>
```

#### 5. 清理策略

- **默认清理**: `monoco issue close` 默认执行 `--prune`，删除 Feature 分支/Worktree
- **保留分支**: 如需保留分支，显式使用 `--no-prune`
- **强制清理**: 使用 `--force` 强制删除未完全合并的分支（谨慎使用）

```bash
# 默认清理分支
$ monoco issue close FEAT-XXXX --solution implemented
# ✔ Cleaned up: branch:feat/feat-XXXX-xxx

# 保留分支
$ monoco issue close FEAT-XXXX --solution implemented --no-prune

# 强制清理（谨慎）
$ monoco issue close FEAT-XXXX --solution implemented --force
```

### 总结

| 操作 | 命令 | 说明 |
|------|------|------|
| 创建 Issue | `monoco issue create feature -t "标题"` | 先创建 Issue 再开发 |
| 启动开发 | `monoco issue start FEAT-XXXX --branch` | 创建 Feature 分支 |
| 同步文件 | `monoco issue sync-files` | 更新 files 字段 |
| 提交评审 | `monoco issue submit FEAT-XXXX` | 进入 Review 阶段 |
| 关闭 Issue | `monoco issue close FEAT-XXXX --solution implemented` | 唯一合并途径 |
| 保留分支 | `monoco issue close ... --no-prune` | 关闭但不删除分支 |

> ⚠️ **警告**: 任何绕过 `monoco issue close` 的手动合并操作都可能导致主线状态污染，违反工作流合规要求。
