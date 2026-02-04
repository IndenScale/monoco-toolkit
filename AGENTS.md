# Monoco Toolkit

<!-- MONOCO_GENERATED_START -->
## Monoco Toolkit

> **Auto-Generated**: This section is managed by Monoco. Do not edit manually.

### Agent

###### Monoco 核心

项目管理的核心工具包命令。

- **初始化**: `monoco init` (初始化新的 Monoco 项目)
- **配置**: `monoco config get|set <key> [value]` (管理配置)
- **同步**: `monoco sync` (与 agent 环境同步)
- **卸载**: `monoco uninstall` (清理 agent 集成)

---

##### ⚠️ Agent 必读: Git 工作流

在修改任何代码前,**必须**遵循以下步骤:

###### 标准流程

1. **创建 Issue**: `monoco issue create feature -t "功能标题"`
2. **🔒 启动隔离环境**: `monoco issue start FEAT-XXX --branch`
   - ⚠️ **强制要求** `--branch` 参数
   - ❌ 禁止在 `main`/`master` 分支直接修改代码
3. **实现功能**: 正常编码和测试
4. **同步文件**: `monoco issue sync-files` (提交前必须运行)
5. **提交审查**: `monoco issue submit FEAT-XXX`
6. **关闭 Issue**: `monoco issue close FEAT-XXX --solution implemented`

###### 质量门禁

- Git Hooks 会自动运行 `monoco issue lint` 和测试
- 不要使用 `git commit --no-verify` 绕过检查
- Linter 会阻止在受保护分支上的直接修改

> 📖 详见 `monoco-issue` skill 获取完整工作流文档。

### Issue Management

#### Issue 管理 (Agent 指引)

##### Issue 管理

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

##### Git 合并策略 (Merge Strategy)

###### 核心原则

为确保 Feature 分支安全合并到主线，避免"旧状态污染主线"问题，必须遵循以下合并策略：

####### 1. 禁止手动 Merge

- **🛑 严禁** Agent 手动执行 `git merge` 合并 Feature 分支
- **🛑 严禁** 使用 `git pull origin main` 后直接提交
- **✅ 唯一权威途径**: 必须使用 `monoco issue close` 进行闭环

####### 2. 安全合并流程 (Safe Merge Flow)

正确的 Issue 关闭流程如下：

```bash
#### 1. 确保当前在 main/master 分支，且代码已合并
$ git checkout main
$ git pull origin main

#### 2. 确认 Feature 分支的变更已合并到主线
####    (通过 PR/MR 或其他代码审查流程)

#### 3. 使用 monoco issue close 关闭 Issue (默认执行 prune)
$ monoco issue close FEAT-XXXX --solution implemented

#### 4. 如需保留分支，使用 --no-prune
$ monoco issue close FEAT-XXXX --solution implemented --no-prune
```

####### 3. 冲突处理原则

当 Feature 分支与主线产生冲突时：

1. **自动合并停止**: 如果 `touched files` (Issue `files` 字段) 与主线产生冲突，自动化工具**必须立即停止合并**，并抛出明确错误。

2. **手动 Cherry-Pick 模式**: 
   - 错误信息会指示 Agent 转入手动 Cherry-Pick 模式
   - **核心原则**: 仅挑选属于本 Feature 的有效变更，严禁覆盖主线上无关 Issue 的更新
   - 使用 `git cherry-pick <commit>` 逐个应用有效提交

3. **Fallback 策略**:
   ```bash
###   # 1. 创建临时分支用于解决冲突
   $ git checkout main
   $ git checkout -b temp/FEAT-XXXX-resolve
   
###   # 2. 逐个 Cherry-Pick 有效提交
   $ git cherry-pick <commit-hash-1>
   $ git cherry-pick <commit-hash-2>
   
###   # 3. 如有冲突，仅保留本 Feature 的变更
###   #    放弃任何会覆盖主线上其他 Issue 更新的修改
   
###   # 4. 完成后合并临时分支
   $ git checkout main
   $ git merge temp/FEAT-XXXX-resolve
   
###   # 5. 关闭 Issue
   $ monoco issue close FEAT-XXXX --solution implemented
   ```

####### 4. 基于 files 字段的智能合并 (Smart Atomic Merge)

Issue 的 `files` 字段记录了 Feature 分支的真实影响范围 (Actual Impact Scope)：

- **生成方式**: `monoco issue sync-files` 使用 `git diff --name-only base...target` 逻辑
- **作用**: 作为合并白名单，仅合并列表中的文件，过滤因"旧版本基线"导致的隐性覆盖
- **限制**: 无法防御显式的误操作修改（如无意中格式化其他 Issue 文件）

**未来增强**: 基于 `files` 列表实现选择性合并逻辑：
```bash
#### 选择性合并（规划中）
$ git checkout main
$ git checkout feature/FEAT-XXXX -- <files...>
```

####### 5. 清理策略

- **默认清理**: `monoco issue close` 默认执行 `--prune`，删除 Feature 分支/Worktree
- **保留分支**: 如需保留分支，显式使用 `--no-prune`
- **强制清理**: 使用 `--force` 强制删除未完全合并的分支（谨慎使用）

```bash
#### 默认清理分支
$ monoco issue close FEAT-XXXX --solution implemented
#### ✔ Cleaned up: branch:feat/feat-XXXX-xxx

#### 保留分支
$ monoco issue close FEAT-XXXX --solution implemented --no-prune

#### 强制清理（谨慎）
$ monoco issue close FEAT-XXXX --solution implemented --force
```

###### 总结

| 操作 | 命令 | 说明 |
|------|------|------|
| 创建 Issue | `monoco issue create feature -t "标题"` | 先创建 Issue 再开发 |
| 启动开发 | `monoco issue start FEAT-XXXX --branch` | 创建 Feature 分支 |
| 同步文件 | `monoco issue sync-files` | 更新 files 字段 |
| 提交评审 | `monoco issue submit FEAT-XXXX` | 进入 Review 阶段 |
| 关闭 Issue | `monoco issue close FEAT-XXXX --solution implemented` | 唯一合并途径 |
| 保留分支 | `monoco issue close ... --no-prune` | 关闭但不删除分支 |

> ⚠️ **警告**: 任何绕过 `monoco issue close` 的手动合并操作都可能导致主线状态污染，违反工作流合规要求。

### Git Hooks



### Memo (Fleeting Notes)

Lightweight note-taking for ideas and quick thoughts. **Signal Queue Model** (FEAT-0165).

#### Signal Queue Semantics

- **Memo is a signal, not an asset** - Its value is in triggering action
- **File existence = signal pending** - Inbox has unprocessed memos
- **File cleared = signal consumed** - Memos are deleted after processing
- **Git is the archive** - History is in git, not app state

#### Commands

- **Add**: `monoco memo add "Content" [-c context]` - Create a signal
- **List**: `monoco memo list` - Show pending signals (consumed memos are in git history)
- **Delete**: `monoco memo delete <id>` - Manual delete (normally auto-consumed)
- **Open**: `monoco memo open` - Edit inbox directly

#### Workflow

1. Capture ideas as memos
2. When threshold (5) is reached, Architect is auto-triggered
3. Memos are consumed (deleted) and embedded in Architect's prompt
4. Architect creates Issues from memos
5. No need to "link" or "resolve" memos - they're gone after consumption

#### Guideline

- Use Memos for **fleeting ideas** - things that might become Issues
- Use Issues for **actionable work** - structured, tracked, with lifecycle
- Never manually link memos to Issues - if important, create an Issue

### Glossary

###### 术语表

####### Monoco 术语表

######## 核心架构隐喻: "Linux 发行版"

| 术语 | 定义 | 隐喻 |
| :--- | :--- | :--- |
| **Monoco** | 智能体操作系统发行版。管理策略、工作流和包系统。 | **发行版** (如 Ubuntu, Arch) |
| **Kimi CLI** | 核心运行时执行引擎。处理 LLM 交互、工具执行和进程管理。 | **内核** (Linux Kernel) |
| **Session** | 由 Monoco 管理的智能体内核初始化实例。具有状态和上下文。 | **初始化系统/守护进程** (systemd) |
| **Issue** | 具有状态（Open/Done）和严格生命周期的原子工作单元。 | **单元文件** (systemd unit) |
| **Skill** | 扩展智能体功能的工具、提示词和流程包。 | **软件包** (apt/pacman package) |
| **Context File** | 定义环境规则和行为偏好的配置文件（如 `GEMINI.md`, `AGENTS.md`）。 | **配置** (`/etc/config`) |
| **Agent Client** | 连接 Monoco 的用户界面（CLI, VSCode, Zed）。 | **桌面环境** (GNOME/KDE) |

######## 关键概念

######### Context File

像 `GEMINI.md` 这样的文件，为智能体提供"宪法"。它们定义了特定上下文（根目录、目录、项目）中智能体的角色、范围和行为策略。

######### Headless

Monoco 设计为无需原生 GUI 即可运行。它通过标准协议（LSP, ACP）暴露其能力，供各种客户端（IDE、终端）使用。

######### Universal Shell

CLI 是所有工作流的通用接口的概念。Monoco 作为 shell 的智能层。

### Spike (Research)

###### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Artifacts & Mailroom

Monoco Artifacts 系统提供了多模态产物的生命周期管理能力，包括：

1. **内容寻址存储 (CAS)**: 所有产物存储在全局池 `~/.monoco/artifacts` 中，基于内容的 SHA256 哈希值进行寻址和去重。
2. **自动化摄取 (Mailroom)**: 通过监听 `.monoco/dropzone/` 目录，自动触发文档（Office, PDF 等）到 WebP 的转换流程。
3. **环境追踪**: 自动探测系统中的 `LibreOffice`, `PyMuPDF` 等工具链。
4. **元数据管理**: 项目本地维护 `manifest.jsonl`，记录所有产物的类型、哈希及创建时间。

###### 常用操作建议

- **上传文档**: 建议将原始文档放入 `.monoco/dropzone/`，等待 Mailroom 自动完成转换并注册为 Artifact。
- **查看产物**: 检查 `.monoco/artifacts/manifest.jsonl` 获取当前可用的产物列表。
- **引用产物**: 在多模态分析时，可以使用产物的 ID 或本地软链接路径。

### Documentation I18n

###### 文档国际化

管理国际化。

- **扫描**: `monoco i18n scan` (检查缺失的翻译)
- **结构**:
  - 根文件: `FILE_ZH.md`
  - 子目录: `folder/zh/file.md`

<!-- MONOCO_GENERATED_END -->

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

### Spike (Research)

### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

### 文档国际化

管理国际化。

- **扫描**: `monoco i18n scan` (检查缺失的翻译)
- **结构**:
  - 根文件: `FILE_ZH.md`
  - 子目录: `folder/zh/file.md`

### Memo (Fleeting Notes)

Lightweight note-taking for ideas and quick thoughts. **Signal Queue Model** (FEAT-0165).

#### Signal Queue Semantics

- **Memo is a signal, not an asset** - Its value is in triggering action
- **File existence = signal pending** - Inbox has unprocessed memos
- **File cleared = signal consumed** - Memos are deleted after processing
- **Git is the archive** - History is in git, not app state

#### Commands

- **Add**: `monoco memo add "Content" [-c context]` - Create a signal
- **List**: `monoco memo list` - Show pending signals (consumed memos are in git history)
- **Delete**: `monoco memo delete <id>` - Manual delete (normally auto-consumed)
- **Open**: `monoco memo open` - Edit inbox directly

#### Workflow

1. Capture ideas as memos
2. When threshold (5) is reached, Architect is auto-triggered
3. Memos are consumed (deleted) and embedded in Architect's prompt
4. Architect creates Issues from memos
5. No need to "link" or "resolve" memos - they're gone after consumption

#### Guideline

- Use Memos for **fleeting ideas** - things that might become Issues
- Use Issues for **actionable work** - structured, tracked, with lifecycle
- Never manually link memos to Issues - if important, create an Issue

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

### Spike (Research)

### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

### 文档国际化

管理国际化。

- **扫描**: `monoco i18n scan` (检查缺失的翻译)
- **结构**:
  - 根文件: `FILE_ZH.md`
  - 子目录: `folder/zh/file.md`

### Memo (Fleeting Notes)

Lightweight note-taking for ideas and quick thoughts. **Signal Queue Model** (FEAT-0165).

#### Signal Queue Semantics

- **Memo is a signal, not an asset** - Its value is in triggering action
- **File existence = signal pending** - Inbox has unprocessed memos
- **File cleared = signal consumed** - Memos are deleted after processing
- **Git is the archive** - History is in git, not app state

#### Commands

- **Add**: `monoco memo add "Content" [-c context]` - Create a signal
- **List**: `monoco memo list` - Show pending signals (consumed memos are in git history)
- **Delete**: `monoco memo delete <id>` - Manual delete (normally auto-consumed)
- **Open**: `monoco memo open` - Edit inbox directly

#### Workflow

1. Capture ideas as memos
2. When threshold (5) is reached, Architect is auto-triggered
3. Memos are consumed (deleted) and embedded in Architect's prompt
4. Architect creates Issues from memos
5. No need to "link" or "resolve" memos - they're gone after consumption

#### Guideline

- Use Memos for **fleeting ideas** - things that might become Issues
- Use Issues for **actionable work** - structured, tracked, with lifecycle
- Never manually link memos to Issues - if important, create an Issue

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

### Spike (Research)

### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

### 文档国际化

管理国际化。

- **扫描**: `monoco i18n scan` (检查缺失的翻译)
- **结构**:
  - 根文件: `FILE_ZH.md`
  - 子目录: `folder/zh/file.md`

### Memo (Fleeting Notes)

Lightweight note-taking for ideas and quick thoughts. **Signal Queue Model** (FEAT-0165).

#### Signal Queue Semantics

- **Memo is a signal, not an asset** - Its value is in triggering action
- **File existence = signal pending** - Inbox has unprocessed memos
- **File cleared = signal consumed** - Memos are deleted after processing
- **Git is the archive** - History is in git, not app state

#### Commands

- **Add**: `monoco memo add "Content" [-c context]` - Create a signal
- **List**: `monoco memo list` - Show pending signals (consumed memos are in git history)
- **Delete**: `monoco memo delete <id>` - Manual delete (normally auto-consumed)
- **Open**: `monoco memo open` - Edit inbox directly

#### Workflow

1. Capture ideas as memos
2. When threshold (5) is reached, Architect is auto-triggered
3. Memos are consumed (deleted) and embedded in Architect's prompt
4. Architect creates Issues from memos
5. No need to "link" or "resolve" memos - they're gone after consumption

#### Guideline

- Use Memos for **fleeting ideas** - things that might become Issues
- Use Issues for **actionable work** - structured, tracked, with lifecycle
- Never manually link memos to Issues - if important, create an Issue

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

### Spike (Research)

### Spike (研究)

管理外部参考仓库。

- **添加仓库**: `monoco spike add <url>` (在 `.reference/<name>` 中可读)
- **同步**: `monoco spike sync` (运行以下载内容)
- **约束**: 永远不要编辑 `.reference/` 中的文件。将它们视为只读的外部知识。

### Documentation I18n

### 文档国际化

管理国际化。

- **扫描**: `monoco i18n scan` (检查缺失的翻译)
- **结构**:
  - 根文件: `FILE_ZH.md`
  - 子目录: `folder/zh/file.md`

### Memo (Fleeting Notes)

Lightweight note-taking for ideas and quick thoughts. **Signal Queue Model** (FEAT-0165).

#### Signal Queue Semantics

- **Memo is a signal, not an asset** - Its value is in triggering action
- **File existence = signal pending** - Inbox has unprocessed memos
- **File cleared = signal consumed** - Memos are deleted after processing
- **Git is the archive** - History is in git, not app state

#### Commands

- **Add**: `monoco memo add "Content" [-c context]` - Create a signal
- **List**: `monoco memo list` - Show pending signals (consumed memos are in git history)
- **Delete**: `monoco memo delete <id>` - Manual delete (normally auto-consumed)
- **Open**: `monoco memo open` - Edit inbox directly

#### Workflow

1. Capture ideas as memos
2. When threshold (5) is reached, Architect is auto-triggered
3. Memos are consumed (deleted) and embedded in Architect's prompt
4. Architect creates Issues from memos
5. No need to "link" or "resolve" memos - they're gone after consumption

#### Guideline

- Use Memos for **fleeting ideas** - things that might become Issues
- Use Issues for **actionable work** - structured, tracked, with lifecycle
- Never manually link memos to Issues - if important, create an Issue
